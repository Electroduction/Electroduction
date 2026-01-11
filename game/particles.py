"""
Particle System - Visual effects and feedback
"""

import pygame
import math
import random

class Particle:
    """Single particle"""

    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self, dt):
        """Update particle"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

        # Apply gravity/drag
        self.vy += 100 * dt
        self.vx *= 0.98
        self.vy *= 0.98

        if self.lifetime <= 0:
            self.alive = False

    def render(self, screen, camera):
        """Render particle"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Fade out
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        alpha = max(0, min(255, alpha))

        # Create surface for alpha
        size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))

        try:
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, alpha)
            pygame.draw.circle(surf, color_with_alpha, (size, size), size)
            screen.blit(surf, (int(screen_x - size), int(screen_y - size)))
        except:
            # Fallback
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), size)

class TextParticle:
    """Floating text particle (damage numbers, etc.)"""

    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.vy = -50
        self.alive = True

    def update(self, dt):
        """Update text particle"""
        self.y += self.vy * dt
        self.lifetime -= dt

        if self.lifetime <= 0:
            self.alive = False

    def render(self, screen, camera):
        """Render text"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        font = pygame.font.Font(None, 20)

        # Fade out
        alpha = int(255 * (self.lifetime / self.max_lifetime))

        try:
            text_surf = font.render(str(self.text), True, self.color)
            text_surf.set_alpha(alpha)
            screen.blit(text_surf, (int(screen_x), int(screen_y)))
        except:
            text_surf = font.render(str(self.text), True, self.color)
            screen.blit(text_surf, (int(screen_x), int(screen_y)))

class ParticleSystem:
    """Manages all particles"""

    def __init__(self):
        self.particles = []
        self.text_particles = []

    def update(self, dt):
        """Update all particles"""
        # Update and remove dead particles
        self.particles = [p for p in self.particles if p.alive]
        self.text_particles = [p for p in self.text_particles if p.alive]

        for particle in self.particles:
            particle.update(dt)

        for text in self.text_particles:
            text.update(dt)

    def render(self, screen, camera):
        """Render all particles"""
        for particle in self.particles:
            particle.render(screen, camera)

        for text in self.text_particles:
            text.render(screen, camera)

    def add_particle(self, x, y, vx, vy, color, size=3, lifetime=0.5):
        """Add a particle"""
        self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def add_damage_numbers(self, x, y, amount, color=(255, 100, 100)):
        """Add floating damage text"""
        self.text_particles.append(TextParticle(x, y, str(int(amount)), color))

    def add_explosion(self, x, y, radius, color):
        """Create explosion effect"""
        num_particles = 20
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            size = random.uniform(3, 8)
            lifetime = random.uniform(0.3, 0.8)

            self.add_particle(x, y, vx, vy, color, size, lifetime)

    def add_slash_effect(self, x, y, angle, color):
        """Create slash trail"""
        num_particles = 10
        for i in range(num_particles):
            offset = i * 5
            px = x + math.cos(angle) * offset
            py = y + math.sin(angle) * offset

            # Perpendicular spread
            spread_angle = angle + math.pi / 2
            spread = random.uniform(-10, 10)
            px += math.cos(spread_angle) * spread
            py += math.sin(spread_angle) * spread

            vx = math.cos(angle) * 30
            vy = math.sin(angle) * 30

            self.add_particle(px, py, vx, vy, color, 4, 0.2)

    def add_dodge_trail(self, x, y, color):
        """Create dodge trail"""
        for _ in range(5):
            vx = random.uniform(-20, 20)
            vy = random.uniform(-20, 20)
            self.add_particle(x, y, vx, vy, color, 5, 0.3)

    def add_teleport_effect(self, x, y, color):
        """Teleport visual"""
        self.add_explosion(x, y, 50, color)

    def add_heal_effect(self, x, y):
        """Healing particles"""
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 50)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 50  # Upward bias

            self.add_particle(x, y, vx, vy, (100, 255, 150), 4, 0.6)

    def add_level_up_effect(self, x, y):
        """Level up celebration"""
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = random.choice([
                (255, 200, 100),
                (255, 255, 100),
                (200, 255, 150)
            ])

            self.add_particle(x, y, vx, vy, color, 6, 1.0)

    def add_death_effect(self, x, y, color):
        """Enemy death effect"""
        self.add_explosion(x, y, 40, color)

    def add_attack_effect(self, x1, y1, x2, y2, color):
        """Attack trail from attacker to target"""
        num_particles = 5
        for i in range(num_particles):
            t = i / num_particles
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t

            vx = (x2 - x1) * 0.1
            vy = (y2 - y1) * 0.1

            self.add_particle(px, py, vx, vy, color, 3, 0.2)

    def add_pulse(self, x, y, radius, color):
        """Pulsing ring effect"""
        # Create ring of particles
        num_particles = 20
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius

            vx = math.cos(angle) * 20
            vy = math.sin(angle) * 20

            self.add_particle(px, py, vx, vy, color, 4, 0.5)

    def add_shockwave(self, x, y, radius, color):
        """Shockwave effect"""
        self.add_pulse(x, y, radius, color)
        self.add_pulse(x, y, radius * 0.7, color)
        self.add_pulse(x, y, radius * 0.4, color)

    def add_drain_effect(self, x1, y1, x2, y2):
        """Energy drain from target to source"""
        num_particles = 8
        for i in range(num_particles):
            t = i / num_particles
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t

            vx = (x2 - x1) * 0.5
            vy = (y2 - y1) * 0.5

            self.add_particle(px, py, vx, vy, (200, 100, 255), 4, 0.4)

    def add_time_warp(self, x, y, radius):
        """Time distortion effect"""
        num_particles = 30
        for i in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, radius)
            px = x + math.cos(angle) * distance
            py = y + math.sin(angle) * distance

            # Spiral motion
            vx = math.cos(angle + math.pi / 2) * 50
            vy = math.sin(angle + math.pi / 2) * 50

            self.add_particle(px, py, vx, vy, (120, 180, 255), 3, 0.8)

    def add_bloom_effect(self, x, y, color):
        """Solar bloom"""
        self.add_explosion(x, y, 60, color)

    def add_emergence_effect(self, x, y, color):
        """Enemy emerging from ground"""
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            self.add_particle(x, y, vx, vy, color, 5, 0.4)

    def add_beam(self, x1, y1, x2, y2, color):
        """Beam effect"""
        num_particles = 20
        for i in range(num_particles):
            t = i / num_particles
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t

            # Add some spread
            spread_x = random.uniform(-5, 5)
            spread_y = random.uniform(-5, 5)

            self.add_particle(px + spread_x, py + spread_y, 0, 0, color, 6, 0.3)

    def add_clone_effect(self, x, y):
        """Temporal clone effect"""
        for _ in range(20):
            vx = random.uniform(-50, 50)
            vy = random.uniform(-50, 50)
            self.add_particle(x, y, vx, vy, (150, 200, 255), 4, 0.5)
