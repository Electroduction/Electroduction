"""
Boss encounters - Unique mechanics and phases
"""

import pygame
import math
import random
from enemies import Enemy

class Boss(Enemy):
    """Base boss class with phase system"""

    def __init__(self, x, y, name):
        super().__init__(x, y, "Boss")
        self.name = name
        self.max_health = 500
        self.health = self.max_health
        self.damage = 20
        self.speed = 60
        self.xp_value = 500

        # Boss-specific
        self.phase = 1
        self.phase_thresholds = [0.75, 0.5, 0.25]  # Health % to trigger phases
        self.boss_width = 60
        self.boss_height = 60

        # Visual
        self.color = (200, 50, 100)
        self.size_pulse = 0

    def update(self, dt, player):
        """Update with phase checking"""
        super().update(dt, player)

        # Check phase transitions
        health_percent = self.health / self.max_health
        for i, threshold in enumerate(self.phase_thresholds):
            if health_percent <= threshold and self.phase == i + 1:
                self.enter_phase(self.phase + 1)

        # Visual pulsing
        self.size_pulse += dt * 3

    def enter_phase(self, new_phase):
        """Transition to new phase"""
        self.phase = new_phase
        print(f"{self.name} enters phase {self.phase}!")

        # Heal a bit
        self.health = min(self.health + 50, self.max_health)

        # Phase transition effect
        self.particles.add_explosion(self.x, self.y, 100, self.color)

    def render(self, screen, camera):
        """Render boss with special effects"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Pulsing size
        pulse = math.sin(self.size_pulse) * 5

        # Flash effect
        if self.hurt_flash > 0:
            color = (255, 150, 150)
        else:
            color = self.color

        # Draw boss (larger)
        size = self.boss_width + pulse
        pygame.draw.rect(
            screen,
            color,
            (int(screen_x - size // 2), int(screen_y - size // 2), int(size), int(size))
        )

        # Draw phase indicator
        for i in range(self.phase):
            pygame.draw.circle(
                screen,
                (255, 200, 50),
                (int(screen_x - 20 + i * 15), int(screen_y - size // 2 - 20)),
                5
            )

        # Health bar (larger)
        self.render_boss_health_bar(screen, screen_x, screen_y - size // 2 - 30)

        # Name
        font = pygame.font.Font(None, 20)
        name_surf = font.render(self.name, True, (255, 200, 100))
        name_rect = name_surf.get_rect(center=(int(screen_x), int(screen_y - size // 2 - 45)))
        screen.blit(name_surf, name_rect)

        # Particles
        self.particles.render(screen, camera)

    def render_boss_health_bar(self, screen, x, y):
        """Render boss health bar"""
        bar_width = 120
        bar_height = 8
        health_ratio = self.health / self.max_health

        # Background
        pygame.draw.rect(screen, (40, 40, 40), (x - bar_width // 2, y, bar_width, bar_height))

        # Health
        health_width = int(bar_width * health_ratio)

        # Color based on phase
        if self.phase == 1:
            health_color = (50, 200, 50)
        elif self.phase == 2:
            health_color = (200, 200, 50)
        elif self.phase == 3:
            health_color = (200, 100, 50)
        else:
            health_color = (200, 50, 50)

        pygame.draw.rect(screen, health_color, (x - bar_width // 2, y, health_width, bar_height))

        # Phase segments
        for threshold in self.phase_thresholds:
            segment_x = x - bar_width // 2 + int(bar_width * threshold)
            pygame.draw.line(screen, (255, 255, 255), (segment_x, y), (segment_x, y + bar_height), 2)

class BrokenAegis(Boss):
    """The Broken Aegis - Void Titan boss"""

    def __init__(self, x, y):
        super().__init__(x, y, "The Broken Aegis")
        self.color = (100, 80, 140)
        self.max_health = 600
        self.health = self.max_health

        # Special attacks
        self.gravity_slam_cooldown = 0
        self.gravity_slam_timer = 5.0

    def update(self, dt, player):
        super().update(dt, player)

        # Gravity slam attack
        self.gravity_slam_cooldown -= dt
        if self.gravity_slam_cooldown <= 0 and self.state == "attack":
            self.gravity_slam(player)

    def gravity_slam(self, player):
        """Special gravity slam attack"""
        self.gravity_slam_cooldown = self.gravity_slam_timer

        # Create gravity wave
        self.particles.add_shockwave(self.x, self.y, 150, (100, 80, 140))

        # Damage and pull players
        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        if dist < 150:
            player.take_damage(self.damage * 1.5)

            # Pull player towards boss
            dx = self.x - player.x
            dy = self.y - player.y
            if dist > 0:
                player.x += (dx / dist) * 30
                player.y += (dy / dist) * 30

    def enter_phase(self, new_phase):
        super().enter_phase(new_phase)

        if new_phase == 2:
            # Speed up
            self.speed += 20
            self.gravity_slam_timer -= 1.0
        elif new_phase == 3:
            # More aggressive
            self.damage += 5
            self.gravity_slam_timer -= 1.0

class LyrasEclipse(Boss):
    """Lyra's Eclipse - Corrupted Solar Mystic"""

    def __init__(self, x, y):
        super().__init__(x, y, "Lyra's Eclipse")
        self.color = (200, 150, 80)
        self.max_health = 450
        self.health = self.max_health

        # Special mechanics
        self.solar_bloom_cooldown = 0
        self.solar_bloom_timer = 6.0
        self.healing = False

    def update(self, dt, player):
        super().update(dt, player)

        # Solar bloom healing
        self.solar_bloom_cooldown -= dt
        if self.solar_bloom_cooldown <= 0:
            self.spawn_solar_bloom()

    def spawn_solar_bloom(self):
        """Create healing bloom"""
        self.solar_bloom_cooldown = self.solar_bloom_timer

        # Spawn bloom at random position nearby
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(80, 150)

        bloom_x = self.x + math.cos(angle) * distance
        bloom_y = self.y + math.sin(angle) * distance

        self.particles.add_bloom_effect(bloom_x, bloom_y, (255, 200, 100))

        # Heal self if near bloom
        dist = math.sqrt((bloom_x - self.x)**2 + (bloom_y - self.y)**2)
        if dist < 50:
            heal_amount = 30
            self.health = min(self.health + heal_amount, self.max_health)
            self.particles.add_heal_effect(self.x, self.y)

    def enter_phase(self, new_phase):
        super().enter_phase(new_phase)

        if new_phase == 2:
            self.solar_bloom_timer -= 1.5
        elif new_phase == 3:
            # Desperate - more blooms
            self.solar_bloom_timer -= 2.0

class ChromancersCore(Boss):
    """The Chronomancer's Core - Time manipulation"""

    def __init__(self, x, y):
        super().__init__(x, y, "Chronomancer's Core")
        self.color = (120, 180, 220)
        self.max_health = 400
        self.health = self.max_health

        # Time mechanics
        self.time_rewind_cooldown = 0
        self.time_rewind_timer = 8.0
        self.saved_health = self.health

    def update(self, dt, player):
        super().update(dt, player)

        # Time rewind
        self.time_rewind_cooldown -= dt
        if self.time_rewind_cooldown <= 0 and self.health < self.saved_health:
            self.time_rewind()

    def time_rewind(self):
        """Rewind to previous state"""
        self.time_rewind_cooldown = self.time_rewind_timer

        self.particles.add_time_warp(self.x, self.y, 100)

        # Restore some health
        heal_amount = min(50, self.saved_health - self.health)
        self.health += heal_amount

        print(f"{self.name} rewinds time, restoring {heal_amount} health!")

    def take_damage(self, amount, source=None):
        """Save health state before taking damage"""
        self.saved_health = self.health
        super().take_damage(amount, source)

    def enter_phase(self, new_phase):
        super().enter_phase(new_phase)

        if new_phase == 2:
            self.time_rewind_timer -= 2.0
        elif new_phase == 3:
            # Clone self (would spawn adds)
            pass

def create_boss(boss_type, x, y):
    """Factory for creating bosses"""
    bosses = {
        "Broken Aegis": BrokenAegis,
        "Lyra's Eclipse": LyrasEclipse,
        "Chronomancer's Core": ChromancersCore
    }

    boss_class = bosses.get(boss_type, Boss)
    return boss_class(x, y)
