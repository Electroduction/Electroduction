"""
Contrastive Preference Optimization (CPO) Engine
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Stores (query, generic_answer, expert_answer) triplets for fine-tuning.
The database expert answer ALWAYS wins over generic LLM output.
Triplets are used as training signal for future fine-tuning runs.

SELF-CORRECTION BLOCK:
    What Could Break:
      1. Triplet file grows unbounded — add rotation/archive
      2. Generic answer blank — still logs with empty string
      3. Confidence mis-calibrated — adjust scoring weights
    How to Test:
      pytest tests/test_cpo_engine.py -v
"""

import json
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


TRIPLETS_DIR = Path("databases/cpo_triplets")
TRIPLETS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CPOTriplet:
    """A training triplet: input + rejected (generic) + chosen (expert)."""
    query: str
    domain: str
    generic_answer: str   # "rejected" in DPO terminology
    expert_answer: str    # "chosen" in DPO terminology
    confidence: float
    timestamp: str
    source_files: list[str]


class CPOEngine:
    """
    Records and stores CPO triplets for fine-tuning.
    Use the stored JSONL file to run DPO fine-tuning later.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.triplet_file = TRIPLETS_DIR / f"{domain}_triplets.jsonl"
        self.conflict_file = TRIPLETS_DIR / f"{domain}_conflicts.csv"

    def record(
        self,
        query: str,
        generic_answer: str,
        expert_results: list[dict],
    ) -> CPOTriplet:
        """Record a triplet and return the resolved expert answer."""
        expert_answer = json.dumps(expert_results, indent=2)
        source_files = [r.get("source_file", "") for r in expert_results if "source_file" in r]

        confidence = min(0.6 + len(expert_results) * 0.1, 0.99) if expert_results else 0.2

        triplet = CPOTriplet(
            query=query,
            domain=self.domain,
            generic_answer=generic_answer,
            expert_answer=expert_answer,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
            source_files=source_files,
        )

        # Save to JSONL (append)
        with open(self.triplet_file, "a") as f:
            f.write(json.dumps(asdict(triplet)) + "\n")

        # Log conflicts separately
        if generic_answer and generic_answer != expert_answer:
            self._log_conflict(query, generic_answer, expert_answer)

        return triplet

    def _log_conflict(self, query: str, generic: str, expert: str):
        """Log conflicts where DB differs from generic LLM."""
        write_header = not self.conflict_file.exists()
        with open(self.conflict_file, "a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "query", "generic_preview", "expert_preview"])
            writer.writerow([
                datetime.utcnow().isoformat(),
                query[:100],
                generic[:150],
                expert[:150],
            ])

    def load_triplets(self) -> list[CPOTriplet]:
        """Load all recorded triplets for review or fine-tuning."""
        triplets = []
        if not self.triplet_file.exists():
            return []
        with open(self.triplet_file) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    triplets.append(CPOTriplet(**data))
                except Exception:
                    pass
        return triplets

    def export_for_finetuning(self) -> Path:
        """Export triplets as HuggingFace DPO-compatible JSONL."""
        output_file = TRIPLETS_DIR / f"{self.domain}_dpo_ready.jsonl"
        triplets = self.load_triplets()

        with open(output_file, "w") as f:
            for t in triplets:
                dpo_record = {
                    "prompt": t.query,
                    "chosen": t.expert_answer,
                    "rejected": t.generic_answer,
                }
                f.write(json.dumps(dpo_record) + "\n")

        print(f"Exported {len(triplets)} triplets to {output_file}")
        return output_file

    def get_stats(self) -> dict:
        triplets = self.load_triplets()
        conflicts = sum(1 for t in triplets if t.generic_answer != t.expert_answer)
        avg_confidence = sum(t.confidence for t in triplets) / len(triplets) if triplets else 0.0
        return {
            "domain": self.domain,
            "total_triplets": len(triplets),
            "conflicts_logged": conflicts,
            "avg_confidence": round(avg_confidence, 3),
        }


class ActiveLearner:
    """
    Identifies what the AI doesn't know and flags gaps for data collection.
    Tracks low-confidence queries for human expert review.
    """

    def __init__(self, confidence_threshold: float = 0.5):
        self.threshold = confidence_threshold
        self.gap_log_file = TRIPLETS_DIR / "knowledge_gaps.jsonl"

    def check(self, query: str, domain: str, confidence: float) -> dict:
        """Flag if the AI's confidence is below threshold."""
        is_gap = confidence < self.threshold

        if is_gap:
            gap = {
                "query": query,
                "domain": domain,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
                "action": "add_data_for_this_query",
            }
            with open(self.gap_log_file, "a") as f:
                f.write(json.dumps(gap) + "\n")

        return {
            "is_knowledge_gap": is_gap,
            "confidence": confidence,
            "suggestion": f"Add more '{domain}' data about: {query[:80]}" if is_gap else "OK",
        }

    def get_top_gaps(self, n: int = 10) -> list[dict]:
        """Return the most common knowledge gaps to prioritize for data collection."""
        if not self.gap_log_file.exists():
            return []
        gaps = []
        with open(self.gap_log_file) as f:
            for line in f:
                try:
                    gaps.append(json.loads(line.strip()))
                except Exception:
                    pass
        return gaps[-n:]


if __name__ == "__main__":
    engine = CPOEngine("finance")
    triplet = engine.record(
        query="What is the PE ratio for AAPL?",
        generic_answer="The PE ratio is around 28.",
        expert_results=[{"pe_ratio": 28.5, "source": "sample_metrics.json"}],
    )
    print("Recorded triplet:", triplet.query)
    print("Stats:", engine.get_stats())

    learner = ActiveLearner()
    gap_check = learner.check("What is the 2026 Fed funds rate?", "finance", confidence=0.2)
    print("Gap check:", gap_check)
