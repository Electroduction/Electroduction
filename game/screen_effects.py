"""
AAA Screen Effects - Screen shake, freeze frames, slow motion, flash effects
Inspired by Hades, Celeste, Dead Cells
"""

import pygame
import random
import math

class ScreenEffects:
    """Manages all screen-level effects"""

    def __init__(self):
        # Screen shake
        self.shake_amount = 0
        self.shake_duration = 0
        self.shake_x = 0
        self.shake_y = 0

        # Freeze frame
        self.freeze_duration = 0
        self.freeze_timer = 0

        # Slow motion
        self.slow_mo_duration = 0
        self.slow_mo_timer = 0
        self.slow_mo_factor = 0.3

        # Flash
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.flash_duration = 0

        # Chromatic aberration (for hits)
        self.aberration_amount = 0

        # Vignette intensity
        self.vignette_intensity = 0.3

    def add_shake(self, amount, duration=0.3):
        """Add screen shake"""
        self.shake_amount = max(self.shake_amount, amount)
        self.shake_duration = max(self.shake_duration, duration)

    def add_freeze(self, duration=0.05):
        """Add freeze frame (hit pause)"""
        self.freeze_duration = duration
        self.freeze_timer = duration

    def add_slow_mo(self, duration=1.0, factor=0.3):
        """Add slow motion effect"""
        self.slow_mo_duration = duration
        self.slow_mo_timer = duration
        self.slow_mo_factor = factor

    def add_flash(self, color=(255, 255, 255), alpha=200, duration=0.1):
        """Add screen flash"""
        self.flash_color = color
        self.flash_alpha = alpha
        self.flash_duration = duration

    def update(self, dt):
        """Update all effects"""
        # Update shake
        if self.shake_duration > 0:
            self.shake_duration -= dt

            # Random shake offset
            self.shake_x = random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_y = random.uniform(-self.shake_amount, self.shake_amount)

            # Decay shake
            self.shake_amount *= 0.9

            if self.shake_duration <= 0:
                self.shake_x = 0
                self.shake_y = 0
                self.shake_amount = 0
        else:
            self.shake_x = 0
            self.shake_y = 0

        # Update freeze
        if self.freeze_timer > 0:
            self.freeze_timer -= dt

            if self.freeze_timer <= 0:
                self.freeze_duration = 0

        # Update slow mo
        if self.slow_mo_timer > 0:
            self.slow_mo_timer -= dt

            if self.slow_mo_timer <= 0:
                self.slow_mo_duration = 0

        # Update flash
        if self.flash_alpha > 0:
            self.flash_alpha -= dt * 1000  # Fade out quickly

        # Update aberration
        if self.aberration_amount > 0:
            self.aberration_amount -= dt * 100

    def get_time_scale(self):
        """Get current time scale (for slow-mo)"""
        if self.is_frozen():
            return 0.0

        if self.slow_mo_timer > 0:
            return self.slow_mo_factor

        return 1.0

    def is_frozen(self):
        """Check if game is frozen"""
        return self.freeze_timer > 0

    def get_shake_offset(self):
        """Get current shake offset"""
        return self.shake_x, self.shake_y

    def render_post_effects(self, screen):
        """Render post-processing effects on top of game"""
        width, height = screen.get_size()

        # Flash effect
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            flash_surf.fill((*self.flash_color, int(max(0, self.flash_alpha))))
            screen.blit(flash_surf, (0, 0))

        # Vignette
        self.render_vignette(screen)

    def render_vignette(self, screen):
        """Render vignette effect"""
        width, height = screen.get_size()

        # Create vignette surface
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)

        # Draw radial gradient
        center_x, center_y = width // 2, height // 2
        max_radius = math.sqrt(center_x**2 + center_y**2)

        for radius in range(int(max_radius), 0, -20):
            alpha = int((radius / max_radius) * 100 * self.vignette_intensity)
            alpha = min(255, max(0, alpha))

            pygame.draw.ellipse(
                vignette,
                (0, 0, 0, 255 - alpha),
                (center_x - radius, center_y - radius, radius * 2, radius * 2)
            )

        screen.blit(vignette, (0, 0))

class DamageNumber:
    """Floating damage number with style"""

    def __init__(self, x, y, amount, is_crit=False, is_heal=False):
        self.x = x
        self.y = y
        self.amount = amount
        self.is_crit = is_crit
        self.is_heal = is_heal

        self.lifetime = 1.0
        self.max_lifetime = 1.0

        # Movement
        self.vy = -80 if not is_heal else -60
        self.vx = random.uniform(-20, 20)

        # Scale effect for crits
        self.scale = 1.5 if is_crit else 1.0
        self.target_scale = 1.0

        self.alive = True

    def update(self, dt):
        """Update damage number"""
        self.y += self.vy * dt
        self.x += self.vx * dt

        self.vy *= 0.95  # Slow down

        # Scale animation
        self.scale += (self.target_scale - self.scale) * dt * 5

        self.lifetime -= dt

        if self.lifetime <= 0:
            self.alive = False

    def render(self, screen, camera):
        """Render damage number"""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Color based on type
        if self.is_heal:
            color = (100, 255, 150)
        elif self.is_crit:
            color = (255, 220, 100)
        else:
            color = (255, 200, 200)

        # Font size based on crit and scale
        base_size = 28 if self.is_crit else 22
        font_size = int(base_size * self.scale)

        font = pygame.font.Font(None, font_size)

        # Format text
        text = str(int(self.amount))
        if self.is_crit:
            text = f"{text}!"

        # Fade out
        alpha = int(255 * (self.lifetime / self.max_lifetime))

        # Render with outline
        # Outline
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            outline_surf = font.render(text, True, (0, 0, 0))
            outline_surf.set_alpha(alpha)
            screen.blit(outline_surf, (int(screen_x + dx), int(screen_y + dy)))

        # Main text
        text_surf = font.render(text, True, color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(int(screen_x), int(screen_y)))
        screen.blit(text_surf, text_rect)

class ComboCounter:
    """Combo counter for successive hits"""

    def __init__(self):
        self.combo = 0
        self.combo_timer = 0
        self.combo_decay = 2.0  # Seconds before combo resets

        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)

    def add_hit(self):
        """Add to combo"""
        self.combo += 1
        self.combo_timer = self.combo_decay

    def reset(self):
        """Reset combo counter"""
        self.combo = 0
        self.combo_timer = 0

    def update(self, dt):
        """Update combo"""
        if self.combo_timer > 0:
            self.combo_timer -= dt

            if self.combo_timer <= 0:
                self.combo = 0

    def get_damage_multiplier(self):
        """Get damage multiplier from combo"""
        if self.combo < 5:
            return 1.0
        elif self.combo < 10:
            return 1.1
        elif self.combo < 20:
            return 1.2
        else:
            return 1.5

    def render(self, screen):
        """Render combo counter"""
        if self.combo < 3:
            return  # Don't show until 3+ combo

        width, height = screen.get_size()

        # Position (top right)
        x = width - 150
        y = 100

        # Combo number
        combo_text = f"{self.combo}x"
        combo_surf = self.font.render(combo_text, True, (255, 220, 100))

        # Pulse effect
        pulse = abs(math.sin(self.combo_timer * 10)) * 5
        combo_surf = pygame.transform.scale(
            combo_surf,
            (combo_surf.get_width() + int(pulse), combo_surf.get_height() + int(pulse))
        )

        combo_rect = combo_surf.get_rect(center=(x, y))
        screen.blit(combo_surf, combo_rect)

        # "COMBO" label
        label_surf = self.small_font.render("COMBO", True, (200, 200, 200))
        label_rect = label_surf.get_rect(center=(x, y + 30))
        screen.blit(label_surf, label_rect)

        # Multiplier
        mult = self.get_damage_multiplier()
        if mult > 1.0:
            mult_text = f"+{int((mult - 1.0) * 100)}% DMG"
            mult_surf = self.small_font.render(mult_text, True, (255, 150, 150))
            mult_rect = mult_surf.get_rect(center=(x, y + 55))
            screen.blit(mult_surf, mult_rect)

class Tooltip:
    """Tooltip system for items, abilities, etc."""

    def __init__(self):
        self.active = False
        self.title = ""
        self.description = []
        self.stats = []

        self.x = 0
        self.y = 0

        self.title_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 20)
        self.stat_font = pygame.font.Font(None, 18)

        self.bg_color = (30, 25, 40)
        self.border_color = (100, 150, 200)

    def show(self, title, description, stats=None, x=0, y=0):
        """Show tooltip"""
        self.active = True
        self.title = title
        self.description = description if isinstance(description, list) else [description]
        self.stats = stats if stats else []
        self.x = x
        self.y = y

    def hide(self):
        """Hide tooltip"""
        self.active = False

    def render(self, screen):
        """Render tooltip"""
        if not self.active:
            return

        # Calculate dimensions
        padding = 15
        line_spacing = 25

        # Title
        title_surf = self.title_font.render(self.title, True, (255, 220, 150))
        width = title_surf.get_width() + padding * 2

        # Description lines
        desc_surfs = []
        for line in self.description:
            surf = self.text_font.render(line, True, (220, 220, 220))
            desc_surfs.append(surf)
            width = max(width, surf.get_width() + padding * 2)

        # Stats
        stat_surfs = []
        for stat in self.stats:
            surf = self.stat_font.render(stat, True, (150, 200, 150))
            stat_surfs.append(surf)
            width = max(width, surf.get_width() + padding * 2)

        # Total height
        height = (padding * 2 +
                 title_surf.get_height() +
                 len(desc_surfs) * line_spacing +
                 len(stat_surfs) * (line_spacing - 5))

        # Position (avoid screen edges)
        screen_width, screen_height = screen.get_size()
        x = min(self.x, screen_width - width - 10)
        y = min(self.y, screen_height - height - 10)

        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.bg_color, bg_rect, border_radius=8)
        pygame.draw.rect(screen, self.border_color, bg_rect, 2, border_radius=8)

        # Render content
        current_y = y + padding

        # Title
        screen.blit(title_surf, (x + padding, current_y))
        current_y += title_surf.get_height() + 5

        # Separator
        pygame.draw.line(screen, self.border_color,
                        (x + padding, current_y),
                        (x + width - padding, current_y), 1)
        current_y += 10

        # Description
        for surf in desc_surfs:
            screen.blit(surf, (x + padding, current_y))
            current_y += line_spacing

        # Stats
        if stat_surfs:
            current_y += 5
            for surf in stat_surfs:
                screen.blit(surf, (x + padding, current_y))
                current_y += line_spacing - 5
