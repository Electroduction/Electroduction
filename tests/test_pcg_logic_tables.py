"""
Tests for algorithms/pcg_logic_tables.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_pcg_logic_tables.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.pcg_logic_tables import (
    LogicTable, LogicRule, PlatformerLevelGenerator,
    LootGenerator, PCGDatabase, GeneratedAsset, LOGIC_TABLES_DIR
)


@pytest.fixture(autouse=True)
def cleanup_pcg():
    """Clean up generated PCG files."""
    yield
    if LOGIC_TABLES_DIR.exists():
        for f in LOGIC_TABLES_DIR.glob("*.json*"):
            f.unlink()


class TestLogicTable:

    def setup_method(self):
        self.table = LogicTable("test_domain")

    def test_add_rule_increases_count(self):
        rule = LogicRule("r1", "test", {"x": 1}, {"y": 2}, priority=1)
        self.table.add_rule(rule)
        assert len(self.table.rules) == 1

    def test_add_rule_sorts_by_priority(self):
        r1 = LogicRule("r1", "test", {}, {}, priority=1)
        r2 = LogicRule("r2", "test", {}, {}, priority=10)
        r3 = LogicRule("r3", "test", {}, {}, priority=5)
        self.table.add_rule(r1)
        self.table.add_rule(r2)
        self.table.add_rule(r3)
        # Should be sorted: r2 (10), r3 (5), r1 (1)
        assert self.table.rules[0].rule_id == "r2"
        assert self.table.rules[1].rule_id == "r3"
        assert self.table.rules[2].rule_id == "r1"

    def test_match_finds_matching_rule(self):
        rule = LogicRule("r1", "test", {"difficulty": "easy"}, {"x": 1})
        self.table.add_rule(rule)
        matched = self.table.match({"difficulty": "easy"})
        assert len(matched) == 1
        assert matched[0].rule_id == "r1"

    def test_match_returns_empty_when_no_match(self):
        rule = LogicRule("r1", "test", {"difficulty": "easy"}, {"x": 1})
        self.table.add_rule(rule)
        matched = self.table.match({"difficulty": "hard"})
        assert matched == []

    def test_match_handles_numeric_ranges(self):
        rule = LogicRule("r1", "test", {"score": {"min": 50, "max": 100}}, {})
        self.table.add_rule(rule)
        matched_in_range = self.table.match({"score": 75})
        matched_out_of_range = self.table.match({"score": 25})
        assert len(matched_in_range) == 1
        assert len(matched_out_of_range) == 0

    def test_save_and_load_roundtrip(self):
        rule = LogicRule("r1", "test", {"x": 1}, {"y": 2}, priority=5)
        self.table.add_rule(rule)
        self.table.save()

        table2 = LogicTable("test_domain")
        table2.load()
        assert len(table2.rules) == 1
        assert table2.rules[0].rule_id == "r1"


class TestPlatformerLevelGenerator:

    def setup_method(self):
        self.gen = PlatformerLevelGenerator()

    def test_generate_returns_generated_asset(self):
        level = self.gen.generate("easy", length=30)
        assert isinstance(level, GeneratedAsset)

    def test_generate_asset_type_is_level(self):
        level = self.gen.generate("easy")
        assert level.asset_type == "level"

    def test_generate_genre_is_platformer(self):
        level = self.gen.generate("easy")
        assert level.genre == "platformer"

    def test_generate_easy_has_low_enemy_density(self):
        level = self.gen.generate("easy", length=50)
        enemy_count = len(level.properties["enemies"])
        # Easy mode should have fewer enemies
        assert enemy_count < 10

    def test_generate_hard_has_high_enemy_density(self):
        level = self.gen.generate("hard", length=50)
        enemy_count = len(level.properties["enemies"])
        # Hard mode should have more enemies
        assert enemy_count >= 2

    def test_generate_hard_has_hazards(self):
        level = self.gen.generate("hard", length=50)
        assert "hazards" in level.properties
        # Hard levels should include hazards
        assert len(level.properties["hazards"]) > 0

    def test_generate_applies_rule_ids(self):
        level = self.gen.generate("easy")
        assert len(level.rules_applied) > 0

    def test_generate_creates_platforms(self):
        level = self.gen.generate("easy", length=30)
        assert "platforms" in level.properties
        assert len(level.properties["platforms"]) > 0


class TestLootGenerator:

    def setup_method(self):
        self.gen = LootGenerator()

    def test_generate_returns_generated_asset(self):
        loot = self.gen.generate("boss", player_level=10)
        assert isinstance(loot, GeneratedAsset)

    def test_generate_boss_loot_is_legendary(self):
        loot = self.gen.generate("boss", player_level=10)
        assert loot.properties["rarity"] == "legendary"

    def test_generate_common_enemy_loot_is_common(self):
        loot = self.gen.generate("common_enemy", player_level=10)
        assert loot.properties["rarity"] == "common"

    def test_generate_boss_loot_has_higher_stats(self):
        boss_loot = self.gen.generate("boss", player_level=10)
        common_loot = self.gen.generate("common_enemy", player_level=10)
        assert boss_loot.properties["damage"] > common_loot.properties["damage"]

    def test_generate_scales_with_player_level(self):
        low_level = self.gen.generate("boss", player_level=5)
        high_level = self.gen.generate("boss", player_level=50)
        assert high_level.properties["damage"] > low_level.properties["damage"]

    def test_generate_boss_has_special_effect(self):
        loot = self.gen.generate("boss", player_level=10)
        assert loot.properties.get("special_effect") is True

    def test_generate_common_no_special_effect(self):
        loot = self.gen.generate("common_enemy", player_level=10)
        assert loot.properties.get("special_effect") is False


class TestPCGDatabase:

    def setup_method(self):
        self.db = PCGDatabase()

    def test_save_creates_file(self):
        asset = GeneratedAsset(
            asset_id="test_001",
            asset_type="level",
            genre="platformer",
            properties={},
            rules_applied=["rule1"],
            created_at="2024-01-15T12:00:00",
        )
        self.db.save(asset)
        assert self.db.db_file.exists()

    def test_load_all_empty_when_no_file(self):
        assets = self.db.load_all()
        assert assets == []

    def test_save_and_load_roundtrip(self):
        asset = GeneratedAsset(
            asset_id="test_002",
            asset_type="loot",
            genre="rpg",
            properties={"damage": 50},
            rules_applied=["boss_loot"],
            created_at="2024-01-15T12:00:00",
            quality_score=0.9,
        )
        self.db.save(asset)
        loaded = self.db.load_all()
        assert len(loaded) == 1
        assert loaded[0].asset_id == "test_002"
        assert loaded[0].quality_score == 0.9

    def test_get_high_quality_filters_correctly(self):
        a1 = GeneratedAsset("a1", "level", "platformer", {}, [], "2024-01-15", quality_score=0.9)
        a2 = GeneratedAsset("a2", "level", "platformer", {}, [], "2024-01-15", quality_score=0.5)
        self.db.save(a1)
        self.db.save(a2)
        high_quality = self.db.get_high_quality(min_score=0.7)
        assert len(high_quality) == 1
        assert high_quality[0].asset_id == "a1"
