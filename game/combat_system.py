"""
Enhanced Combat System - Fixed damage calculation and hit detection
"""

import pygame
import math
import random

class CombatSystem:
    """Manages all combat calculations and hit detection"""

    def __init__(self):
        self.active_hitboxes = []
        self.damage_cooldowns = {}  # Prevent multiple hits per attack

    def create_hitbox(self, x, y, radius, damage, owner, duration=0.1, knockback=20):
        """Create a melee attack hitbox"""
        hitbox = {
            'x': x,
            'y': y,
            'radius': radius,
            'damage': damage,
            'owner': owner,
            'duration': duration,
            'knockback': knockback,
            'hit_entities': set(),  # Track what we've already hit
            'lifetime': 0
        }
        self.active_hitboxes.append(hitbox)
        return hitbox

    def update(self, dt, enemies, player):
        """Update combat system"""
        # Update hitboxes
        for hitbox in self.active_hitboxes[:]:
            hitbox['lifetime'] += dt

            if hitbox['lifetime'] >= hitbox['duration']:
                self.active_hitboxes.remove(hitbox)
                continue

            # Check hits
            if hitbox['owner'] == 'player':
                # Player attacking enemies
                for enemy in enemies:
                    if enemy.alive and id(enemy) not in hitbox['hit_entities']:
                        dist = math.sqrt((enemy.x - hitbox['x'])**2 + (enemy.y - hitbox['y'])**2)

                        if dist < hitbox['radius'] + enemy.width/2:
                            # Hit!
                            enemy.take_damage(hitbox['damage'], player)
                            hitbox['hit_entities'].add(id(enemy))

                            # Knockback
                            dx = enemy.x - hitbox['x']
                            dy = enemy.y - hitbox['y']
                            dist = math.sqrt(dx**2 + dy**2)
                            if dist > 0:
                                enemy.x += (dx / dist) * hitbox['knockback']
                                enemy.y += (dy / dist) * hitbox['knockback']

            elif hasattr(hitbox['owner'], 'enemy_type'):
                # Enemy attacking player
                if id(player) not in hitbox['hit_entities']:
                    dist = math.sqrt((player.x - hitbox['x'])**2 + (player.y - hitbox['y'])**2)

                    if dist < hitbox['radius'] + player.width/2:
                        # Hit!
                        player.take_damage(hitbox['damage'])
                        hitbox['hit_entities'].add(id(player))

                        # Knockback
                        dx = player.x - hitbox['x']
                        dy = player.y - hitbox['y']
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist > 0:
                            player.x += (dx / dist) * hitbox['knockback']
                            player.y += (dy / dist) * hitbox['knockback']

    def clear(self):
        """Clear all hitboxes"""
        self.active_hitboxes.clear()

class Projectile:
    """Projectile system for ranged attacks"""

    def __init__(self, x, y, vx, vy, damage, owner, size=8, color=(255, 200, 100), lifetime=3.0, piercing=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.owner = owner
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.alive = True
        self.piercing = piercing
        self.hit_entities = set()

    def update(self, dt, enemies, player):
        """Update projectile"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

        if self.lifetime <= 0:
            self.alive = False
            return

        # Check collisions
        if self.owner == 'player':
            # Player projectile hitting enemies
            for enemy in enemies:
                if enemy.alive and id(enemy) not in self.hit_entities:
                    dist = math.sqrt((enemy.x - self.x)**2 + (enemy.y - self.y)**2)

                    if dist < self.size + enemy.width/2:
                        enemy.take_damage(self.damage, player)
                        self.hit_entities.add(id(enemy))

                        if not self.piercing:
                            self.alive = False
                        break

        elif hasattr(self.owner, 'enemy_type'):
            # Enemy projectile hitting player
            if id(player) not in self.hit_entities:
                dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)

                if dist < self.size + player.width/2:
                    player.take_damage(self.damage)
                    self.hit_entities.add(id(player))

                    if not self.piercing:
                        self.alive = False

    def render(self, screen, camera):
        """Render projectile"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Draw projectile with glow
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)

        # Outer glow
        glow_color = tuple(min(255, c + 50) for c in self.color[:3])
        pygame.draw.circle(screen, glow_color, (int(screen_x), int(screen_y)), self.size + 2, 2)

class StatusEffect:
    """Status effects (buffs/debuffs)"""

    def __init__(self, effect_type, duration, strength):
        self.effect_type = effect_type  # slow, speed, poison, regen, invuln, etc.
        self.duration = duration
        self.strength = strength
        self.elapsed = 0

    def update(self, dt):
        """Update effect"""
        self.elapsed += dt
        return self.elapsed < self.duration

    def get_remaining(self):
        """Get remaining duration"""
        return max(0, self.duration - self.elapsed)

class StatusEffectManager:
    """Manages status effects on entities"""

    def __init__(self):
        self.effects = []

    def add_effect(self, effect_type, duration, strength):
        """Add a status effect"""
        # Check if effect already exists
        for effect in self.effects:
            if effect.effect_type == effect_type:
                # Refresh duration
                effect.duration = max(effect.duration, duration)
                effect.strength = max(effect.strength, strength)
                return

        # Add new effect
        self.effects.append(StatusEffect(effect_type, duration, strength))

    def update(self, dt):
        """Update all effects"""
        self.effects = [e for e in self.effects if e.update(dt)]

    def has_effect(self, effect_type):
        """Check if has effect"""
        return any(e.effect_type == effect_type for e in self.effects)

    def get_effect_strength(self, effect_type):
        """Get total strength of an effect type"""
        total = 0
        for e in self.effects:
            if e.effect_type == effect_type:
                total += e.strength
        return total

    def clear(self):
        """Clear all effects"""
        self.effects.clear()
