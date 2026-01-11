"""
Enhanced Enemy System - Varied enemies with unique abilities, projectiles, status effects
"""

import pygame
import math
import random
from particles import ParticleSystem
from combat_system import StatusEffectManager

class Enemy:
    """Base enemy class with proper damage handling"""

    def __init__(self, x, y, enemy_type="Basic", combat_system=None):
        self.x = x
        self.y = y
        self.width = 28
        self.height = 28

        self.enemy_type = enemy_type
        self.max_health = 80
        self.health = self.max_health
        self.damage = 12
        self.speed = 90
        self.xp_value = 30
        self.gold_drop = random.randint(5, 15)

        self.vx = 0
        self.vy = 0

        # AI state
        self.state = "idle"
        self.target = None
        self.aggro_range = 350
        self.attack_range = 45
        self.attack_cooldown = 0
        self.attack_speed = 1.8

        # Combat system
        self.combat_system = combat_system
        self.status_effects = StatusEffectManager()

        # Visual
        self.color = (180, 80, 80)
        self.hurt_flash = 0
        self.name = "Enemy"

        # Particles
        self.particles = ParticleSystem()

        self.alive = True

    def update(self, dt, player, projectiles=None):
        """Update enemy AI and state"""
        if not self.alive:
            return

        # Update status effects
        self.status_effects.update(dt)

        # Apply speed modifications
        speed_mult = 1.0
        if self.status_effects.has_effect('speed'):
            speed_mult += self.status_effects.get_effect_strength('speed')
        if self.status_effects.has_effect('slow'):
            speed_mult -= self.status_effects.get_effect_strength('slow')

        effective_speed = self.speed * speed_mult

        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.hurt_flash > 0:
            self.hurt_flash -= dt

        # Poison damage
        if self.status_effects.has_effect('poison'):
            poison_dmg = self.status_effects.get_effect_strength('poison') * dt
            self.health -= poison_dmg
            if self.health <= 0:
                self.die(player)

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
                    self.vx = (dx / distance) * effective_speed
                    self.vy = (dy / distance) * effective_speed
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

        if self.combat_system:
            self.combat_system.create_hitbox(
                self.x, self.y,
                radius=self.attack_range,
                damage=self.damage,
                owner=self,
                duration=0.2,
                knockback=15
            )

        # Visual feedback
        self.particles.add_attack_effect(self.x, self.y, player.x, player.y, self.color)

    def take_damage(self, amount, source=None):
        """Take damage - FIXED to actually reduce health"""
        if not self.alive:
            return

        self.health -= amount
        self.hurt_flash = 0.25

        # Knockback
        if source:
            dx = self.x - source.x
            dy = self.y - source.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                self.x += (dx / dist) * 25
                self.y += (dy / dist) * 25

        # Damage numbers
        self.particles.add_damage_numbers(self.x, self.y - 20, int(amount), (255, 200, 100))

        print(f"{self.name} took {amount} damage! HP: {self.health:.1f}/{self.max_health}")

        if self.health <= 0:
            self.die(source)

    def die(self, killer=None):
        """Handle death"""
        self.alive = False
        self.particles.add_death_effect(self.x, self.y, self.color)

        print(f"{self.name} defeated!")

        # Grant rewards
        if killer and hasattr(killer, 'add_xp'):
            killer.add_xp(self.xp_value)
        if killer and hasattr(killer, 'gold'):
            killer.gold += self.gold_drop

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

        # Status effect visuals
        if self.status_effects.has_effect('poison'):
            # Green tint for poison
            color = tuple(min(255, c + 60) if i == 1 else c for i, c in enumerate(color))

        # Draw enemy
        pygame.draw.rect(
            screen,
            color,
            (int(screen_x - self.width // 2), int(screen_y - self.height // 2),
             self.width, self.height)
        )

        # Enemy label
        font = pygame.font.Font(None, 14)
        label = font.render(self.enemy_type, True, (220, 220, 220))
        label_rect = label.get_rect(center=(int(screen_x), int(screen_y - self.height - 10)))
        screen.blit(label, label_rect)

        # Health bar
        self.render_health_bar(screen, screen_x, screen_y - self.height // 2 - 5)

        # Particles
        self.particles.render(screen, camera)

    def render_health_bar(self, screen, x, y):
        """Render health bar"""
        bar_width = 32
        bar_height = 4
        health_ratio = max(0, self.health / self.max_health)

        # Background
        pygame.draw.rect(screen, (40, 40, 40), (x - bar_width // 2, y, bar_width, bar_height))

        # Health
        health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (200, 50, 50), (x - bar_width // 2, y, health_width, bar_height))

class ArcherEnemy(Enemy):
    """Ranged attacker that shoots projectiles"""

    def __init__(self, x, y, combat_system=None):
        super().__init__(x, y, "Void Archer", combat_system)
        self.max_health = 60
        self.health = self.max_health
        self.damage = 15
        self.speed = 70
        self.color = (120, 100, 180)
        self.xp_value = 40

        # Ranged combat
        self.attack_range = 250
        self.aggro_range = 300
        self.attack_speed = 2.0
        self.projectile_speed = 200
        self.name = "Void Archer"

    def attack(self, player):
        """Shoot projectile at player"""
        self.attack_cooldown = self.attack_speed

        # Calculate direction to player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist > 0:
            from combat_system import Projectile

            vx = (dx / dist) * self.projectile_speed
            vy = (dy / dist) * self.projectile_speed

            # Create projectile
            projectile = Projectile(
                self.x, self.y,
                vx, vy,
                self.damage,
                owner=self,
                size=6,
                color=(150, 100, 200),
                lifetime=3.0
            )

            # Store in combat system or return it
            if hasattr(self, 'projectiles'):
                self.projectiles.append(projectile)

        # Visual
        self.particles.add_attack_effect(self.x, self.y, player.x, player.y, self.color)

class BerserkerEnemy(Enemy):
    """Gets faster and stronger when damaged"""

    def __init__(self, x, y, combat_system=None):
        super().__init__(x, y, "Blood Berserker", combat_system)
        self.max_health = 120
        self.health = self.max_health
        self.damage = 18
        self.speed = 100
        self.color = (200, 60, 60)
        self.xp_value = 50
        self.name = "Blood Berserker"

        self.base_speed = self.speed
        self.base_damage = self.damage
        self.enraged = False

    def take_damage(self, amount, source=None):
        """Enrage when below 50% health"""
        super().take_damage(amount, source)

        health_percent = self.health / self.max_health

        if health_percent < 0.5 and not self.enraged:
            self.enraged = True
            self.speed = self.base_speed * 1.5
            self.damage = self.base_damage * 1.3
            self.color = (255, 30, 30)
            print(f"{self.name} is ENRAGED!")

class StealthEnemy(Enemy):
    """Can become invisible and ambush"""

    def __init__(self, x, y, combat_system=None):
        super().__init__(x, y, "Shadow Stalker", combat_system)
        self.max_health = 50
        self.health = self.max_health
        self.damage = 20
        self.speed = 130
        self.color = (80, 80, 120)
        self.xp_value = 45
        self.name = "Shadow Stalker"

        self.invisible = False
        self.invisibility_cooldown = 0
        self.invisibility_duration = 0

    def update(self, dt, player, projectiles=None):
        super().update(dt, player, projectiles)

        # Invisibility mechanic
        self.invisibility_cooldown -= dt

        if self.invisibility_duration > 0:
            self.invisibility_duration -= dt
            self.invisible = True
        else:
            self.invisible = False

        # Try to go invisible
        dist_to_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        if dist_to_player > 150 and dist_to_player < 300 and self.invisibility_cooldown <= 0:
            self.invisibility_duration = 2.0
            self.invisibility_cooldown = 8.0
            self.particles.add_teleport_effect(self.x, self.y, (100, 100, 150))

    def render(self, screen, camera):
        """Render with transparency when invisible"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Semi-transparent when invisible
        if self.invisible:
            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            color_with_alpha = (*self.color, 80)
            surf.fill(color_with_alpha)
            screen.blit(surf, (int(screen_x - self.width // 2), int(screen_y - self.height // 2)))
        else:
            super().render(screen, camera)

class PoisonEnemy(Enemy):
    """Applies poison on hit"""

    def __init__(self, x, y, combat_system=None):
        super().__init__(x, y, "Toxic Spitter", combat_system)
        self.max_health = 70
        self.health = self.max_health
        self.damage = 8
        self.speed = 85
        self.color = (100, 180, 80)
        self.xp_value = 40
        self.name = "Toxic Spitter"

    def attack(self, player):
        """Attack that poisons"""
        super().attack(player)

        # Apply poison
        if hasattr(player, 'status_effects'):
            player.status_effects.add_effect('poison', duration=5.0, strength=5.0)
            print(f"{self.name} poisoned the player!")

class TeleporterEnemy(Enemy):
    """Teleports around the player"""

    def __init__(self, x, y, combat_system=None):
        super().__init__(x, y, "Phase Walker", combat_system)
        self.max_health = 65
        self.health = self.max_health
        self.damage = 14
        self.speed = 110
        self.color = (100, 150, 200)
        self.xp_value = 45
        self.name = "Phase Walker"

        self.teleport_cooldown = 0
        self.teleport_timer = 4.0

    def update(self, dt, player, projectiles=None):
        super().update(dt, player, projectiles)

        # Teleport mechanic
        self.teleport_cooldown -= dt

        dist_to_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)

        if self.teleport_cooldown <= 0 and dist_to_player > 100 and dist_to_player < self.aggro_range:
            self.teleport_near_player(player)

    def teleport_near_player(self, player):
        """Teleport to random position near player"""
        self.teleport_cooldown = self.teleport_timer

        # Old position effect
        self.particles.add_teleport_effect(self.x, self.y, self.color)

        # Teleport
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(80, 150)

        self.x = player.x + math.cos(angle) * distance
        self.y = player.y + math.sin(angle) * distance

        # New position effect
        self.particles.add_teleport_effect(self.x, self.y, self.color)

def create_enemy(enemy_type, x, y, combat_system=None):
    """Factory function for creating enemies"""
    enemy_types = {
        "Basic": Enemy,
        "Void Archer": ArcherEnemy,
        "Blood Berserker": BerserkerEnemy,
        "Shadow Stalker": StealthEnemy,
        "Toxic Spitter": PoisonEnemy,
        "Phase Walker": TeleporterEnemy
    }

    enemy_class = enemy_types.get(enemy_type, Enemy)
    return enemy_class(x, y, combat_system)
