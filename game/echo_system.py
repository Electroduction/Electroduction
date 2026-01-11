"""
Echo Fragment System - Core progression and build customization
"""

import random
import math

class EchoFragment:
    """Base class for Echo Fragments"""

    def __init__(self, name, fragment_type, rarity="Common"):
        self.name = name
        self.fragment_type = fragment_type  # Void, Solar, Temporal, Aether, Blood
        self.rarity = rarity
        self.level = 1
        self.mastery_xp = 0

    def get_color(self):
        """Get color based on fragment type"""
        colors = {
            "Void": (120, 80, 180),
            "Solar": (255, 200, 80),
            "Temporal": (100, 200, 255),
            "Aether": (150, 255, 150),
            "Blood": (200, 50, 50),
            "Neutral": (180, 180, 180)
        }
        return colors.get(self.fragment_type, (150, 150, 150))

class ActiveFragment(EchoFragment):
    """Active ability fragment"""

    def __init__(self, name, fragment_type, cooldown, effect_func):
        super().__init__(name, fragment_type, "Active")
        self.cooldown = cooldown
        self.effect_func = effect_func
        self.current_cooldown = 0

    def activate(self, player):
        """Activate the ability"""
        if self.current_cooldown <= 0:
            self.effect_func(player, self)
            self.current_cooldown = self.cooldown
            return True
        return False

class PassiveFragment(EchoFragment):
    """Passive stat/behavior modifier"""

    def __init__(self, name, fragment_type, stat_bonuses):
        super().__init__(name, fragment_type, "Passive")
        self.stat_bonuses = stat_bonuses  # Dict of stat: value

    def apply_to_player(self, player):
        """Apply passive bonuses"""
        for stat, bonus in self.stat_bonuses.items():
            if stat == "max_health":
                player.max_health += bonus
            elif stat == "power":
                player.power += bonus
            elif stat == "vitality":
                player.vitality += bonus
            elif stat == "speed":
                player.speed += bonus

class CoreFragment(EchoFragment):
    """Core identity fragment (defines class archetype)"""

    def __init__(self, name, fragment_type, description, bonuses):
        super().__init__(name, fragment_type, "Core")
        self.description = description
        self.bonuses = bonuses

class EchoLibrary:
    """Library of all available Echo Fragments"""

    def __init__(self):
        self.fragments = self._create_fragment_library()

    def _create_fragment_library(self):
        """Create all available fragments"""
        library = {}

        # CORE FRAGMENTS (Class Archetypes)
        library['Shadowblade Core'] = CoreFragment(
            "Shadowblade Core",
            "Void",
            "Master of swift strikes and void manipulation",
            {
                'attack_speed': 0.2,
                'dodge_cooldown': -0.3,
                'crit_chance': 0.15
            }
        )

        library['Solar Mystic Core'] = CoreFragment(
            "Solar Mystic Core",
            "Solar",
            "Channeler of radiant energy and healing light",
            {
                'ability_power': 0.3,
                'health_regen': 5,
                'solar_damage': 0.25
            }
        )

        library['Chrono Warrior Core'] = CoreFragment(
            "Chrono Warrior Core",
            "Temporal",
            "Manipulator of time and space",
            {
                'cooldown_reduction': 0.2,
                'dodge_charges': 1,
                'temporal_power': 0.2
            }
        )

        # ACTIVE ABILITIES

        # Void abilities
        def phantom_step(player, fragment):
            """Teleport forward"""
            distance = 150
            player.x += math.cos(player.facing_angle) * distance
            player.y += math.sin(player.facing_angle) * distance
            player.particles.add_teleport_effect(player.x, player.y, (120, 80, 180))
            player.invulnerable = True
            # Set brief invuln (would need timer system)

        library['Phantom Step'] = ActiveFragment(
            "Phantom Step",
            "Void",
            5.0,
            phantom_step
        )

        def void_surge(player, fragment):
            """Release void energy in area"""
            player.particles.add_explosion(player.x, player.y, 100, (120, 80, 180))
            # Damage nearby enemies (handled in combat system)
            player.last_ability_damage = 40
            player.last_ability_range = 100

        library['Void Surge'] = ActiveFragment(
            "Void Surge",
            "Void",
            8.0,
            void_surge
        )

        # Solar abilities
        def solar_lance(player, fragment):
            """Fire a piercing solar beam"""
            beam_length = 300
            end_x = player.x + math.cos(player.facing_angle) * beam_length
            end_y = player.y + math.sin(player.facing_angle) * beam_length

            player.particles.add_beam(
                player.x, player.y,
                end_x, end_y,
                (255, 200, 80)
            )

            player.last_ability_damage = 35
            player.last_ability_range = beam_length

        library['Solar Lance'] = ActiveFragment(
            "Solar Lance",
            "Solar",
            6.0,
            solar_lance
        )

        def radiant_heal(player, fragment):
            """Heal self and nearby allies"""
            heal_amount = 30 + player.focus * 2
            player.heal(heal_amount)
            player.particles.add_heal_effect(player.x, player.y)

        library['Radiant Heal'] = ActiveFragment(
            "Radiant Heal",
            "Solar",
            10.0,
            radiant_heal
        )

        # Temporal abilities
        def time_slow(player, fragment):
            """Slow time in area"""
            player.particles.add_time_warp(player.x, player.y, 150)
            # Set time dilation field (would affect enemies in range)
            player.time_field_active = True
            player.time_field_duration = 3.0

        library['Time Slow'] = ActiveFragment(
            "Time Slow",
            "Temporal",
            12.0,
            time_slow
        )

        def temporal_echo(player, fragment):
            """Create echo of yourself"""
            # Would create AI companion that mimics player attacks
            player.particles.add_clone_effect(player.x, player.y)
            player.echo_clone_active = True
            player.echo_clone_duration = 5.0

        library['Temporal Echo'] = ActiveFragment(
            "Temporal Echo",
            "Temporal",
            15.0,
            temporal_echo
        )

        # PASSIVE FRAGMENTS

        library['Lifesteal Shard'] = PassiveFragment(
            "Lifesteal Shard",
            "Blood",
            {'lifesteal': 0.15}
        )

        library['Void Armor'] = PassiveFragment(
            "Void Armor",
            "Void",
            {'vitality': 5, 'dodge_cooldown': -0.2}
        )

        library['Solar Blessing'] = PassiveFragment(
            "Solar Blessing",
            "Solar",
            {'max_health': 20, 'health_regen': 2}
        )

        library['Swift Steps'] = PassiveFragment(
            "Swift Steps",
            "Aether",
            {'speed': 50, 'celerity': 5}
        )

        library['Critical Mind'] = PassiveFragment(
            "Critical Mind",
            "Neutral",
            {'crit_chance': 0.1, 'crit_damage': 0.5}
        )

        library['Power Surge'] = PassiveFragment(
            "Power Surge",
            "Neutral",
            {'power': 8, 'attack_speed': 0.1}
        )

        return library

    def get_fragment(self, name):
        """Get fragment by name"""
        return self.fragments.get(name)

    def get_random_fragment(self, fragment_type=None):
        """Get random fragment, optionally filtered by type"""
        eligible = list(self.fragments.values())

        if fragment_type:
            eligible = [f for f in eligible if f.fragment_type == fragment_type]

        if eligible:
            return random.choice(eligible)
        return None

    def get_fragments_by_type(self, fragment_type):
        """Get all fragments of a type"""
        return [f for f in self.fragments.values() if f.fragment_type == fragment_type]

    def get_starting_loadout(self, archetype="Balanced"):
        """Get starting fragment loadout"""
        loadouts = {
            "Balanced": {
                'core': 'Shadowblade Core',
                'abilities': ['Void Surge', 'Radiant Heal'],
                'passives': ['Swift Steps', 'Power Surge']
            },
            "Solar Mystic": {
                'core': 'Solar Mystic Core',
                'abilities': ['Solar Lance', 'Radiant Heal'],
                'passives': ['Solar Blessing', 'Critical Mind']
            },
            "Chrono Warrior": {
                'core': 'Chrono Warrior Core',
                'abilities': ['Time Slow', 'Phantom Step'],
                'passives': ['Swift Steps', 'Void Armor']
            }
        }

        loadout_names = loadouts.get(archetype, loadouts["Balanced"])
        loadout = {
            'core': self.get_fragment(loadout_names['core']),
            'abilities': [self.get_fragment(name) for name in loadout_names['abilities']],
            'passives': [self.get_fragment(name) for name in loadout_names['passives']]
        }

        return loadout

class EchoForge:
    """System for upgrading and combining fragments"""

    def __init__(self):
        self.upgrade_costs = {
            1: 100,
            2: 250,
            3: 500,
            4: 1000,
            5: 2000
        }

    def can_upgrade(self, fragment, player_shards):
        """Check if fragment can be upgraded"""
        cost = self.upgrade_costs.get(fragment.level, 9999)
        return player_shards >= cost

    def upgrade_fragment(self, fragment):
        """Upgrade fragment level"""
        fragment.level += 1

        # Enhance fragment effects
        if isinstance(fragment, ActiveFragment):
            fragment.cooldown *= 0.9  # Reduce cooldown
        elif isinstance(fragment, PassiveFragment):
            # Increase stat bonuses
            for stat in fragment.stat_bonuses:
                fragment.stat_bonuses[stat] *= 1.2

        return True

    def combine_fragments(self, fragment1, fragment2):
        """Combine two fragments (fusion system)"""
        # Creates hybrid fragment (complex system for later)
        pass
