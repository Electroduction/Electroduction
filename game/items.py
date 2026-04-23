"""
Items and Gear System - Weapons, armor, and loot
"""

import random

class Item:
    """Base item class"""

    def __init__(self, name, item_type, rarity="Common"):
        self.name = name
        self.item_type = item_type
        self.rarity = rarity
        self.level = 1

    def get_rarity_color(self):
        """Get color based on rarity"""
        colors = {
            "Common": (150, 150, 150),
            "Uncommon": (100, 200, 100),
            "Rare": (100, 150, 255),
            "Epic": (200, 100, 255),
            "Legendary": (255, 180, 50)
        }
        return colors.get(self.rarity, (150, 150, 150))

class Weapon(Item):
    """Weapon with damage and affixes"""

    def __init__(self, name, weapon_type, base_damage, rarity="Common"):
        super().__init__(name, "Weapon", rarity)
        self.weapon_type = weapon_type  # Sword, Hammer, Bow, Staff, etc.
        self.base_damage = base_damage
        self.attack_speed = 1.0
        self.affixes = []

    def get_total_damage(self, player_power):
        """Calculate total damage with affixes"""
        damage = self.base_damage + player_power

        # Apply affixes
        for affix in self.affixes:
            if affix.stat == "damage":
                damage += affix.value
            elif affix.stat == "damage_percent":
                damage *= (1 + affix.value / 100)

        return damage

    def add_affix(self, affix):
        """Add affix to weapon"""
        self.affixes.append(affix)

class Armor(Item):
    """Armor piece with defense and affixes"""

    def __init__(self, name, slot, defense, rarity="Common"):
        super().__init__(name, "Armor", rarity)
        self.slot = slot  # head, chest, legs, boots
        self.defense = defense
        self.affixes = []

    def add_affix(self, affix):
        """Add affix to armor"""
        self.affixes.append(affix)

class Accessory(Item):
    """Accessory with special effects"""

    def __init__(self, name, rarity="Common"):
        super().__init__(name, "Accessory", rarity)
        self.affixes = []

    def add_affix(self, affix):
        """Add affix"""
        self.affixes.append(affix)

class Affix:
    """Stat modifier or special effect"""

    def __init__(self, name, stat, value):
        self.name = name
        self.stat = stat
        self.value = value

    def __str__(self):
        if self.stat.endswith("_percent"):
            return f"+{self.value}% {self.stat.replace('_percent', '')}"
        else:
            return f"+{self.value} {self.stat}"

class LootGenerator:
    """Generates random loot"""

    def __init__(self):
        # Rarity chances (cumulative)
        self.rarity_weights = {
            "Common": 60,
            "Uncommon": 85,
            "Rare": 95,
            "Epic": 99,
            "Legendary": 100
        }

        # Affix pools
        self.offensive_affixes = [
            ("Crushing", "damage", 5),
            ("Sharp", "damage", 8),
            ("Mighty", "damage_percent", 15),
            ("Swift", "attack_speed", 0.1),
            ("Critical", "crit_chance", 5),
            ("Lethal", "crit_damage", 25)
        ]

        self.defensive_affixes = [
            ("Sturdy", "max_health", 20),
            ("Fortified", "defense", 10),
            ("Vital", "vitality", 5),
            ("Resilient", "damage_reduction", 5),
            ("Regenerating", "health_regen", 2)
        ]

        self.utility_affixes = [
            ("Swift", "movement_speed", 10),
            ("Focused", "cooldown_reduction", 10),
            ("Energetic", "ability_power", 15),
            ("Lucky", "magic_find", 20)
        ]

    def generate_rarity(self, luck_bonus=0):
        """Generate random rarity"""
        roll = random.randint(1, 100) + luck_bonus

        for rarity, threshold in self.rarity_weights.items():
            if roll <= threshold:
                return rarity

        return "Legendary"

    def generate_weapon(self, level=1, biome="Void"):
        """Generate random weapon"""
        rarity = self.generate_rarity()

        # Weapon types by biome theme
        weapon_types = {
            "Void": ["Void Blade", "Shadow Dagger", "Abyss Hammer"],
            "Solar": ["Solar Lance", "Radiant Sword", "Dawn Staff"],
            "Temporal": ["Chrono Blade", "Time Scepter", "Paradox Bow"],
            "Forest": ["Thorn Spear", "Verdant Bow", "Root Staff"]
        }

        weapon_names = weapon_types.get(biome, weapon_types["Void"])
        weapon_name = random.choice(weapon_names)

        base_damage = 10 + level * 3

        # Rarity multiplier
        rarity_mult = {
            "Common": 1.0,
            "Uncommon": 1.2,
            "Rare": 1.5,
            "Epic": 1.8,
            "Legendary": 2.5
        }

        base_damage = int(base_damage * rarity_mult[rarity])

        weapon = Weapon(weapon_name, "Sword", base_damage, rarity)

        # Add affixes based on rarity
        affix_count = {
            "Common": 0,
            "Uncommon": 1,
            "Rare": 2,
            "Epic": 3,
            "Legendary": 4
        }

        for _ in range(affix_count[rarity]):
            affix_data = random.choice(self.offensive_affixes)
            affix = Affix(affix_data[0], affix_data[1], affix_data[2])
            weapon.add_affix(affix)

        return weapon

    def generate_armor(self, level=1, slot="chest"):
        """Generate random armor"""
        rarity = self.generate_rarity()

        armor_names = {
            "head": ["Helmet", "Crown", "Hood"],
            "chest": ["Chestplate", "Robe", "Cuirass"],
            "legs": ["Greaves", "Leggings", "Pants"],
            "boots": ["Boots", "Sabatons", "Treads"]
        }

        armor_name = random.choice(armor_names.get(slot, ["Armor"]))

        base_defense = 5 + level * 2

        rarity_mult = {
            "Common": 1.0,
            "Uncommon": 1.2,
            "Rare": 1.5,
            "Epic": 1.8,
            "Legendary": 2.5
        }

        base_defense = int(base_defense * rarity_mult[rarity])

        armor = Armor(armor_name, slot, base_defense, rarity)

        # Add affixes
        affix_count = {
            "Common": 0,
            "Uncommon": 1,
            "Rare": 2,
            "Epic": 3,
            "Legendary": 4
        }

        for _ in range(affix_count[rarity]):
            affix_data = random.choice(self.defensive_affixes)
            affix = Affix(affix_data[0], affix_data[1], affix_data[2])
            armor.add_affix(affix)

        return armor

    def generate_accessory(self, level=1):
        """Generate random accessory"""
        rarity = self.generate_rarity()

        accessory_types = ["Ring", "Amulet", "Charm", "Talisman"]
        accessory_name = random.choice(accessory_types)

        accessory = Accessory(accessory_name, rarity)

        # Accessories get mixed affixes
        affix_count = {
            "Common": 1,
            "Uncommon": 2,
            "Rare": 3,
            "Epic": 4,
            "Legendary": 5
        }

        all_affixes = self.offensive_affixes + self.defensive_affixes + self.utility_affixes

        for _ in range(affix_count[rarity]):
            affix_data = random.choice(all_affixes)
            affix = Affix(affix_data[0], affix_data[1], affix_data[2])
            accessory.add_affix(affix)

        return accessory

    def generate_loot_drop(self, level=1, biome="Void"):
        """Generate random loot drop"""
        roll = random.random()

        if roll < 0.5:
            # Weapon
            return self.generate_weapon(level, biome)
        elif roll < 0.8:
            # Armor
            slot = random.choice(["head", "chest", "legs", "boots"])
            return self.generate_armor(level, slot)
        else:
            # Accessory
            return self.generate_accessory(level)

class Inventory:
    """Player inventory system"""

    def __init__(self, max_size=30):
        self.items = []
        self.max_size = max_size

    def add_item(self, item):
        """Add item to inventory"""
        if len(self.items) < self.max_size:
            self.items.append(item)
            return True
        return False

    def remove_item(self, item):
        """Remove item"""
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def get_items_by_type(self, item_type):
        """Get all items of a type"""
        return [item for item in self.items if item.item_type == item_type]

    def is_full(self):
        """Check if inventory is full"""
        return len(self.items) >= self.max_size
