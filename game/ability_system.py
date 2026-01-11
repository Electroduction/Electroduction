"""
AAA Ability System - Fixed Q/E abilities with proper cooldowns, targeting, effects
Inspired by Hades boon system and Wizard of Legend spells
"""

import pygame
import math
import random
from combat_system import Projectile

class Ability:
    """Base ability class"""

    def __init__(self, name, description, cooldown, cost=0):
        self.name = name
        self.description = description
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.cost = cost  # Mana/energy cost if needed

        self.icon_color = (150, 200, 255)
        self.key_binding = None

    def can_use(self):
        """Check if ability can be used"""
        return self.current_cooldown <= 0

    def use(self, player, target_x=None, target_y=None):
        """Use ability - override in subclasses"""
        if not self.can_use():
            return False

        self.current_cooldown = self.cooldown
        return True

    def update(self, dt):
        """Update cooldown"""
        if self.current_cooldown > 0:
            self.current_cooldown -= dt

    def get_tooltip_text(self):
        """Get tooltip information"""
        return [
            self.description,
            f"Cooldown: {self.cooldown}s"
        ]

# === OFFENSIVE ABILITIES ===

class VoidSlash(Ability):
    """Dash forward with a damaging slash"""

    def __init__(self):
        super().__init__(
            "Void Slash",
            "Dash forward, slashing enemies in your path for 40 damage",
            4.0
        )
        self.icon_color = (120, 80, 180)
        self.dash_distance = 150
        self.damage = 40

    def use(self, player, target_x=None, target_y=None):
        if not super().use(player, target_x, target_y):
            return False

        # Dash forward
        dash_x = player.x + math.cos(player.facing_angle) * self.dash_distance
        dash_y = player.y + math.sin(player.facing_angle) * self.dash_distance

        # Create hitbox along path
        if hasattr(player, 'combat_system') and player.combat_system:
            player.combat_system.create_hitbox(
                dash_x, dash_y,
                radius=60,
                damage=self.damage,
                owner='player',
                duration=0.2,
                knockback=50
            )

        # Move player
        player.x = dash_x
        player.y = dash_y

        # Visual effects
        player.particles.add_slash_effect(
            player.x, player.y,
            player.facing_angle,
            self.icon_color
        )

        # Make player briefly invulnerable
        player.invulnerable = True
        player.invuln_duration = 0.2

        # Sound
        from audio_system import get_audio_system
        get_audio_system().play_ability_sound()

        return True

class SolarBeam(Ability):
    """Fire a piercing solar beam"""

    def __init__(self):
        super().__init__(
            "Solar Beam",
            "Fire a piercing beam of solar energy for 50 damage",
            6.0
        )
        self.icon_color = (255, 200, 80)
        self.damage = 50
        self.range = 400

    def use(self, player, target_x=None, target_y=None):
        if not super().use(player, target_x, target_y):
            return False

        # Create projectile
        vx = math.cos(player.facing_angle) * 600
        vy = math.sin(player.facing_angle) * 600

        projectile = Projectile(
            player.x, player.y,
            vx, vy,
            self.damage,
            owner='player',
            size=12,
            color=self.icon_color,
            lifetime=1.0,
            piercing=True
        )

        # Add to projectile list
        if hasattr(player, 'projectiles'):
            player.projectiles.append(projectile)

        # Visual
        end_x = player.x + math.cos(player.facing_angle) * self.range
        end_y = player.y + math.sin(player.facing_angle) * self.range

        player.particles.add_beam(
            player.x, player.y,
            end_x, end_y,
            self.icon_color
        )

        # Sound
        from audio_system import get_audio_system
        get_audio_system().play_ability_sound()

        return True

class VoidBurst(Ability):
    """AoE explosion around player"""

    def __init__(self):
        super().__init__(
            "Void Burst",
            "Release void energy in all directions for 35 damage",
            8.0
        )
        self.icon_color = (120, 80, 180)
        self.damage = 35
        self.radius = 120

    def use(self, player, target_x=None, target_y=None):
        if not super().use(player, target_x, target_y):
            return False

        # Create AoE hitbox
        if hasattr(player, 'combat_system') and player.combat_system:
            player.combat_system.create_hitbox(
                player.x, player.y,
                radius=self.radius,
                damage=self.damage,
                owner='player',
                duration=0.3,
                knockback=80
            )

        # Visual
        player.particles.add_explosion(player.x, player.y, self.radius, self.icon_color)

        # Screen shake
        if hasattr(player, 'screen_effects'):
            player.screen_effects.add_shake(8, 0.3)

        # Sound
        from audio_system import get_audio_system
        get_audio_system().play_ability_sound()

        return True

class TimeSlow(Ability):
    """Slow time in an area"""

    def __init__(self):
        super().__init__(
            "Time Distortion",
            "Slow enemies in a large area for 4 seconds",
            12.0
        )
        self.icon_color = (100, 180, 255)
        self.duration = 4.0
        self.radius = 200

    def use(self, player, target_x=None, target_y=None):
        if not super().use(player, target_x, target_y):
            return False

        # Apply slow to nearby enemies (handled by game manager)
        if hasattr(player, 'time_slow_active'):
            player.time_slow_active = True
            player.time_slow_duration = self.duration
            player.time_slow_radius = self.radius

        # Visual
        player.particles.add_time_warp(player.x, player.y, self.radius)

        # Sound
        from audio_system import get_audio_system
        get_audio_system().play_ability_sound()

        return True

# === UTILITY/SUPPORT ABILITIES ===

class RadiantHeal(Ability):
    """Heal self"""

    def __init__(self):
        super().__init__(
            "Radiant Heal",
            "Restore 40 health instantly",
            10.0
        )
        self.icon_color = (150, 255, 150)
        self.heal_amount = 40

    def use(self, player, target_x=None, target_y=None):
        if not super().use(player, target_x, target_y):
            return False

        # Heal player
        player.heal(self.heal_amount)

        # Visual
        player.particles.add_heal_effect(player.x, player.y)

        # Sound
        from audio_system import get_audio_system
        get_audio_system().play_pickup_sound()

        return True

class PhantomClone(Ability):
    """Create a clone that mimics your attacks"""

    def __init__(self):
        super().__init__(
            "Phantom Clone",
            "Summon a clone that fights alongside you for 8 seconds",
            15.0
        )
        self.icon_color = (150, 150, 255)
        self.duration = 8.0

    def use(self, player, target_x=None, target_y=None):
        if not super().use(player, target_x, target_y):
            return False

        # Activate clone (handled by game manager)
        if hasattr(player, 'clone_active'):
            player.clone_active = True
            player.clone_duration = self.duration

        # Visual
        player.particles.add_clone_effect(player.x, player.y)

        # Sound
        from audio_system import get_audio_system
        get_audio_system().play_ability_sound()

        return True

class AbilityManager:
    """Manages player abilities"""

    def __init__(self):
        # Available abilities
        self.ability_library = {
            'void_slash': VoidSlash(),
            'solar_beam': SolarBeam(),
            'void_burst': VoidBurst(),
            'time_slow': TimeSlow(),
            'radiant_heal': RadiantHeal(),
            'phantom_clone': PhantomClone()
        }

        # Player loadout (4 slots)
        self.equipped_abilities = [None, None, None, None]

        # Key bindings
        self.key_bindings = [pygame.K_q, pygame.K_e, pygame.K_r, pygame.K_f]

    def equip_ability(self, ability_name, slot):
        """Equip ability to slot (0-3)"""
        if ability_name in self.ability_library and 0 <= slot < 4:
            self.equipped_abilities[slot] = self.ability_library[ability_name]
            self.equipped_abilities[slot].key_binding = self.key_bindings[slot]
            return True
        return False

    def use_ability(self, slot, player, target_x=None, target_y=None):
        """Use ability in slot"""
        if 0 <= slot < 4 and self.equipped_abilities[slot]:
            ability = self.equipped_abilities[slot]
            return ability.use(player, target_x, target_y)
        return False

    def update(self, dt):
        """Update all abilities"""
        for ability in self.equipped_abilities:
            if ability:
                ability.update(dt)

    def get_ability(self, slot):
        """Get ability in slot"""
        if 0 <= slot < 4:
            return self.equipped_abilities[slot]
        return None

    def get_default_loadout(self):
        """Get starting abilities"""
        self.equip_ability('void_slash', 0)
        self.equip_ability('void_burst', 1)
        self.equip_ability('radiant_heal', 2)
        self.equip_ability('solar_beam', 3)
