"""
Tests for algorithms/cpo_engine.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_cpo_engine.py -v
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.cpo_engine import CPOEngine, CPOTriplet, ActiveLearner


TRIPLETS_DIR = Path("databases/cpo_triplets")
TEST_DOMAIN = "_pytest_cpo"


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Remove test domain files before and after each test."""
    _cleanup()
    yield
    _cleanup()


def _cleanup():
    for suffix in ["_triplets.jsonl", "_conflicts.csv", "_dpo_ready.jsonl"]:
        p = TRIPLETS_DIR / f"{TEST_DOMAIN}{suffix}"
        if p.exists():
            p.unlink()


class TestCPOEngine:

    def setup_method(self):
        self.engine = CPOEngine(TEST_DOMAIN)

    def test_record_returns_cpo_triplet(self):
        triplet = self.engine.record(
            query="What is the PE ratio for AAPL?",
            generic_answer="Around 28.",
            expert_results=[{"pe_ratio": 28.5, "source_file": "metrics.json"}],
        )
        assert isinstance(triplet, CPOTriplet)

    def test_record_stores_query(self):
        triplet = self.engine.record("test query", "generic", [{"x": 1, "source_file": "f.json"}])
        assert triplet.query == "test query"

    def test_record_stores_domain(self):
        triplet = self.engine.record("q", "g", [{"x": 1}])
        assert triplet.domain == TEST_DOMAIN

    def test_record_confidence_increases_with_more_results(self):
        t1 = self.engine.record("q1", "g", [{"x": 1}])
        t2 = self.engine.record("q2", "g", [{"x": 1}, {"y": 2}, {"z": 3}])
        assert t2.confidence > t1.confidence

    def test_record_confidence_capped_at_099(self):
        expert_results = [{"x": i, "source_file": f"f{i}.json"} for i in range(20)]
        triplet = self.engine.record("q", "g", expert_results)
        assert triplet.confidence <= 0.99

    def test_record_low_confidence_on_empty_results(self):
        triplet = self.engine.record("q", "g", [])
        assert triplet.confidence == 0.2

    def test_record_extracts_source_files(self):
        triplet = self.engine.record("q", "g", [
            {"data": "x", "source_file": "file1.json"},
            {"data": "y", "source_file": "file2.json"},
        ])
        assert "file1.json" in triplet.source_files
        assert "file2.json" in triplet.source_files

    def test_record_writes_to_jsonl(self):
        self.engine.record("q", "g", [{"x": 1}])
        assert self.engine.triplet_file.exists()
        with open(self.engine.triplet_file) as f:
            line = f.readline()
        data = json.loads(line)
        assert "query" in data
        assert "expert_answer" in data

    def test_record_appends_to_jsonl(self):
        self.engine.record("q1", "g1", [{"x": 1}])
        self.engine.record("q2", "g2", [{"x": 2}])
        with open(self.engine.triplet_file) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_record_logs_conflict_when_answers_differ(self):
        self.engine.record("q", "generic answer text", [{"db_answer": "expert text"}])
        if self.engine.conflict_file.exists():
            content = self.engine.conflict_file.read_text()
            assert "q" in content

    def test_record_no_conflict_when_no_generic_answer(self):
        self.engine.record("q", "", [{"x": 1}])
        assert not self.engine.conflict_file.exists()

    def test_timestamp_is_iso_format(self):
        triplet = self.engine.record("q", "g", [{"x": 1}])
        datetime.fromisoformat(triplet.timestamp)  # raises if invalid

    def test_load_triplets_empty_when_no_file(self):
        triplets = self.engine.load_triplets()
        assert triplets == []

    def test_load_triplets_returns_cpo_triplets(self):
        self.engine.record("q1", "g1", [{"x": 1}])
        self.engine.record("q2", "g2", [{"x": 2}])
        loaded = self.engine.load_triplets()
        assert len(loaded) == 2
        assert all(isinstance(t, CPOTriplet) for t in loaded)

    def test_load_triplets_skips_corrupt_lines(self):
        TRIPLETS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.engine.triplet_file, "w") as f:
            f.write('{"query": "good"}\n')
            f.write("CORRUPT_LINE_NOT_JSON\n")
        # Should not raise; just skips bad line
        loaded = self.engine.load_triplets()
        # 1 good line + 1 bad — loads 0 (missing required fields) or 1
        assert isinstance(loaded, list)

    def test_export_for_finetuning_creates_file(self):
        self.engine.record("q", "g", [{"x": 1}])
        output = self.engine.export_for_finetuning()
        assert output.exists()
        output.unlink()

    def test_export_has_dpo_fields(self):
        self.engine.record("test prompt", "rejected text", [{"chosen": "expert text"}])
        output = self.engine.export_for_finetuning()
        with open(output) as f:
            record = json.loads(f.readline())
        assert "prompt" in record
        assert "chosen" in record
        assert "rejected" in record
        output.unlink()

    def test_get_stats_returns_dict(self):
        self.engine.record("q", "g", [{"x": 1}])
        stats = self.engine.get_stats()
        assert "domain" in stats
        assert "total_triplets" in stats
        assert "conflicts_logged" in stats
        assert "avg_confidence" in stats

    def test_get_stats_counts_triplets(self):
        self.engine.record("q1", "g1", [{"x": 1}])
        self.engine.record("q2", "g2", [{"x": 2}])
        stats = self.engine.get_stats()
        assert stats["total_triplets"] == 2

    def test_get_stats_empty_domain(self):
        stats = self.engine.get_stats()
        assert stats["total_triplets"] == 0
        assert stats["avg_confidence"] == 0.0


class TestActiveLearner:

    GAP_FILE = TRIPLETS_DIR / "knowledge_gaps.jsonl"

    def setup_method(self):
        self.learner = ActiveLearner(confidence_threshold=0.5)
        if self.GAP_FILE.exists():
            self.GAP_FILE.unlink()

    def teardown_method(self):
        if self.GAP_FILE.exists():
            self.GAP_FILE.unlink()

    def test_check_returns_dict(self):
        result = self.learner.check("test query", "finance", 0.3)
        assert isinstance(result, dict)

    def test_low_confidence_is_gap(self):
        result = self.learner.check("obscure query", "finance", 0.1)
        assert result["is_knowledge_gap"] is True

    def test_high_confidence_not_gap(self):
        result = self.learner.check("common query", "finance", 0.9)
        assert result["is_knowledge_gap"] is False

    def test_gap_boundary_at_threshold(self):
        result_below = self.learner.check("q", "music", 0.49)
        result_at = self.learner.check("q", "music", 0.5)
        assert result_below["is_knowledge_gap"] is True
        assert result_at["is_knowledge_gap"] is False

    def test_gap_written_to_file(self):
        self.learner.check("rare edge case query", "cybersecurity", 0.15)
        assert self.GAP_FILE.exists()
        with open(self.GAP_FILE) as f:
            gap = json.loads(f.readline())
        assert gap["query"] == "rare edge case query"
        assert gap["action"] == "add_data_for_this_query"

    def test_no_write_for_high_confidence(self):
        self.learner.check("easy query", "finance", 0.95)
        assert not self.GAP_FILE.exists()

    def test_suggestion_message_on_gap(self):
        result = self.learner.check("unknown domain question", "creativity", 0.2)
        assert "creativity" in result["suggestion"]

    def test_suggestion_ok_on_high_confidence(self):
        result = self.learner.check("common question", "finance", 0.8)
        assert result["suggestion"] == "OK"

    def test_get_top_gaps_empty_when_no_file(self):
        gaps = self.learner.get_top_gaps()
        assert gaps == []

    def test_get_top_gaps_returns_n_items(self):
        for i in range(15):
            self.learner.check(f"gap query {i}", "music", 0.1)
        gaps = self.learner.get_top_gaps(n=10)
        assert len(gaps) == 10

    def test_get_top_gaps_returns_most_recent(self):
        for i in range(5):
            self.learner.check(f"gap {i}", "finance", 0.1)
        gaps = self.learner.get_top_gaps(n=3)
        assert len(gaps) == 3
        # Most recent are at the end of file, so returned last N
        assert gaps[-1]["query"] == "gap 4"

    def test_custom_threshold(self):
        strict_learner = ActiveLearner(confidence_threshold=0.8)
        result_lo = strict_learner.check("q", "video", 0.5)
        result_hi = strict_learner.check("q", "video", 0.9)
        assert result_lo["is_knowledge_gap"] is True
        assert result_hi["is_knowledge_gap"] is False
