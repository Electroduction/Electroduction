"""
Router Agent — Decides which domain database to query.
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Uses keyword matching now; upgrade to embedding-based routing later.

SELF-CORRECTION BLOCK:
    What Could Break:
      1. Ambiguous queries routed to wrong domain
      2. No domain match → falls back to "general"
    How to Test:
      pytest tests/test_router.py -v
    How to Fix:
      Add more keywords, or switch to embedding cosine similarity
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RouteDecision:
    domain: str
    confidence: float
    strategy: str  # "exact_match" | "keyword" | "fallback"
    keywords_matched: list[str]


DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "cybersecurity": [
        "attack", "exploit", "vulnerability", "cve", "falco", "log", "intrusion",
        "malware", "ransomware", "firewall", "breach", "hack", "threat", "mitre",
        "nsl-kdd", "payload", "phishing", "zero-day", "siem", "ioc", "ttps",
    ],
    "finance": [
        "stock", "price", "pe ratio", "earnings", "market", "portfolio", "equity",
        "debt", "roe", "sentiment", "bullish", "bearish", "trade", "invest",
        "sharpe", "alpha", "beta", "etf", "dividend", "fundamental", "valuation",
    ],
    "game_dev": [
        "sprite", "asset", "animation", "jump", "attack", "pixel", "tile",
        "platformer", "rpg", "fps", "sound effect", "sfx", "frame", "character",
        "texture", "level", "game design", "unity", "unreal", "genre",
    ],
    "music": [
        "chord", "melody", "beat", "tempo", "bpm", "genre", "lo-fi", "edm",
        "jazz", "drum", "bass", "synth", "scale", "key", "progression",
        "stem", "midi", "audio", "instrument", "mix", "master",
    ],
    "video": [
        "edit", "cut", "transition", "hook", "b-roll", "scene", "pacing",
        "retention", "youtube", "short", "tutorial", "footage", "cta",
        "render", "caption", "thumbnail", "vlog", "documentary",
    ],
    "creativity": [
        "story", "plot", "character", "idea", "brainstorm", "novel", "write",
        "narrative", "three-act", "hero", "archetype", "scamper", "creative",
        "concept", "product idea", "innovation", "prompt", "inspiration",
    ],
}


class RouterAgent:
    """Routes user queries to the correct domain database."""

    def route(self, query: str) -> RouteDecision:
        """Determine the best domain for a given query."""
        query_lower = query.lower()
        scores: dict[str, list[str]] = {d: [] for d in DOMAIN_KEYWORDS}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[domain].append(kw)

        # Sort by match count
        ranked = sorted(scores.items(), key=lambda x: len(x[1]), reverse=True)
        best_domain, matched = ranked[0]

        if not matched:
            return RouteDecision(
                domain="cybersecurity",  # safe default
                confidence=0.2,
                strategy="fallback",
                keywords_matched=[],
            )

        confidence = min(0.5 + len(matched) * 0.1, 0.99)
        return RouteDecision(
            domain=best_domain,
            confidence=confidence,
            strategy="keyword",
            keywords_matched=matched,
        )

    def route_multi(self, query: str, top_n: int = 2) -> list[RouteDecision]:
        """Return top N domain matches for cross-domain queries."""
        query_lower = query.lower()
        decisions = []

        for domain, keywords in DOMAIN_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in query_lower]
            if matched:
                confidence = min(0.5 + len(matched) * 0.1, 0.99)
                decisions.append(RouteDecision(
                    domain=domain,
                    confidence=confidence,
                    strategy="keyword",
                    keywords_matched=matched,
                ))

        decisions.sort(key=lambda d: d.confidence, reverse=True)
        return decisions[:top_n] if decisions else [
            RouteDecision("cybersecurity", 0.2, "fallback", [])
        ]


class TemporalAttentionAgent:
    """
    Shadowing agent — monitors user activity and triggers the right skill.
    In production: hook into OS window focus events or terminal stdin.
    """

    def __init__(self):
        self.router = RouterAgent()
        self.history: list[dict] = []
        self.pause_threshold_seconds = 10

    def process_input(self, user_text: str, elapsed_seconds: float = 0.0) -> dict:
        """Process user input and decide when/how to intervene."""
        route = self.router.route(user_text)

        event = {
            "input": user_text[:100],
            "domain": route.domain,
            "confidence": route.confidence,
            "elapsed_s": elapsed_seconds,
            "should_intervene": self._should_intervene(route, elapsed_seconds),
        }

        self.history.append(event)
        return event

    def _should_intervene(self, route: RouteDecision, elapsed: float) -> bool:
        """Decide whether to show the shadowing AI suggestion."""
        # Intervene if: user paused long + high-confidence domain match
        if elapsed > self.pause_threshold_seconds and route.confidence > 0.6:
            return True
        # Always intervene for cybersecurity threats
        if route.domain == "cybersecurity" and route.confidence > 0.5:
            return True
        return False


if __name__ == "__main__":
    router = RouterAgent()

    test_queries = [
        "How do I detect a Falco log intrusion?",
        "What is the PE ratio for AAPL?",
        "Generate a pixel art character for my platformer game",
        "Create a lo-fi jazz chord progression at 80 BPM",
        "How do I add a hook to my YouTube tutorial?",
        "Write a three-act story about a time traveler",
    ]

    print("ROUTER AGENT TEST")
    print("=" * 60)
    for q in test_queries:
        decision = router.route(q)
        print(f"\nQuery: {q[:50]}...")
        print(f"  → Domain: {decision.domain} (confidence: {decision.confidence:.2f})")
        print(f"  → Matched: {decision.keywords_matched}")
