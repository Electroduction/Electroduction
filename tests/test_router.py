"""
Tests for algorithms/router_agent.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_router.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.router_agent import RouterAgent, TemporalAttentionAgent, RouteDecision, DOMAIN_KEYWORDS


class TestRouterAgent:

    def setup_method(self):
        self.router = RouterAgent()

    def test_cybersecurity_routing(self):
        decision = self.router.route("How do I detect a Falco intrusion log?")
        assert decision.domain == "cybersecurity"
        assert decision.confidence > 0.5
        assert "falco" in decision.keywords_matched or "intrusion" in decision.keywords_matched

    def test_finance_routing(self):
        decision = self.router.route("What is the PE ratio and ROE for AAPL stock?")
        assert decision.domain == "finance"
        assert decision.confidence > 0.5

    def test_music_routing(self):
        decision = self.router.route("Create a lo-fi jazz chord progression at 80 BPM")
        assert decision.domain == "music"
        assert decision.confidence > 0.5

    def test_game_dev_routing(self):
        decision = self.router.route("Generate a pixel art character for my platformer game")
        assert decision.domain == "game_dev"
        assert decision.confidence > 0.5

    def test_video_routing(self):
        decision = self.router.route("What is the best hook for my YouTube tutorial video?")
        assert decision.domain == "video"
        assert decision.confidence > 0.5

    def test_creativity_routing(self):
        decision = self.router.route("Write a three-act story about a time-traveling hero archetype")
        assert decision.domain == "creativity"
        assert decision.confidence > 0.5

    def test_fallback_routing_returns_default(self):
        decision = self.router.route("xyzzy nonexistent gibberish aaabbbccc")
        assert decision.strategy == "fallback"
        assert decision.confidence <= 0.3
        assert decision.keywords_matched == []

    def test_route_decision_is_dataclass(self):
        decision = self.router.route("malware attack")
        assert isinstance(decision, RouteDecision)
        assert hasattr(decision, "domain")
        assert hasattr(decision, "confidence")
        assert hasattr(decision, "strategy")
        assert hasattr(decision, "keywords_matched")

    def test_confidence_capped_at_099(self):
        # Many keywords — confidence should not exceed 0.99
        query = " ".join(DOMAIN_KEYWORDS["finance"])
        decision = self.router.route(query)
        assert decision.confidence <= 0.99

    def test_confidence_minimum_on_single_keyword(self):
        decision = self.router.route("stock")
        assert 0.5 <= decision.confidence <= 0.7

    def test_multi_route_returns_list(self):
        decisions = self.router.route_multi("jazz chord for a game soundtrack", top_n=2)
        assert isinstance(decisions, list)
        assert len(decisions) >= 1
        assert all(isinstance(d, RouteDecision) for d in decisions)

    def test_multi_route_respects_top_n(self):
        decisions = self.router.route_multi("attack stock beat melody", top_n=3)
        assert len(decisions) <= 3

    def test_multi_route_sorted_by_confidence(self):
        decisions = self.router.route_multi("malware phishing attack vulnerability exploit", top_n=3)
        confidences = [d.confidence for d in decisions]
        assert confidences == sorted(confidences, reverse=True)

    def test_multi_route_fallback_on_no_match(self):
        decisions = self.router.route_multi("zzzznonexistent", top_n=2)
        assert len(decisions) >= 1
        assert decisions[0].strategy == "fallback"

    def test_domain_keywords_not_empty(self):
        for domain, keywords in DOMAIN_KEYWORDS.items():
            assert len(keywords) >= 10, f"Domain '{domain}' has fewer than 10 keywords"

    def test_all_domains_represented(self):
        expected = {"cybersecurity", "finance", "game_dev", "music", "video", "creativity"}
        assert set(DOMAIN_KEYWORDS.keys()) == expected


class TestTemporalAttentionAgent:

    def setup_method(self):
        self.agent = TemporalAttentionAgent()

    def test_process_input_returns_event(self):
        event = self.agent.process_input("detect a malware attack", elapsed_seconds=15.0)
        assert "domain" in event
        assert "confidence" in event
        assert "should_intervene" in event
        assert "elapsed_s" in event

    def test_cyber_always_intervenes(self):
        event = self.agent.process_input("phishing attack ransomware vulnerability", elapsed_seconds=0.0)
        if event["domain"] == "cybersecurity" and event["confidence"] > 0.5:
            assert event["should_intervene"] is True

    def test_no_intervene_on_low_confidence_short_pause(self):
        event = self.agent.process_input("xyzzy nonexistent", elapsed_seconds=2.0)
        assert event["should_intervene"] is False

    def test_intervene_on_long_pause_high_confidence(self):
        event = self.agent.process_input("jazz chord progression at 80 BPM melody bass", elapsed_seconds=15.0)
        if event["confidence"] > 0.6:
            assert event["should_intervene"] is True

    def test_history_accumulates(self):
        for i in range(3):
            self.agent.process_input(f"test query {i}")
        assert len(self.agent.history) == 3

    def test_input_truncated_in_history(self):
        long_input = "a" * 200
        self.agent.process_input(long_input)
        assert len(self.agent.history[-1]["input"]) <= 100
