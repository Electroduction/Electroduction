"""
PCG Logic Tables — Procedural Content Generation for Game Dev
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Rule-based procedural generation for game assets: levels, loot, NPCs, quests.
Uses logic tables (like decision trees) to generate consistent, high-quality content.

Key Concept: Instead of random generation, use domain rules from database
Use Case: "Generate a platformer level" → checks difficulty curve, jump distance rules, enemy placement logic

SELF-CORRECTION BLOCK:
    What Could Break:
      1. Generated content violates game physics (impossible jumps)
      2. Logic rules conflict (rule A says yes, rule B says no)
      3. Output too predictable — players notice the patterns
    How to Test:
      pytest tests/test_pcg_logic_tables.py -v
    How to Fix:
      Add physics validator before accepting generated content
      Implement rule priority system (core physics > aesthetic preferences)
      Add controlled randomness within valid ranges
"""

import json
import random
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Literal, Optional


@dataclass
class LogicRule:
    """A single rule in the PCG logic table."""
    rule_id: str
    domain: str          # "level_design" | "loot_generation" | "npc_behavior"
    condition: dict      # {"difficulty": "hard", "genre": "platformer"}
    action: dict         # {"enemy_density": 0.8, "jump_distance_max": 5.0}
    priority: int = 0    # higher priority rules override lower


@dataclass
class GeneratedAsset:
    """A procedurally generated game asset."""
    asset_id: str
    asset_type: str      # "level" | "loot" | "npc" | "quest"
    genre: str
    properties: dict
    rules_applied: list[str]  # rule_ids that generated this
    created_at: str
    quality_score: Optional[float] = None


LOGIC_TABLES_DIR = Path("databases/game_dev/pcg_logic_tables")
LOGIC_TABLES_DIR.mkdir(parents=True, exist_ok=True)


class LogicTable:
    """
    A table of rules for procedural generation.

    Rules are applied in priority order. If multiple rules match,
    highest priority wins.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.rules: list[LogicRule] = []
        self.table_file = LOGIC_TABLES_DIR / f"{domain}_rules.json"

    def add_rule(self, rule: LogicRule):
        """Add a rule to the table."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def match(self, context: dict) -> list[LogicRule]:
        """Find all rules that match the given context."""
        matched = []
        for rule in self.rules:
            if self._conditions_met(rule.condition, context):
                matched.append(rule)
        return matched

    def _conditions_met(self, conditions: dict, context: dict) -> bool:
        """Check if all conditions are met by the context."""
        for key, expected_value in conditions.items():
            if key not in context:
                return False
            actual_value = context[key]

            # Handle ranges for numeric values
            if isinstance(expected_value, dict) and "min" in expected_value:
                if not (expected_value.get("min", float('-inf')) <= actual_value <= expected_value.get("max", float('inf'))):
                    return False
            # Exact match for strings/simple values
            elif actual_value != expected_value:
                return False

        return True

    def save(self):
        """Save rules to disk."""
        data = [asdict(r) for r in self.rules]
        with open(self.table_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load rules from disk."""
        if not self.table_file.exists():
            return
        with open(self.table_file) as f:
            data = json.load(f)
        self.rules = [LogicRule(**r) for r in data]
        self.rules.sort(key=lambda r: r.priority, reverse=True)


class PlatformerLevelGenerator:
    """
    Generates platformer levels using logic table rules.

    Rules govern: jump distances, enemy placement, platform spacing, etc.
    """

    def __init__(self):
        self.logic_table = LogicTable("platformer_levels")
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize default platformer rules."""
        # Rule: Easy difficulty → short jumps, low enemy density
        self.logic_table.add_rule(LogicRule(
            rule_id="easy_platformer",
            domain="platformer_levels",
            condition={"difficulty": "easy"},
            action={
                "platform_spacing": {"min": 2, "max": 4},  # tiles
                "enemy_density": 0.1,
                "jump_required": False,
                "moving_platforms": False,
            },
            priority=10,
        ))

        # Rule: Hard difficulty → precise jumps, high enemy density
        self.logic_table.add_rule(LogicRule(
            rule_id="hard_platformer",
            domain="platformer_levels",
            condition={"difficulty": "hard"},
            action={
                "platform_spacing": {"min": 4, "max": 7},
                "enemy_density": 0.6,
                "jump_required": True,
                "moving_platforms": True,
                "spike_hazards": True,
            },
            priority=10,
        ))

        # Rule: Speedrun genre → long platforms, few obstacles
        self.logic_table.add_rule(LogicRule(
            rule_id="speedrun_platformer",
            domain="platformer_levels",
            condition={"genre": "speedrun"},
            action={
                "platform_length": {"min": 8, "max": 15},
                "enemy_density": 0.2,
                "collectibles": True,
            },
            priority=5,
        ))

    def generate(self, difficulty: str, length: int = 50) -> GeneratedAsset:
        """
        Generate a platformer level.

        difficulty: "easy" | "medium" | "hard"
        length: level length in tiles
        """
        context = {"difficulty": difficulty}
        matched_rules = self.logic_table.match(context)

        if not matched_rules:
            # Fallback: medium difficulty
            return self._generate_default(length)

        # Apply highest-priority rule
        rule = matched_rules[0]
        level = self._apply_rule(rule, length)

        asset_id = f"platformer_{difficulty}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return GeneratedAsset(
            asset_id=asset_id,
            asset_type="level",
            genre="platformer",
            properties=level,
            rules_applied=[r.rule_id for r in matched_rules],
            created_at=datetime.utcnow().isoformat(),
        )

    def _apply_rule(self, rule: LogicRule, length: int) -> dict:
        """Apply a rule to generate level structure."""
        action = rule.action

        # Platform spacing
        spacing_range = action.get("platform_spacing", {"min": 3, "max": 5})
        platforms = []
        x = 0
        while x < length:
            spacing = random.randint(spacing_range["min"], spacing_range["max"])
            platform_length = random.randint(3, 6)
            platforms.append({"x": x, "y": 0, "length": platform_length})
            x += platform_length + spacing

        # Enemy placement
        enemy_density = action.get("enemy_density", 0.3)
        num_enemies = int(length * enemy_density / 10)
        enemies = [
            {"x": random.randint(0, length), "y": 0, "type": "basic"}
            for _ in range(num_enemies)
        ]

        # Collectibles
        collectibles = []
        if action.get("collectibles"):
            num_collectibles = max(3, length // 10)
            collectibles = [
                {"x": random.randint(0, length), "y": random.randint(0, 5), "type": "coin"}
                for _ in range(num_collectibles)
            ]

        # Hazards
        hazards = []
        if action.get("spike_hazards"):
            num_hazards = length // 15
            hazards = [
                {"x": random.randint(0, length), "y": 0, "type": "spike"}
                for _ in range(num_hazards)
            ]

        return {
            "length": length,
            "platforms": platforms,
            "enemies": enemies,
            "collectibles": collectibles,
            "hazards": hazards,
            "requires_precise_jumps": action.get("jump_required", False),
            "has_moving_platforms": action.get("moving_platforms", False),
        }

    def _generate_default(self, length: int) -> GeneratedAsset:
        """Fallback generator for medium difficulty."""
        return GeneratedAsset(
            asset_id=f"platformer_default_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            asset_type="level",
            genre="platformer",
            properties={
                "length": length,
                "platforms": [{"x": i*10, "y": 0, "length": 5} for i in range(length//10)],
                "enemies": [],
                "collectibles": [],
                "hazards": [],
            },
            rules_applied=["default"],
            created_at=datetime.utcnow().isoformat(),
        )


class LootGenerator:
    """
    Generates loot/items using rarity and power level rules.
    """

    def __init__(self):
        self.logic_table = LogicTable("loot_generation")
        self._init_default_rules()

    def _init_default_rules(self):
        # Rule: Boss drop → high rarity
        self.logic_table.add_rule(LogicRule(
            rule_id="boss_loot",
            domain="loot_generation",
            condition={"source": "boss"},
            action={
                "rarity": "legendary",
                "stat_multiplier": {"min": 1.5, "max": 2.5},
                "special_effect": True,
            },
            priority=20,
        ))

        # Rule: Common enemy → low rarity
        self.logic_table.add_rule(LogicRule(
            rule_id="common_loot",
            domain="loot_generation",
            condition={"source": "common_enemy"},
            action={
                "rarity": "common",
                "stat_multiplier": {"min": 0.8, "max": 1.2},
                "special_effect": False,
            },
            priority=5,
        ))

    def generate(self, source: str, player_level: int) -> GeneratedAsset:
        """Generate a loot item."""
        context = {"source": source}
        matched_rules = self.logic_table.match(context)

        if not matched_rules:
            rule = None
            rarity = "common"
            stat_mult = 1.0
        else:
            rule = matched_rules[0]
            rarity = rule.action.get("rarity", "common")
            mult_range = rule.action.get("stat_multiplier", {"min": 1.0, "max": 1.0})
            stat_mult = random.uniform(mult_range["min"], mult_range["max"])

        # Generate item properties
        base_damage = player_level * 10
        item = {
            "name": f"{rarity.capitalize()} Sword",
            "rarity": rarity,
            "damage": int(base_damage * stat_mult),
            "level_requirement": player_level,
            "special_effect": rule.action.get("special_effect") if rule else False,
        }

        asset_id = f"loot_{source}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return GeneratedAsset(
            asset_id=asset_id,
            asset_type="loot",
            genre="rpg",
            properties=item,
            rules_applied=[matched_rules[0].rule_id] if matched_rules else ["default"],
            created_at=datetime.utcnow().isoformat(),
        )


class PCGDatabase:
    """Stores generated assets for review and reuse."""

    def __init__(self):
        self.db_file = LOGIC_TABLES_DIR / "generated_assets.jsonl"

    def save(self, asset: GeneratedAsset):
        with open(self.db_file, "a") as f:
            f.write(json.dumps(asdict(asset)) + "\n")

    def load_all(self) -> list[GeneratedAsset]:
        if not self.db_file.exists():
            return []
        assets = []
        with open(self.db_file) as f:
            for line in f:
                try:
                    assets.append(GeneratedAsset(**json.loads(line.strip())))
                except Exception:
                    pass
        return assets

    def get_high_quality(self, min_score: float = 0.7) -> list[GeneratedAsset]:
        """Return assets rated above quality threshold."""
        all_assets = self.load_all()
        return [a for a in all_assets if a.quality_score and a.quality_score >= min_score]


if __name__ == "__main__":
    # Example: Generate platformer level
    level_gen = PlatformerLevelGenerator()
    easy_level = level_gen.generate("easy", length=30)
    hard_level = level_gen.generate("hard", length=50)

    print(f"Easy level: {easy_level.asset_id}")
    print(f"  Platforms: {len(easy_level.properties['platforms'])}")
    print(f"  Enemies: {len(easy_level.properties['enemies'])}")
    print(f"  Rules: {easy_level.rules_applied}")

    print(f"\nHard level: {hard_level.asset_id}")
    print(f"  Platforms: {len(hard_level.properties['platforms'])}")
    print(f"  Enemies: {len(hard_level.properties['enemies'])}")
    print(f"  Hazards: {len(hard_level.properties['hazards'])}")
    print(f"  Rules: {hard_level.rules_applied}")

    # Example: Generate loot
    loot_gen = LootGenerator()
    boss_drop = loot_gen.generate("boss", player_level=20)
    common_drop = loot_gen.generate("common_enemy", player_level=5)

    print(f"\nBoss loot: {boss_drop.properties}")
    print(f"Common loot: {common_drop.properties}")

    # Save to database
    db = PCGDatabase()
    db.save(easy_level)
    db.save(hard_level)
    db.save(boss_drop)
    db.save(common_drop)

    print(f"\nSaved {len(db.load_all())} assets to database")
