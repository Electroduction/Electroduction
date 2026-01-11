"""
Player Character - Movement, combat, abilities, progression
"""

import pygame
import math
from echo_system import EchoFragment
from items import Weapon, Armor
from particles import ParticleSystem

class Player:
    def __init__(self, x, y, game_state):
        # Position
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32

        # Movement
        self.speed = 250
        self.vx = 0
        self.vy = 0

        # Combat stats
        self.max_health = 100
        self.health = self.max_health
        self.power = 10
        self.vitality = 10
        self.focus = 10
        self.celerity = 10

        # Combat state
        self.attack_cooldown = 0
        self.attack_speed = 0.4  # Seconds between attacks
        self.attack_range = 60
        self.attack_damage = 15

        # Dodge/roll
        self.dodge_cooldown = 0
        self.dodge_duration = 0.3
        self.dodge_speed = 400
        self.is_dodging = False
        self.dodge_timer = 0
        self.invulnerable = False

        # Abilities
        self.ability_cooldowns = [0, 0, 0, 0]
        self.ability_keys = [pygame.K_q, pygame.K_e, pygame.K_r, pygame.K_f]

        # Echo system
        self.equipped_core_fragment = None
        self.equipped_abilities = []
        self.equipped_passives = []

        # Equip starting loadout
        self._equip_starting_loadout()

        # Gear
        self.weapon = None
        self.armor_pieces = {'head': None, 'chest': None, 'legs': None, 'boots': None}
        self.accessories = []

        # Progression
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100
        self.stat_points = 0
        self.game_state = game_state

        # Visual
        self.color = (100, 150, 255)
        self.facing_angle = 0
        self.particles = ParticleSystem()

        # Animation
        self.hurt_flash = 0

    def update(self, dt, enemies, obstacles):
        """Update player state"""
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= dt

        for i in range(len(self.ability_cooldowns)):
            if self.ability_cooldowns[i] > 0:
                self.ability_cooldowns[i] -= dt

        # Update dodge state
        if self.is_dodging:
            self.dodge_timer -= dt
            if self.dodge_timer <= 0:
                self.is_dodging = False
                self.invulnerable = False

        # Handle input
        if not self.is_dodging:
            self.handle_input(dt)

        # Movement
        self.move(dt, obstacles)

        # Update particles
        self.particles.update(dt)

        # Hurt flash
        if self.hurt_flash > 0:
            self.hurt_flash -= dt

        # Regeneration (passive)
        if self.health < self.max_health:
            self.health += self.vitality * 0.1 * dt
            self.health = min(self.health, self.max_health)

    def handle_input(self, dt):
        """Handle player input"""
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        # Movement
        dx = 0
        dy = 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.vx = dx * self.speed
        self.vy = dy * self.speed

        # Face towards mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # This will be adjusted by camera in render
        self.facing_angle = math.atan2(mouse_y - 360, mouse_x - 640)

        # Attack
        if mouse_buttons[0] and self.attack_cooldown <= 0:
            self.attack()

        # Dodge
        if keys[pygame.K_SPACE] and self.dodge_cooldown <= 0:
            self.dodge()

        # Abilities
        for i, key in enumerate(self.ability_keys):
            if keys[key] and self.ability_cooldowns[i] <= 0:
                self.use_ability(i)

    def move(self, dt, obstacles):
        """Move player with collision"""
        # Apply dodge boost
        if self.is_dodging:
            move_multiplier = self.dodge_speed / self.speed
        else:
            move_multiplier = 1.0

        new_x = self.x + self.vx * dt * move_multiplier
        new_y = self.y + self.vy * dt * move_multiplier

        # Simple bounds checking (will be expanded for dungeon collision)
        # For now, just keep within reasonable bounds
        self.x = new_x
        self.y = new_y

    def attack(self):
        """Perform basic attack"""
        self.attack_cooldown = self.attack_speed

        # Calculate attack position
        attack_x = self.x + math.cos(self.facing_angle) * self.attack_range
        attack_y = self.y + math.sin(self.facing_angle) * self.attack_range

        # Create attack hitbox (will be used for enemy collision)
        self.last_attack_pos = (attack_x, attack_y)
        self.last_attack_time = 0.1  # Visual indicator duration

        # Visual feedback
        self.particles.add_slash_effect(
            self.x, self.y,
            self.facing_angle,
            self.color
        )

    def dodge(self):
        """Perform dodge/roll"""
        self.dodge_cooldown = 1.0  # 1 second cooldown
        self.is_dodging = True
        self.dodge_timer = self.dodge_duration
        self.invulnerable = True

        # Dodge in movement direction or forward if not moving
        if self.vx == 0 and self.vy == 0:
            self.vx = math.cos(self.facing_angle) * self.speed
            self.vy = math.sin(self.facing_angle) * self.speed

        # Particles
        self.particles.add_dodge_trail(self.x, self.y, self.color)

    def use_ability(self, ability_index):
        """Use equipped ability"""
        if ability_index < len(self.equipped_abilities):
            ability = self.equipped_abilities[ability_index]
            if ability:
                ability.activate(self)
                self.ability_cooldowns[ability_index] = ability.cooldown

    def take_damage(self, amount):
        """Take damage with invulnerability check"""
        if self.invulnerable:
            return

        # Apply damage reduction from vitality
        reduction = min(self.vitality * 0.5, 50)  # Max 50% reduction
        actual_damage = amount * (1 - reduction / 100)

        self.health -= actual_damage
        self.hurt_flash = 0.2

        # Visual feedback
        self.particles.add_damage_numbers(self.x, self.y - 20, int(actual_damage), (255, 50, 50))

        if self.health <= 0:
            self.health = 0
            self.on_death()

    def heal(self, amount):
        """Heal player"""
        old_health = self.health
        self.health = min(self.health + amount, self.max_health)
        healed = self.health - old_health

        if healed > 0:
            self.particles.add_damage_numbers(self.x, self.y - 20, int(healed), (50, 255, 100))

    def add_xp(self, amount):
        """Add experience and handle level ups"""
        self.xp += amount

        while self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        """Level up and grant rewards"""
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.3)

        # Stat increases
        self.max_health += 10
        self.health = self.max_health
        self.stat_points += 3

        # Visual feedback
        print(f"Level up! Now level {self.level}")
        self.particles.add_level_up_effect(self.x, self.y)

    def equip_fragment(self, fragment, slot='core'):
        """Equip an Echo Fragment"""
        if slot == 'core':
            self.equipped_core_fragment = fragment
            self.apply_core_fragment_effects()
        elif slot == 'ability':
            self.equipped_abilities.append(fragment)
        elif slot == 'passive':
            self.equipped_passives.append(fragment)
            self.apply_passive_effects()

    def apply_core_fragment_effects(self):
        """Apply core fragment stat bonuses"""
        if self.equipped_core_fragment:
            # Example: Different cores grant different bonuses
            pass

    def apply_passive_effects(self):
        """Apply passive fragment effects"""
        # Recalculate all passive bonuses
        pass

    def _equip_starting_loadout(self):
        """Equip starting Echo Fragment loadout"""
        from echo_system import EchoLibrary

        library = EchoLibrary()

        # Get balanced starting loadout
        loadout = library.get_starting_loadout("Balanced")

        # Equip core fragment
        if loadout['core']:
            self.equipped_core_fragment = loadout['core']

        # Equip abilities
        for ability in loadout['abilities']:
            if ability:
                self.equipped_abilities.append(ability)

        # Equip passives
        for passive in loadout['passives']:
            if passive:
                self.equipped_passives.append(passive)

        print("Starting loadout equipped: Shadowblade Core with Void Surge and Radiant Heal")

    def start_dungeon_run(self, start_x, start_y):
        """Prepare for dungeon run"""
        self.x = start_x
        self.y = start_y
        self.health = self.max_health
        self.game_state.start_new_run()

    def return_to_hub(self, hub_x, hub_y):
        """Return to hub"""
        self.x = hub_x
        self.y = hub_y
        self.health = self.max_health

    def on_death(self):
        """Handle death"""
        print(f"Player died at level {self.level}")

    def render(self, screen, camera):
        """Render player"""
        # Screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Hurt flash
        if self.hurt_flash > 0:
            color = (255, 100, 100)
        elif self.is_dodging:
            color = (150, 200, 255)
        else:
            color = self.color

        # Draw player circle
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.width // 2)

        # Draw directional indicator
        end_x = screen_x + math.cos(self.facing_angle) * 20
        end_y = screen_y + math.sin(self.facing_angle) * 20
        pygame.draw.line(screen, (255, 255, 255), (screen_x, screen_y), (end_x, end_y), 3)

        # Render particles
        self.particles.render(screen, camera)

        # Health bar above player
        self.render_health_bar(screen, screen_x, screen_y - 30)

    def render_health_bar(self, screen, x, y):
        """Render health bar"""
        bar_width = 40
        bar_height = 4
        health_ratio = self.health / self.max_health

        # Background
        pygame.draw.rect(screen, (60, 60, 60), (x - bar_width // 2, y, bar_width, bar_height))

        # Health
        health_width = int(bar_width * health_ratio)
        health_color = (50, 200, 50) if health_ratio > 0.5 else (200, 200, 50) if health_ratio > 0.25 else (200, 50, 50)
        pygame.draw.rect(screen, health_color, (x - bar_width // 2, y, health_width, bar_height))
