"""
Tests for algorithms/weak_to_strong.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_weak_to_strong.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.weak_to_strong import (
    WeakModel, WeakLabelValidator, WeakToStrongPipeline,
    WeakLabel, StrongTrainingExample, SupervisionStats, SUPERVISION_DIR
)


@pytest.fixture(autouse=True)
def cleanup_supervision():
    """Clean up supervision output files."""
    yield
    if SUPERVISION_DIR.exists():
        for f in SUPERVISION_DIR.glob("*.jsonl"):
            f.unlink()


class TestWeakModel:

    @pytest.fixture
    def tmp_db(self, tmp_path):
        return tmp_path

    def test_label_returns_weak_label(self, tmp_db):
        model = WeakModel("finance", tmp_db)
        label = model.label("What is the PE ratio for AAPL?")
        assert isinstance(label, WeakLabel)

    def test_label_includes_prediction(self, tmp_db):
        model = WeakModel("finance", tmp_db)
        label = model.label("PE ratio is 35")
        assert label.weak_prediction is not None

    def test_label_includes_confidence(self, tmp_db):
        model = WeakModel("finance", tmp_db)
        label = model.label("PE ratio is 35")
        assert 0.0 <= label.weak_confidence <= 1.0

    def test_label_includes_reasoning(self, tmp_db):
        model = WeakModel("finance", tmp_db)
        label = model.label("PE ratio is 35")
        assert len(label.reasoning) > 0

    def test_finance_pe_high_predicts_overvalued(self, tmp_db):
        model = WeakModel("finance", tmp_db)
        label = model.label("PE ratio is 50")
        assert label.weak_prediction == "overvalued"

    def test_finance_pe_low_predicts_fairly_valued(self, tmp_db):
        model = WeakModel("finance", tmp_db)
        label = model.label("PE ratio is 15")
        assert label.weak_prediction == "fairly_valued"

    def test_cybersecurity_threat_keywords_detected(self, tmp_db):
        model = WeakModel("cybersecurity", tmp_db)
        label = model.label("malware exploit vulnerability detected")
        assert label.weak_prediction == "threat"

    def test_cybersecurity_safe_keywords_detected(self, tmp_db):
        model = WeakModel("cybersecurity", tmp_db)
        label = model.label("system updated with security patch")
        assert label.weak_prediction == "safe"

    def test_confidence_higher_for_clear_signals(self, tmp_db):
        model = WeakModel("cybersecurity", tmp_db)
        clear = model.label("exploit malware vulnerability ransomware")
        unclear = model.label("system status check")
        assert clear.weak_confidence > unclear.weak_confidence


class TestWeakLabelValidator:

    @pytest.fixture
    def tmp_db(self, tmp_path):
        return tmp_path

    def test_validate_returns_dict(self, tmp_db):
        validator = WeakLabelValidator(tmp_db)
        label = WeakLabel(
            data_id="test",
            domain="finance",
            input_text="test",
            weak_prediction="overvalued",
            weak_confidence=0.8,
            reasoning="PE > threshold",
            created_at="2024-01-15",
        )
        result = validator.validate(label)
        assert "verified" in result
        assert "quality_score" in result
        assert "note" in result

    def test_validate_rejects_low_confidence(self, tmp_db):
        validator = WeakLabelValidator(tmp_db)
        label = WeakLabel(
            "test", "finance", "test", "unknown", 0.3, "unclear", "2024-01-15"
        )
        result = validator.validate(label)
        assert result["verified"] is False

    def test_validate_accepts_high_confidence_finance_with_reasoning(self, tmp_db):
        validator = WeakLabelValidator(tmp_db)
        label = WeakLabel(
            "test", "finance", "test", "overvalued", 0.85,
            "PE ratio exceeds threshold", "2024-01-15"
        )
        result = validator.validate(label)
        assert result["verified"] is True

    def test_validate_quality_score_ranges_0_to_1(self, tmp_db):
        validator = WeakLabelValidator(tmp_db)
        label = WeakLabel("test", "finance", "test", "x", 0.8, "y", "2024-01-15")
        result = validator.validate(label)
        assert 0.0 <= result["quality_score"] <= 1.0

    def test_validate_cybersecurity_with_keyword_reasoning(self, tmp_db):
        validator = WeakLabelValidator(tmp_db)
        label = WeakLabel(
            "test", "cybersecurity", "test", "threat", 0.8,
            "Threat keywords detected: 3", "2024-01-15"
        )
        result = validator.validate(label)
        assert result["verified"] is True


class TestWeakToStrongPipeline:

    @pytest.fixture
    def tmp_db(self, tmp_path):
        return tmp_path

    def test_process_batch_returns_examples(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        inputs = ["PE ratio is 35", "What is ROE?"]
        examples = pipeline.process_batch(inputs)
        assert len(examples) == 2
        assert all(isinstance(ex, StrongTrainingExample) for ex in examples)

    def test_process_batch_verifies_high_quality(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        inputs = ["PE ratio is 50"]  # Should trigger overvalued with high confidence
        examples = pipeline.process_batch(inputs)
        # At least one should be verified if confidence is high
        assert any(ex.verified for ex in examples)

    def test_export_training_set_creates_file(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        pipeline.process_batch(["PE ratio is 50"])
        output = pipeline.export_training_set(min_quality=0.0)
        assert output.exists()
        output.unlink()

    def test_export_training_set_filters_by_quality(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        # Mix of high and low confidence inputs
        pipeline.process_batch([
            "PE ratio is 50",  # High confidence
            "unknown query xyz",  # Low confidence
        ])
        high_quality_file = pipeline.export_training_set(min_quality=0.7)

        # Read and count
        with open(high_quality_file) as f:
            lines = f.readlines()
        # Should have fewer than total examples (low quality filtered out)
        assert len(lines) < 2
        high_quality_file.unlink()

    def test_get_stats_returns_supervision_stats(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        pipeline.process_batch(["test1", "test2"])
        stats = pipeline.get_stats()
        assert isinstance(stats, SupervisionStats)
        assert stats.domain == "finance"
        assert stats.total_examples == 2

    def test_get_stats_calculates_verification_rate(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        pipeline.process_batch(["PE ratio is 50", "unknown xyz"])
        stats = pipeline.get_stats()
        assert 0.0 <= stats.verification_rate <= 1.0

    def test_training_examples_accumulate(self, tmp_db):
        pipeline = WeakToStrongPipeline("finance", tmp_db)
        pipeline.process_batch(["test1"])
        pipeline.process_batch(["test2", "test3"])
        assert len(pipeline.training_examples) == 3
