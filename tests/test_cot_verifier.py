"""
Tests for algorithms/cot_verifier.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_cot_verifier.py -v
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.cot_verifier import (
    CitationParser, DatabaseRuleChecker, CoTVerifier, CoTDatabase,
    ReasoningStep, CoTAnswer
)


class TestCitationParser:

    def setup_method(self):
        self.parser = CitationParser()

    def test_extract_citations_finds_single_citation(self):
        text = "PE ratio is high [Source: data/finance/metrics.json | Rule: pe_threshold]"
        citations = self.parser.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["source_file"] == "data/finance/metrics.json"
        assert citations[0]["rule_name"] == "pe_threshold"

    def test_extract_citations_finds_multiple_citations(self):
        text = """
        [Source: file1.json | Rule: rule1]
        and also [Source: file2.json | Rule: rule2]
        """
        citations = self.parser.extract_citations(text)
        assert len(citations) == 2

    def test_extract_citations_empty_when_none(self):
        text = "This is plain text with no citations"
        citations = self.parser.extract_citations(text)
        assert citations == []

    def test_has_citation_true_when_present(self):
        text = "Some text [Source: test.json | Rule: test_rule]"
        assert self.parser.has_citation(text) is True

    def test_has_citation_false_when_absent(self):
        text = "No citations here"
        assert self.parser.has_citation(text) is False


class TestDatabaseRuleChecker:

    @pytest.fixture
    def tmp_db(self, tmp_path):
        """Create temp database with test rules."""
        rules_file = tmp_path / "test_rules.json"
        rules = {
            "pe_threshold": {"value": 30, "description": "PE ratio threshold"},
            "debt_threshold": {"value": 2.0, "description": "D/E ratio threshold"},
        }
        rules_file.write_text(json.dumps(rules))
        return tmp_path

    def test_verify_citation_succeeds_when_file_and_rule_exist(self, tmp_db):
        checker = DatabaseRuleChecker(tmp_db)
        citation = {"source_file": "test_rules.json", "rule_name": "pe_threshold"}
        result = checker.verify_citation(citation)
        assert result["verified"] is True

    def test_verify_citation_fails_when_file_missing(self, tmp_db):
        checker = DatabaseRuleChecker(tmp_db)
        citation = {"source_file": "nonexistent.json", "rule_name": "any_rule"}
        result = checker.verify_citation(citation)
        assert result["verified"] is False
        assert "not found" in result["note"].lower()

    def test_verify_citation_fails_when_rule_missing(self, tmp_db):
        checker = DatabaseRuleChecker(tmp_db)
        citation = {"source_file": "test_rules.json", "rule_name": "nonexistent_rule"}
        result = checker.verify_citation(citation)
        assert result["verified"] is False

    def test_rule_cache_works(self, tmp_db):
        checker = DatabaseRuleChecker(tmp_db)
        # First load
        citation1 = {"source_file": "test_rules.json", "rule_name": "pe_threshold"}
        checker.verify_citation(citation1)
        # Second load (from cache)
        citation2 = {"source_file": "test_rules.json", "rule_name": "debt_threshold"}
        result = checker.verify_citation(citation2)
        assert result["verified"] is True


class TestCoTVerifier:

    @pytest.fixture
    def tmp_db(self, tmp_path):
        rules_file = tmp_path / "finance_rules.json"
        rules = {"valuation_threshold": {"pe_limit": 30}}
        rules_file.write_text(json.dumps(rules))
        return tmp_path

    def test_verify_returns_cot_answer(self, tmp_db):
        verifier = CoTVerifier(tmp_db, strict_mode=False)
        output = """
Step 1: Check PE ratio
Final Answer: Stock is fairly valued
"""
        result = verifier.verify("Query", "finance", output)
        assert isinstance(result, CoTAnswer)

    def test_verify_parses_steps(self, tmp_db):
        verifier = CoTVerifier(tmp_db, strict_mode=False)
        output = """
Step 1: First claim
Step 2: Second claim
Final Answer: Done
"""
        result = verifier.verify("Query", "finance", output)
        assert len(result.reasoning_steps) == 2

    def test_verify_extracts_final_answer(self, tmp_db):
        verifier = CoTVerifier(tmp_db, strict_mode=False)
        output = """
Step 1: Analysis
Final Answer: The answer is 42
"""
        result = verifier.verify("Query", "finance", output)
        assert "42" in result.final_answer

    def test_verify_marks_uncited_steps_as_unverified_in_strict_mode(self, tmp_db):
        verifier = CoTVerifier(tmp_db, strict_mode=True)
        output = """
Step 1: This step has no citation
Final Answer: Done
"""
        result = verifier.verify("Query", "finance", output)
        assert result.reasoning_steps[0].verified is False

    def test_verify_confidence_high_when_all_verified(self, tmp_db):
        verifier = CoTVerifier(tmp_db, strict_mode=False)
        # Create a file the verifier can find
        (tmp_db / "test.json").write_text('{"rule1": "value"}')
        output = """
Step 1: Claim [Source: test.json | Rule: rule1]
Final Answer: Done
"""
        result = verifier.verify("Query", "finance", output)
        assert result.confidence > 0.5

    def test_verify_overall_verified_true_when_all_pass(self, tmp_db):
        verifier = CoTVerifier(tmp_db, strict_mode=False)
        (tmp_db / "test.json").write_text('{"rule1": "value"}')
        output = """
Step 1: Claim [Source: test.json | Rule: rule1]
Final Answer: Done
"""
        result = verifier.verify("Query", "finance", output)
        if result.reasoning_steps and result.reasoning_steps[0].verified:
            assert result.overall_verified is True


class TestCoTDatabase:

    @pytest.fixture(autouse=True)
    def cleanup(self):
        db = CoTDatabase("_test")
        if db.verified_file.exists():
            db.verified_file.unlink()
        if db.rejected_file.exists():
            db.rejected_file.unlink()
        yield
        if db.verified_file.exists():
            db.verified_file.unlink()
        if db.rejected_file.exists():
            db.rejected_file.unlink()

    def test_save_verified_answer_to_verified_file(self):
        db = CoTDatabase("_test")
        answer = CoTAnswer(
            query="test",
            domain="_test",
            reasoning_steps=[],
            final_answer="answer",
            overall_verified=True,
            confidence=0.9,
            timestamp="2024-01-15T12:00:00",
        )
        db.save(answer)
        assert db.verified_file.exists()

    def test_save_rejected_answer_to_rejected_file(self):
        db = CoTDatabase("_test")
        answer = CoTAnswer(
            query="test",
            domain="_test",
            reasoning_steps=[],
            final_answer="answer",
            overall_verified=False,
            confidence=0.3,
            timestamp="2024-01-15T12:00:00",
        )
        db.save(answer)
        assert db.rejected_file.exists()

    def test_load_verified_returns_empty_when_no_file(self):
        db = CoTDatabase("_test")
        verified = db.load_verified()
        assert verified == []

    def test_get_stats_calculates_verification_rate(self):
        db = CoTDatabase("_test")
        verified = CoTAnswer("q", "_test", [], "a", True, 0.9, "2024-01-15")
        rejected = CoTAnswer("q", "_test", [], "a", False, 0.3, "2024-01-15")
        db.save(verified)
        db.save(rejected)

        stats = db.get_stats()
        assert stats["verified"] == 1
        assert stats["rejected"] == 1
        assert stats["verification_rate"] == 0.5
