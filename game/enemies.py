"""
Enemy system - AI, behaviors, and enemy types
"""

import pygame
import math
import random
from particles import ParticleSystem

class Enemy:
    """Base enemy class"""

    def __init__(self, x, y, enemy_type="Basic"):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24

        self.enemy_type = enemy_type
        self.max_health = 50
        self.health = self.max_health
        self.damage = 10
        self.speed = 80
        self.xp_value = 25

        self.vx = 0
        self.vy = 0

        # AI state
        self.state = "idle"  # idle, chase, attack, flee
        self.target = None
        self.aggro_range = 300
        self.attack_range = 40
        self.attack_cooldown = 0
        self.attack_speed = 1.5

        # Visual
        self.color = (180, 80, 80)
        self.hurt_flash = 0

        # Particles
        self.particles = ParticleSystem()

        self.alive = True

    def update(self, dt, player):
        """Update enemy AI and state"""
        if not self.alive:
            return

        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.hurt_flash > 0:
            self.hurt_flash -= dt

        # AI behavior
        dist_to_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)

        if dist_to_player < self.aggro_range:
            self.target = player
            self.state = "chase"

            if dist_to_player < self.attack_range:
                self.state = "attack"
                if self.attack_cooldown <= 0:
                    self.attack(player)
            else:
                # Move towards player
                dx = player.x - self.x
                dy = player.y - self.y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > 0:
                    self.vx = (dx / distance) * self.speed
                    self.vy = (dy / distance) * self.speed
        else:
            self.state = "idle"
            self.vx = 0
            self.vy = 0

        # Apply movement
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Update particles
        self.particles.update(dt)

    def attack(self, player):
        """Attack the player"""
        self.attack_cooldown = self.attack_speed
        player.take_damage(self.damage)

        # Visual feedback
        self.particles.add_attack_effect(self.x, self.y, player.x, player.y, self.color)

    def take_damage(self, amount, source=None):
        """Take damage"""
        self.health -= amount
        self.hurt_flash = 0.2

        # Knockback
        if source:
            dx = self.x - source.x
            dy = self.y - source.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                self.x += (dx / dist) * 20
                self.y += (dy / dist) * 20

        # Damage numbers
        self.particles.add_damage_numbers(self.x, self.y - 20, int(amount), (255, 200, 100))

        if self.health <= 0:
            self.die()

    def die(self):
        """Handle death"""
        self.alive = False
        self.particles.add_death_effect(self.x, self.y, self.color)

    def render(self, screen, camera):
        """Render enemy"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Flash effect when hurt
        if self.hurt_flash > 0:
            color = (255, 150, 150)
        else:
            color = self.color

        # Draw enemy
        pygame.draw.rect(
            screen,
            color,
            (int(screen_x - self.width // 2), int(screen_y - self.height // 2),
             self.width, self.height)
        )

        # Health bar
        self.render_health_bar(screen, screen_x, screen_y - 20)

        # Particles
        self.particles.render(screen, camera)

    def render_health_bar(self, screen, x, y):
        """Render health bar"""
        bar_width = 30
        bar_height = 3
        health_ratio = self.health / self.max_health

        # Background
        pygame.draw.rect(screen, (40, 40, 40), (x - bar_width // 2, y, bar_width, bar_height))

        # Health
        health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (200, 50, 50), (x - bar_width // 2, y, health_width, bar_height))

class LanternCrawler(Enemy):
    """Void enemy with disorienting pulses"""

    def __init__(self, x, y):
        super().__init__(x, y, "Lantern Crawler")
        self.max_health = 40
        self.health = self.max_health
        self.speed = 100
        self.damage = 8
        self.color = (100, 80, 140)
        self.xp_value = 30

        # Special ability
        self.pulse_cooldown = 0
        self.pulse_timer = 3.0

    def update(self, dt, player):
        super().update(dt, player)

        # Pulse ability
        self.pulse_cooldown -= dt
        if self.pulse_cooldown <= 0:
            self.pulse_cooldown = self.pulse_timer
            self.emit_pulse(player)

    def emit_pulse(self, player):
        """Emit disorienting pulse"""
        self.particles.add_pulse(self.x, self.y, 80, (120, 100, 180))

        # Check if player in range
        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        if dist < 80:
            # Disorient effect (would slow player or invert controls briefly)
            pass

class EchoLeech(Enemy):
    """Drains fragment energy"""

    def __init__(self, x, y):
        super().__init__(x, y, "Echo Leech")
        self.max_health = 30
        self.health = self.max_health
        self.speed = 60
        self.damage = 5
        self.color = (140, 60, 120)
        self.xp_value = 35

    def attack(self, player):
        """Drain attack"""
        super().attack(player)

        # Drain effect - increase cooldowns
        for i in range(len(player.ability_cooldowns)):
            player.ability_cooldowns[i] += 1.0

        self.particles.add_drain_effect(player.x, player.y, self.x, self.y)

class PhaseBlade(Enemy):
    """Teleporting melee attacker"""

    def __init__(self, x, y):
        super().__init__(x, y, "Phase Blade")
        self.max_health = 45
        self.health = self.max_health
        self.speed = 120
        self.damage = 15
        self.color = (100, 100, 180)
        self.xp_value = 40

        self.teleport_cooldown = 0
        self.teleport_timer = 5.0

    def update(self, dt, player):
        super().update(dt, player)

        # Teleport ability
        self.teleport_cooldown -= dt
        if self.teleport_cooldown <= 0 and self.state == "chase":
            dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
            if dist > 100 and dist < self.aggro_range:
                self.teleport_to_player(player)

    def teleport_to_player(self, player):
        """Teleport near player"""
        self.teleport_cooldown = self.teleport_timer

        # Teleport to random position near player
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(50, 100)

        self.particles.add_teleport_effect(self.x, self.y, self.color)

        self.x = player.x + math.cos(angle) * distance
        self.y = player.y + math.sin(angle) * distance

        self.particles.add_teleport_effect(self.x, self.y, self.color)

class Thornstalker(Enemy):
    """Forest ambusher"""

    def __init__(self, x, y):
        super().__init__(x, y, "Thornstalker")
        self.max_health = 55
        self.health = self.max_health
        self.speed = 90
        self.damage = 12
        self.color = (80, 120, 60)
        self.xp_value = 35

        # Ambush mechanic
        self.burrowed = True
        self.burrow_timer = 2.0

    def update(self, dt, player):
        if self.burrowed:
            self.burrow_timer -= dt
            if self.burrow_timer <= 0:
                dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
                if dist < 150:
                    self.emerge()
        else:
            super().update(dt, player)

    def emerge(self):
        """Emerge from ground"""
        self.burrowed = False
        self.particles.add_emergence_effect(self.x, self.y, (60, 100, 40))

    def render(self, screen, camera):
        if self.burrowed:
            # Draw subtle indicator
            screen_x, screen_y = camera.world_to_screen(self.x, self.y)
            pygame.draw.circle(screen, (40, 60, 30), (int(screen_x), int(screen_y)), 8)
        else:
            super().render(screen, camera)

class TimeShards(Enemy):
    """Crystal time anomaly"""

    def __init__(self, x, y):
        super().__init__(x, y, "Time Shard")
        self.max_health = 35
        self.health = self.max_health
        self.speed = 70
        self.damage = 8
        self.color = (120, 180, 220)
        self.xp_value = 45

        # Time manipulation
        self.slow_field_active = False

    def update(self, dt, player):
        super().update(dt, player)

        # Create slow field
        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        if dist < 100:
            self.slow_field_active = True
            # Slow player (would modify player.speed)
        else:
            self.slow_field_active = False

    def render(self, screen, camera):
        super().render(screen, camera)

        # Render slow field
        if self.slow_field_active:
            screen_x, screen_y = camera.world_to_screen(self.x, self.y)
            pygame.draw.circle(screen, (100, 150, 200), (int(screen_x), int(screen_y)), 100, 2)

def create_enemy(enemy_type, x, y):
    """Factory function for creating enemies"""
    enemy_types = {
        "Lantern Crawler": LanternCrawler,
        "Echo Leech": EchoLeech,
        "Phase Blade": PhaseBlade,
        "Thornstalker": Thornstalker,
        "Time Shard": TimeShards,
        "Basic": Enemy
    }

    enemy_class = enemy_types.get(enemy_type, Enemy)
    return enemy_class(x, y)
