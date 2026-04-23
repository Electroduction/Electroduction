"""
Tests for mcp_server/mcp_skill_server.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_mcp_server.py -v
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.mcp_skill_server import DatabaseConnector, CPOResolver, VerifierAgent


# ─── DatabaseConnector Tests ─────────────────────────────────────────────────

class TestDatabaseConnector:

    @pytest.fixture
    def tmp_db(self, tmp_path):
        """Create a temporary domain database with test records."""
        domain_dir = tmp_path / "test_domain"
        domain_dir.mkdir()

        records = [
            {"title": "Malware Detection", "category": "threat", "source_file": "file1.json"},
            {"title": "Phishing Patterns", "category": "social engineering", "source_file": "file2.json"},
            {"title": "Firewall Rules", "category": "defense", "source_file": "file3.json"},
        ]
        for i, rec in enumerate(records):
            (domain_dir / f"record_{i}.json").write_text(json.dumps(rec))

        # Also test list format
        list_file = domain_dir / "list_records.json"
        list_file.write_text(json.dumps([
            {"title": "NSL-KDD entry", "attack_type": "dos"},
            {"title": "Zero-day exploit", "cve": "CVE-2024-9999"},
        ]))

        return tmp_path

    def test_load_domain_returns_list(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        records = connector.load_domain("test_domain")
        assert isinstance(records, list)

    def test_load_domain_finds_all_records(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        records = connector.load_domain("test_domain")
        # 3 dict files + 2 from list file = 5
        assert len(records) == 5

    def test_load_domain_caches_results(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        first = connector.load_domain("test_domain")
        second = connector.load_domain("test_domain")
        assert first is second  # same object (from cache)

    def test_load_missing_domain_returns_empty(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        records = connector.load_domain("nonexistent_domain")
        assert records == []

    def test_query_returns_relevant_results(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        results = connector.query("test_domain", "malware detection", top_k=3)
        assert len(results) >= 1
        result_str = json.dumps(results).lower()
        assert "malware" in result_str or "threat" in result_str

    def test_query_respects_top_k(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        results = connector.query("test_domain", "the a of", top_k=2)
        assert len(results) <= 2

    def test_query_empty_on_no_match(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        results = connector.query("test_domain", "zzzznonexistentterm", top_k=3)
        assert results == []

    def test_load_domain_skips_invalid_json(self, tmp_path):
        domain_dir = tmp_path / "broken_domain"
        domain_dir.mkdir()
        (domain_dir / "good.json").write_text('{"key": "value"}')
        (domain_dir / "bad.json").write_text("NOT VALID JSON {{{")
        connector = DatabaseConnector(tmp_path)
        records = connector.load_domain("broken_domain")
        assert len(records) == 1  # only the good file

    def test_get_stats_returns_all_domains(self, tmp_db):
        connector = DatabaseConnector(tmp_db)
        # Patch DOMAINS for this test
        import mcp_server.mcp_skill_server as srv
        original = srv.DOMAINS
        srv.DOMAINS = ["test_domain"]
        stats = connector.get_stats()
        srv.DOMAINS = original
        assert "test_domain" in stats
        assert "records" in stats["test_domain"]


# ─── CPOResolver Tests ───────────────────────────────────────────────────────

class TestCPOResolver:

    def setup_method(self):
        self.cpo = CPOResolver()

    def test_resolve_with_db_results_uses_expert_source(self):
        result = self.cpo.resolve("PE ratio AAPL", [{"pe": 28.5}], generic_answer="around 28")
        assert result["source"] == "expert_database"

    def test_resolve_without_db_results_uses_generic(self):
        result = self.cpo.resolve("obscure query", [], generic_answer="I don't know")
        assert result["source"] == "generic_llm"

    def test_resolve_without_db_includes_warning(self):
        result = self.cpo.resolve("q", [], generic_answer="generic")
        assert "warning" in result

    def test_resolve_confidence_scales_with_results(self):
        r1 = self.cpo.resolve("q", [{"x": 1}])
        r2 = self.cpo.resolve("q", [{"x": 1}, {"y": 2}, {"z": 3}])
        assert r2["confidence"] > r1["confidence"]

    def test_resolve_confidence_capped(self):
        many = [{"x": i} for i in range(50)]
        result = self.cpo.resolve("q", many)
        assert result["confidence"] <= 0.99

    def test_resolve_logs_conflict(self):
        self.cpo.resolve("q", [{"db": "expert answer"}], generic_answer="different generic answer")
        assert len(self.cpo.conflicts_log) == 1

    def test_resolve_no_conflict_when_no_generic(self):
        self.cpo.resolve("q", [{"db": "expert answer"}], generic_answer="")
        assert len(self.cpo.conflicts_log) == 0

    def test_resolve_cpo_applied_flag(self):
        result = self.cpo.resolve("q", [{"x": 1}])
        assert result.get("cpo_applied") is True

    def test_resolve_results_count(self):
        results = [{"x": i} for i in range(4)]
        r = self.cpo.resolve("q", results)
        assert r["results_count"] == 4

    def test_resolve_empty_generic_still_warns(self):
        result = self.cpo.resolve("q", [], generic_answer="")
        assert result["source"] == "generic_llm"


# ─── VerifierAgent Tests ─────────────────────────────────────────────────────

class TestVerifierAgent:

    def setup_method(self):
        self.verifier = VerifierAgent()

    def test_clean_output_passes(self):
        result = self.verifier.verify("The PE ratio for AAPL is 28.5", "finance")
        assert result["passed"] is True
        assert result["issues"] == []

    def test_rm_rf_blocked(self):
        result = self.verifier.verify("run rm -rf /tmp to clean up", "cybersecurity")
        assert result["passed"] is False
        assert any("rm -rf" in issue for issue in result["issues"])

    def test_drop_table_blocked(self):
        result = self.verifier.verify("execute DROP TABLE users", "finance")
        assert result["passed"] is False

    def test_format_c_blocked(self):
        result = self.verifier.verify("format c: to reset the drive", "game_dev")
        assert result["passed"] is False

    def test_del_command_blocked(self):
        result = self.verifier.verify("del /f /s /q C:\\Windows", "cybersecurity")
        assert result["passed"] is False

    def test_sudo_outside_sandbox_warns_cybersecurity(self):
        result = self.verifier.verify("run sudo apt-get update to install packages", "cybersecurity")
        assert len(result["issues"]) > 0
        assert any("sudo" in i for i in result["issues"])

    def test_sudo_with_sandbox_context_passes_cybersecurity(self):
        result = self.verifier.verify(
            "run sudo command inside sandbox environment for testing", "cybersecurity"
        )
        # Should NOT trigger sudo warning since "sandbox" is mentioned
        sudo_issues = [i for i in result["issues"] if "sudo" in i.lower()]
        assert len(sudo_issues) == 0

    def test_guaranteed_return_warns_finance(self):
        result = self.verifier.verify("This investment gives guaranteed 100% return", "finance")
        assert len(result["issues"]) > 0
        assert any("financial" in i.lower() or "claim" in i.lower() for i in result["issues"])

    def test_guaranteed_not_flagged_in_other_domains(self):
        result = self.verifier.verify("guaranteed smooth animation", "game_dev")
        # "guaranteed" check is only for finance domain
        assert result["passed"] is True

    def test_safe_to_show_even_with_warnings(self):
        result = self.verifier.verify("sudo install inside sandbox for testing", "cybersecurity")
        # WARNING (not BLOCKED) — safe_to_show should still be True
        blocked = [i for i in result["issues"] if i.startswith("BLOCKED")]
        assert result["safe_to_show"] is (len(blocked) == 0)

    def test_safe_to_show_false_on_blocked(self):
        result = self.verifier.verify("rm -rf / dangerous", "cybersecurity")
        assert result["safe_to_show"] is False

    def test_case_insensitive_blocking(self):
        result = self.verifier.verify("RM -RF /important/files", "cybersecurity")
        assert result["passed"] is False

    def test_empty_output_passes(self):
        result = self.verifier.verify("", "finance")
        assert result["passed"] is True


# ─── Integration Tests ───────────────────────────────────────────────────────

class TestIntegration:
    """End-to-end: connector → cpo resolver → verifier."""

    @pytest.fixture
    def setup_db(self, tmp_path):
        domain_dir = tmp_path / "finance"
        domain_dir.mkdir()
        metrics = {"ticker": "AAPL", "pe_ratio": 28.5, "roe": 0.87, "source_file": "metrics.json"}
        (domain_dir / "aapl_metrics.json").write_text(json.dumps(metrics))
        return tmp_path

    def test_full_pipeline_finance(self, setup_db):
        connector = DatabaseConnector(setup_db)
        cpo = CPOResolver()
        verifier = VerifierAgent()

        results = connector.query("finance", "AAPL PE ratio", top_k=3)
        resolved = cpo.resolve("What is the PE ratio for AAPL?", results, generic_answer="around 28")
        verified = verifier.verify(resolved["answer"], "finance")

        assert resolved["source"] == "expert_database"
        assert resolved["confidence"] > 0.5
        assert verified["passed"] is True

    def test_full_pipeline_no_data(self, setup_db):
        connector = DatabaseConnector(setup_db)
        cpo = CPOResolver()
        verifier = VerifierAgent()

        results = connector.query("finance", "2040 quantum stock prediction", top_k=3)
        resolved = cpo.resolve("future prediction", results, generic_answer="unknown")

        assert resolved["source"] == "generic_llm"
        assert "warning" in resolved
