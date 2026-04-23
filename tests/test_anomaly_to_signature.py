"""
Tests for algorithms/anomaly_to_signature.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_anomaly_to_signature.py -v
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.anomaly_to_signature import (
    AnomalyParser, SignatureGenerator, SignatureDatabase,
    Anomaly, Signature, SIGNATURES_DIR
)


@pytest.fixture(autouse=True)
def cleanup_signatures():
    """Clean up generated signatures before and after tests."""
    _cleanup()
    yield
    _cleanup()


def _cleanup():
    if SIGNATURES_DIR.exists():
        for f in SIGNATURES_DIR.glob("*"):
            if f.is_file():
                f.unlink()


class TestAnomalyParser:

    def setup_method(self):
        self.parser = AnomalyParser()

    def test_parse_extracts_syscalls(self):
        log = "syscall=execve proc.name=bash"
        features = self.parser.parse(log, "falco")
        assert "execve" in features["syscalls"]

    def test_parse_extracts_multiple_syscalls(self):
        log = "syscall=open syscall=read syscall=close"
        features = self.parser.parse(log, "falco")
        assert len(features["syscalls"]) == 3

    def test_parse_extracts_ips(self):
        log = "connection from 192.168.1.100 to 10.0.0.5"
        features = self.parser.parse(log, "network")
        assert "192.168.1.100" in features["ips"]
        assert "10.0.0.5" in features["ips"]

    def test_parse_extracts_ports(self):
        log = "connection on port=443 from port=12345"
        features = self.parser.parse(log, "network")
        assert "443" in features["ports"]
        assert "12345" in features["ports"]

    def test_parse_extracts_processes(self):
        log = "proc.name=nginx proc.name=apache2"
        features = self.parser.parse(log, "falco")
        assert "nginx" in features["processes"]
        assert "apache2" in features["processes"]

    def test_parse_extracts_falco_rule(self):
        log = "rule=Terminal_shell_in_container syscall=execve"
        features = self.parser.parse(log, "falco")
        assert features["rule"] == "Terminal_shell_in_container"

    def test_parse_no_falco_rule_returns_none(self):
        log = "syscall=open proc.name=test"
        features = self.parser.parse(log, "falco")
        assert features["rule"] is None


class TestSignatureGenerator:

    def setup_method(self):
        self.generator = SignatureGenerator()

    def create_anomaly(self, syscalls=None, processes=None, source="falco"):
        return Anomaly(
            timestamp="2024-01-15T12:00:00",
            source=source,
            raw_log="test log",
            features={
                "syscalls": syscalls or [],
                "processes": processes or [],
                "ports": [],
                "ips": [],
            },
            severity=0.8,
        )

    def test_generate_requires_min_support(self):
        anomalies = [self.create_anomaly(syscalls=["execve"])]
        sigs = self.generator.generate_from_anomalies(anomalies, min_support=3)
        assert len(sigs) == 0

    def test_generate_creates_signature_above_min_support(self):
        anomalies = [
            self.create_anomaly(syscalls=["execve"], processes=["bash"]),
            self.create_anomaly(syscalls=["execve"], processes=["bash"]),
            self.create_anomaly(syscalls=["execve"], processes=["bash"]),
        ]
        sigs = self.generator.generate_from_anomalies(anomalies, min_support=3)
        assert len(sigs) >= 1

    def test_generate_falco_rule_has_correct_type(self):
        anomalies = [
            self.create_anomaly(syscalls=["execve"], source="falco"),
            self.create_anomaly(syscalls=["execve"], source="falco"),
            self.create_anomaly(syscalls=["execve"], source="falco"),
        ]
        sigs = self.generator.generate_from_anomalies(anomalies, min_support=2)
        falco_sigs = [s for s in sigs if s.rule_type == "falco"]
        assert len(falco_sigs) >= 1

    def test_signature_confidence_increases_with_more_anomalies(self):
        small_batch = [self.create_anomaly(syscalls=["open"]) for _ in range(3)]
        large_batch = [self.create_anomaly(syscalls=["open"]) for _ in range(10)]

        small_sigs = self.generator.generate_from_anomalies(small_batch, min_support=2)
        large_sigs = self.generator.generate_from_anomalies(large_batch, min_support=2)

        if small_sigs and large_sigs:
            assert large_sigs[0].confidence >= small_sigs[0].confidence

    def test_signature_includes_source_anomalies(self):
        anomalies = [
            self.create_anomaly(syscalls=["execve"]),
            self.create_anomaly(syscalls=["execve"]),
            self.create_anomaly(syscalls=["execve"]),
        ]
        sigs = self.generator.generate_from_anomalies(anomalies, min_support=2)
        if sigs:
            assert len(sigs[0].source_anomalies) > 0


class TestSignatureDatabase:

    def setup_method(self):
        self.db = SignatureDatabase()

    def create_signature(self, sig_id="test_sig", pattern="test pattern"):
        return Signature(
            signature_id=sig_id,
            name="test_signature",
            pattern=pattern,
            rule_type="falco",
            confidence=0.85,
            created_at="2024-01-15T12:00:00",
            source_anomalies=["a1", "a2"],
            rule_text="test rule text",
        )

    def test_add_signature_succeeds_when_no_conflicts(self):
        sig = self.create_signature()
        result = self.db.add(sig)
        assert result["added"] is True

    def test_load_all_returns_empty_when_no_file(self):
        sigs = self.db.load_all()
        assert sigs == []

    def test_add_and_load_roundtrip(self):
        sig = self.create_signature("sig_001")
        self.db.add(sig)
        loaded = self.db.load_all()
        assert len(loaded) == 1
        assert loaded[0].signature_id == "sig_001"

    def test_conflict_detection_rejects_similar_patterns(self):
        # Use patterns with >70% word overlap to trigger conflict
        sig1 = self.create_signature("sig1", pattern="syscall execve process bash user attacker")
        sig2 = self.create_signature("sig2", pattern="syscall execve process bash user malicious")

        self.db.add(sig1)
        result2 = self.db.add(sig2)

        # Should conflict due to high word overlap (5/6 words match)
        assert result2["added"] is False
        assert result2["reason"] == "conflict"

    def test_export_rules_creates_file(self):
        sig = self.create_signature()
        self.db.add(sig)
        output = self.db.export_rules("falco")
        assert output.exists()
        output.unlink()
