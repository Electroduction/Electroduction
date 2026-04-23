"""
Chain-of-Thought (CoT) Verifier — Forces AI to Show Work
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Forces the AI to show reasoning steps against database rules before giving a final answer.
Catches hallucinations early: if the AI can't cite a database source for each reasoning step, reject.

Key Concept: "Show your work" for AI answers
Use Case: Finance AI says "PE ratio is too high" → must cite DB rule "PE > 30 = overvalued for tech"

SELF-CORRECTION BLOCK:
    What Could Break:
      1. AI generates fake citations (hallucinated sources)
      2. Reasoning steps too vague to verify
      3. Database missing the actual rule the AI needs
    How to Test:
      pytest tests/test_cot_verifier.py -v
    How to Fix:
      Cross-check citations against actual database files
      Require specific format: [Source: filename.json, line X, rule Y]
      Add "citation verification" step — reject if source not found
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Literal


@dataclass
class ReasoningStep:
    """A single step in chain-of-thought reasoning."""
    step_number: int
    claim: str
    citation: Optional[str] = None  # database source backing this claim
    verified: bool = False
    verification_note: str = ""


@dataclass
class CoTAnswer:
    """An answer with chain-of-thought reasoning."""
    query: str
    domain: str
    reasoning_steps: list[ReasoningStep]
    final_answer: str
    overall_verified: bool
    confidence: float
    timestamp: str


class CitationParser:
    """Extracts citations from AI output."""

    # Expected citation format: [Source: data/finance/metrics.json | Rule: PE_ratio_threshold]
    CITATION_PATTERN = re.compile(r'\[Source:\s*([^\|]+)\s*\|\s*Rule:\s*([^\]]+)\]')

    def extract_citations(self, text: str) -> list[dict]:
        """Extract all citations from text."""
        matches = self.CITATION_PATTERN.findall(text)
        return [
            {"source_file": m[0].strip(), "rule_name": m[1].strip()}
            for m in matches
        ]

    def has_citation(self, text: str) -> bool:
        """Check if text contains any citations."""
        return bool(self.CITATION_PATTERN.search(text))


class DatabaseRuleChecker:
    """
    Verifies that cited database rules actually exist.

    In production: Load all JSON rules into memory at startup.
    For now: Check file existence and parse JSON.
    """

    def __init__(self, db_root: Path):
        self.db_root = db_root
        self._rule_cache: dict[str, dict] = {}

    def verify_citation(self, citation: dict) -> dict:
        """
        Verify that a citation refers to a real database entry.

        Returns: {"verified": bool, "note": str, "rule_data": dict}
        """
        source_file = citation["source_file"]
        rule_name = citation["rule_name"]

        # Construct full path
        if not source_file.startswith("/"):
            full_path = self.db_root / source_file
        else:
            full_path = Path(source_file)

        # Check file exists
        if not full_path.exists():
            return {
                "verified": False,
                "note": f"File not found: {source_file}",
                "rule_data": None,
            }

        # Load and check for rule
        try:
            rule_data = self._load_rule(full_path, rule_name)
            if rule_data:
                return {
                    "verified": True,
                    "note": f"Rule '{rule_name}' found in {source_file}",
                    "rule_data": rule_data,
                }
            else:
                return {
                    "verified": False,
                    "note": f"Rule '{rule_name}' not found in {source_file}",
                    "rule_data": None,
                }
        except Exception as e:
            return {
                "verified": False,
                "note": f"Error loading {source_file}: {e}",
                "rule_data": None,
            }

    def _load_rule(self, file_path: Path, rule_name: str) -> Optional[dict]:
        """Load specific rule from JSON file."""
        cache_key = str(file_path)

        # Check cache
        if cache_key not in self._rule_cache:
            with open(file_path) as f:
                self._rule_cache[cache_key] = json.load(f)

        data = self._rule_cache[cache_key]

        # Search for rule by name (handle different JSON structures)
        if isinstance(data, dict):
            # Direct lookup
            if rule_name in data:
                return {rule_name: data[rule_name]}
            # Nested search
            for key, value in data.items():
                if isinstance(value, dict) and rule_name in str(value):
                    return value
        elif isinstance(data, list):
            # List of rules
            for item in data:
                if isinstance(item, dict) and item.get("name") == rule_name:
                    return item

        return None


class CoTVerifier:
    """
    Verifies chain-of-thought reasoning against database rules.

    Process:
    1. Parse AI output into reasoning steps
    2. Extract citations from each step
    3. Verify each citation against database
    4. Reject answer if any step lacks valid citation
    """

    def __init__(self, db_root: Path, strict_mode: bool = True):
        self.db_root = db_root
        self.strict_mode = strict_mode  # require citation for EVERY step
        self.parser = CitationParser()
        self.rule_checker = DatabaseRuleChecker(db_root)

    def verify(self, query: str, domain: str, ai_output: str) -> CoTAnswer:
        """
        Verify an AI's chain-of-thought answer.

        ai_output format expected:
        ```
        Step 1: [claim] [Source: ... | Rule: ...]
        Step 2: [claim] [Source: ... | Rule: ...]
        Final Answer: [answer]
        ```
        """
        # Parse into steps
        steps = self._parse_steps(ai_output)

        # Verify each step
        verified_steps = []
        for step in steps:
            verified_step = self._verify_step(step)
            verified_steps.append(verified_step)

        # Extract final answer
        final_answer = self._extract_final_answer(ai_output)

        # Overall verification
        all_verified = all(s.verified or not self.strict_mode for s in verified_steps)
        confidence = self._calculate_confidence(verified_steps)

        return CoTAnswer(
            query=query,
            domain=domain,
            reasoning_steps=verified_steps,
            final_answer=final_answer,
            overall_verified=all_verified,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
        )

    def _parse_steps(self, output: str) -> list[ReasoningStep]:
        """Parse AI output into reasoning steps."""
        steps = []
        lines = output.split("\n")

        step_num = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match "Step N:" or numbered list
            if re.match(r'^(Step\s+\d+:|[\d]+\.)', line, re.IGNORECASE):
                step_num += 1
                # Extract claim (everything before citation if present)
                citations = self.parser.extract_citations(line)
                claim = re.sub(self.parser.CITATION_PATTERN, '', line).strip()

                step = ReasoningStep(
                    step_number=step_num,
                    claim=claim,
                    citation=json.dumps(citations[0]) if citations else None,
                )
                steps.append(step)

        return steps

    def _verify_step(self, step: ReasoningStep) -> ReasoningStep:
        """Verify a single reasoning step's citation."""
        if not step.citation:
            step.verified = False
            step.verification_note = "No citation provided"
            return step

        citation = json.loads(step.citation)
        result = self.rule_checker.verify_citation(citation)

        step.verified = result["verified"]
        step.verification_note = result["note"]

        return step

    def _extract_final_answer(self, output: str) -> str:
        """Extract the final answer from output."""
        match = re.search(r'Final Answer:\s*(.+)', output, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: last line
        lines = [l.strip() for l in output.split("\n") if l.strip()]
        return lines[-1] if lines else ""

    def _calculate_confidence(self, steps: list[ReasoningStep]) -> float:
        """Calculate confidence based on verification rate."""
        if not steps:
            return 0.0

        verified_count = sum(1 for s in steps if s.verified)
        base_confidence = verified_count / len(steps)

        # Boost if all steps verified
        if verified_count == len(steps):
            return min(base_confidence + 0.2, 0.99)

        return base_confidence


class CoTDatabase:
    """Stores verified and rejected CoT answers for training."""

    def __init__(self, domain: str):
        self.domain = domain
        self.verified_file = Path(f"databases/cot_verified/{domain}_verified.jsonl")
        self.rejected_file = Path(f"databases/cot_verified/{domain}_rejected.jsonl")
        self.verified_file.parent.mkdir(parents=True, exist_ok=True)

    def save(self, cot_answer: CoTAnswer):
        """Save CoT answer to appropriate file."""
        target = self.verified_file if cot_answer.overall_verified else self.rejected_file
        with open(target, "a") as f:
            f.write(json.dumps(asdict(cot_answer)) + "\n")

    def load_verified(self) -> list[CoTAnswer]:
        """Load all verified answers (good training examples)."""
        return self._load_from_file(self.verified_file)

    def load_rejected(self) -> list[CoTAnswer]:
        """Load all rejected answers (bad examples to avoid)."""
        return self._load_from_file(self.rejected_file)

    def _load_from_file(self, file_path: Path) -> list[CoTAnswer]:
        if not file_path.exists():
            return []
        answers = []
        with open(file_path) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # Reconstruct ReasoningSteps
                    data["reasoning_steps"] = [
                        ReasoningStep(**s) for s in data["reasoning_steps"]
                    ]
                    answers.append(CoTAnswer(**data))
                except Exception:
                    pass
        return answers

    def get_stats(self) -> dict:
        verified = self.load_verified()
        rejected = self.load_rejected()
        total = len(verified) + len(rejected)
        return {
            "domain": self.domain,
            "verified": len(verified),
            "rejected": len(rejected),
            "verification_rate": len(verified) / total if total > 0 else 0.0,
        }


if __name__ == "__main__":
    # Example: Verify a finance AI's reasoning
    verifier = CoTVerifier(db_root=Path("data"), strict_mode=True)
    db = CoTDatabase("finance")

    sample_output = """
Step 1: AAPL's PE ratio is 28.5 [Source: data/finance/sample_metrics.json | Rule: pe_ratio]
Step 2: For tech stocks, PE > 30 is considered overvalued [Source: data/finance/valuation_rules.json | Rule: tech_pe_threshold]
Step 3: Therefore AAPL is fairly valued, not overvalued
Final Answer: AAPL is fairly valued with PE ratio of 28.5
"""

    result = verifier.verify(
        query="Is AAPL overvalued?",
        domain="finance",
        ai_output=sample_output,
    )

    print(f"Query: {result.query}")
    print(f"Overall verified: {result.overall_verified}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"\nReasoning steps:")
    for step in result.reasoning_steps:
        status = "✓" if step.verified else "✗"
        print(f"  {status} Step {step.step_number}: {step.claim[:60]}...")
        print(f"     Note: {step.verification_note}")

    print(f"\nFinal answer: {result.final_answer}")

    # Save to database
    db.save(result)
    print(f"\nSaved to {db.verified_file if result.overall_verified else db.rejected_file}")
    print(f"Stats: {db.get_stats()}")
