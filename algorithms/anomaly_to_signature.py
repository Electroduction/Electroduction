"""
Anomaly-to-Signature Mapper — Cybersecurity Domain
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Converts raw log anomalies into actionable defense signatures.
The AI learns to recognize patterns and auto-generates Falco/Snort rules.

Key Concept: Transform unknown anomalies → known attack signatures
Use Case: Falco log shows weird syscall pattern → generates new detection rule

SELF-CORRECTION BLOCK:
    What Could Break:
      1. False positives — signature too broad, catches normal traffic
      2. Signature collision — new rule conflicts with existing rules
      3. Overfitting — signature only matches the specific anomaly instance
    How to Test:
      pytest tests/test_anomaly_to_signature.py -v
    How to Fix:
      Add negative examples (normal logs) to training
      Use rule conflict checker before adding to database
      Test signature on wider anomaly dataset before finalizing
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from collections import Counter


@dataclass
class Anomaly:
    """A detected anomaly in logs/network traffic."""
    timestamp: str
    source: str           # "falco" | "network" | "system"
    raw_log: str
    features: dict        # extracted features (syscalls, IPs, ports, etc.)
    severity: float       # 0.0-1.0


@dataclass
class Signature:
    """A defense signature/rule generated from anomalies."""
    signature_id: str
    name: str
    pattern: str          # regex or structured pattern
    rule_type: str        # "falco" | "snort" | "yara" | "sigma"
    confidence: float
    created_at: str
    source_anomalies: list[str]  # IDs of anomalies that led to this signature
    rule_text: str        # actual deployable rule


SIGNATURES_DIR = Path("databases/cybersecurity/signatures")
SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)


class AnomalyParser:
    """Extracts structured features from raw log entries."""

    SYSCALL_PATTERN = re.compile(r'syscall=([a-z_]+)')
    IP_PATTERN = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    PORT_PATTERN = re.compile(r'port=(\d+)')
    PROCESS_PATTERN = re.compile(r'proc\.name=([^\s]+)')

    def parse(self, raw_log: str, source: str = "falco") -> dict:
        """Extract structured features from raw log."""
        features = {
            "syscalls": self.SYSCALL_PATTERN.findall(raw_log),
            "ips": self.IP_PATTERN.findall(raw_log),
            "ports": self.PORT_PATTERN.findall(raw_log),
            "processes": self.PROCESS_PATTERN.findall(raw_log),
        }

        # Source-specific parsing
        if source == "falco":
            features["rule"] = self._extract_falco_rule(raw_log)
        elif source == "network":
            features["protocol"] = self._extract_protocol(raw_log)

        return features

    def _extract_falco_rule(self, log: str) -> Optional[str]:
        match = re.search(r'rule=([^\s]+)', log)
        return match.group(1) if match else None

    def _extract_protocol(self, log: str) -> Optional[str]:
        for proto in ["TCP", "UDP", "ICMP", "HTTP", "HTTPS"]:
            if proto.lower() in log.lower():
                return proto
        return None


class SignatureGenerator:
    """
    Generates defense signatures from clustered anomalies.

    Strategy: Find common patterns across multiple anomalies,
    then create a signature that matches those patterns.
    """

    def __init__(self):
        self.parser = AnomalyParser()

    def generate_from_anomalies(
        self,
        anomalies: list[Anomaly],
        min_support: int = 3,
        confidence_threshold: float = 0.6,
    ) -> list[Signature]:
        """
        Generate signatures from a set of related anomalies.

        min_support: Minimum number of anomalies needed to form a signature
        confidence_threshold: Minimum confidence to generate signature
        """
        if len(anomalies) < min_support:
            return []

        # Find common patterns
        all_features = [a.features for a in anomalies]
        common = self._find_common_features(all_features)

        if not common:
            return []

        # Generate signatures for different rule types
        signatures = []

        # Falco rule
        if any(a.source == "falco" for a in anomalies):
            falco_sig = self._generate_falco_rule(common, anomalies)
            if falco_sig:
                signatures.append(falco_sig)

        # Snort rule (network-based)
        if any(a.source == "network" for a in anomalies):
            snort_sig = self._generate_snort_rule(common, anomalies)
            if snort_sig:
                signatures.append(snort_sig)

        return [s for s in signatures if s.confidence >= confidence_threshold]

    def _find_common_features(self, features_list: list[dict]) -> dict:
        """Find features that appear in majority of anomalies."""
        common = {}

        # Syscalls
        all_syscalls = [sc for f in features_list for sc in f.get("syscalls", [])]
        if all_syscalls:
            syscall_counts = Counter(all_syscalls)
            threshold = len(features_list) * 0.5  # appear in 50%+ of logs
            common["syscalls"] = [sc for sc, cnt in syscall_counts.items() if cnt >= threshold]

        # Processes
        all_processes = [p for f in features_list for p in f.get("processes", [])]
        if all_processes:
            proc_counts = Counter(all_processes)
            threshold = len(features_list) * 0.5
            common["processes"] = [p for p, cnt in proc_counts.items() if cnt >= threshold]

        # Ports
        all_ports = [p for f in features_list for p in f.get("ports", [])]
        if all_ports:
            port_counts = Counter(all_ports)
            common["ports"] = [p for p, cnt in port_counts.items() if cnt >= 2]

        return common

    def _generate_falco_rule(self, common: dict, anomalies: list[Anomaly]) -> Optional[Signature]:
        """Generate a Falco YAML rule from common features."""
        if not common.get("syscalls") and not common.get("processes"):
            return None

        rule_name = f"anomaly_detect_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        conditions = []
        if common.get("syscalls"):
            syscalls = " or ".join(f"evt.type={sc}" for sc in common["syscalls"])
            conditions.append(f"({syscalls})")
        if common.get("processes"):
            procs = " or ".join(f'proc.name="{p}"' for p in common["processes"])
            conditions.append(f"({procs})")

        condition = " and ".join(conditions)

        rule_text = f"""- rule: {rule_name}
  desc: Auto-generated rule from anomaly cluster
  condition: {condition}
  output: "Anomaly detected: %evt.type %proc.name (user=%user.name)"
  priority: WARNING
  tags: [anomaly, auto_generated]
"""

        confidence = min(0.5 + len(anomalies) * 0.1, 0.95)

        return Signature(
            signature_id=f"falco_{rule_name}",
            name=rule_name,
            pattern=condition,
            rule_type="falco",
            confidence=confidence,
            created_at=datetime.utcnow().isoformat(),
            source_anomalies=[a.timestamp for a in anomalies],
            rule_text=rule_text,
        )

    def _generate_snort_rule(self, common: dict, anomalies: list[Anomaly]) -> Optional[Signature]:
        """Generate a Snort rule from network anomaly patterns."""
        if not common.get("ports") and not common.get("ips"):
            return None

        rule_id = f"1{datetime.utcnow().strftime('%H%M%S')}"
        rule_name = f"anomaly_network_{rule_id}"

        # Snort rule format: alert protocol src_ip src_port -> dst_ip dst_port (msg:"..."; sid:...)
        protocol = "tcp"  # default
        ports = common.get("ports", ["any"])[0] if common.get("ports") else "any"

        rule_text = f'alert {protocol} any any -> any {ports} (msg:"Network anomaly pattern detected"; sid:{rule_id}; rev:1;)'

        confidence = min(0.5 + len(anomalies) * 0.08, 0.9)

        return Signature(
            signature_id=f"snort_{rule_id}",
            name=rule_name,
            pattern=rule_text,
            rule_type="snort",
            confidence=confidence,
            created_at=datetime.utcnow().isoformat(),
            source_anomalies=[a.timestamp for a in anomalies],
            rule_text=rule_text,
        )


class SignatureDatabase:
    """Stores and manages generated signatures with conflict detection."""

    def __init__(self):
        self.db_file = SIGNATURES_DIR / "generated_signatures.jsonl"
        self.conflict_log = SIGNATURES_DIR / "signature_conflicts.jsonl"

    def add(self, signature: Signature) -> dict:
        """Add signature to database after conflict check."""
        existing = self.load_all()

        # Check for conflicts
        conflicts = self._check_conflicts(signature, existing)

        if conflicts:
            self._log_conflict(signature, conflicts)
            return {
                "added": False,
                "reason": "conflict",
                "conflicts": [c.signature_id for c in conflicts],
            }

        # Save signature
        with open(self.db_file, "a") as f:
            f.write(json.dumps(asdict(signature)) + "\n")

        return {
            "added": True,
            "signature_id": signature.signature_id,
            "confidence": signature.confidence,
        }

    def load_all(self) -> list[Signature]:
        """Load all stored signatures."""
        if not self.db_file.exists():
            return []
        signatures = []
        with open(self.db_file) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    signatures.append(Signature(**data))
                except Exception:
                    pass
        return signatures

    def _check_conflicts(self, new_sig: Signature, existing: list[Signature]) -> list[Signature]:
        """Check if new signature conflicts with existing ones."""
        conflicts = []
        for sig in existing:
            if sig.rule_type != new_sig.rule_type:
                continue
            # Check pattern overlap (simple string similarity for now)
            if self._patterns_overlap(new_sig.pattern, sig.pattern):
                conflicts.append(sig)
        return conflicts

    def _patterns_overlap(self, p1: str, p2: str) -> bool:
        """Simple overlap check — upgrade to semantic similarity later."""
        words1 = set(p1.lower().split())
        words2 = set(p2.lower().split())
        overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
        return overlap > 0.7  # 70% word overlap = conflict

    def _log_conflict(self, new_sig: Signature, conflicts: list[Signature]):
        """Log signature conflicts for review."""
        conflict_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "new_signature": new_sig.signature_id,
            "conflicts_with": [c.signature_id for c in conflicts],
            "new_pattern": new_sig.pattern,
        }
        with open(self.conflict_log, "a") as f:
            f.write(json.dumps(conflict_record) + "\n")

    def export_rules(self, rule_type: str = "falco") -> Path:
        """Export all rules of a specific type to a deployable file."""
        signatures = [s for s in self.load_all() if s.rule_type == rule_type]
        output_file = SIGNATURES_DIR / f"{rule_type}_rules_generated.yaml"

        with open(output_file, "w") as f:
            if rule_type == "falco":
                f.write("# Auto-generated Falco rules from anomaly analysis\n\n")
            for sig in signatures:
                f.write(sig.rule_text + "\n")

        return output_file


if __name__ == "__main__":
    # Example: Process anomaly logs and generate signatures
    parser = AnomalyParser()
    generator = SignatureGenerator()
    db = SignatureDatabase()

    # Sample anomaly logs (in real system: read from databases/cybersecurity/falco/)
    sample_logs = [
        "2024-01-15 12:34:56 syscall=execve proc.name=bash user.name=attacker",
        "2024-01-15 12:35:02 syscall=execve proc.name=bash user.name=attacker",
        "2024-01-15 12:35:08 syscall=execve proc.name=bash user.name=suspicious",
    ]

    anomalies = []
    for i, log in enumerate(sample_logs):
        features = parser.parse(log, source="falco")
        anomaly = Anomaly(
            timestamp=f"2024-01-15T12:35:{i:02d}",
            source="falco",
            raw_log=log,
            features=features,
            severity=0.8,
        )
        anomalies.append(anomaly)

    # Generate signatures
    signatures = generator.generate_from_anomalies(anomalies, min_support=2)
    print(f"Generated {len(signatures)} signature(s)")

    for sig in signatures:
        result = db.add(sig)
        print(f"Signature {sig.signature_id}: {result}")

    # Export to deployable file
    if signatures:
        output = db.export_rules("falco")
        print(f"\nExported rules to: {output}")
