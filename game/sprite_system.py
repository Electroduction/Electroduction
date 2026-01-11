"""
Sprite System - Enhanced visual rendering with simple sprite shapes
"""

import pygame
import math

class SpriteRenderer:
    """Renders entities with improved sprites and animations"""

    def __init__(self):
        self.animation_time = 0

    def update(self, dt):
        """Update animations"""
        self.animation_time += dt

    def render_player(self, screen, camera, player):
        """Render player with enhanced sprite"""
        screen_x, screen_y = camera.world_to_screen(player.x, player.y)

        # Hurt flash
        if player.hurt_flash > 0:
            color = (255, 100, 100)
        elif player.is_dodging:
            color = (150, 200, 255)
        else:
            color = player.color

        # Body (circle)
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), player.width // 2)

        # Armor highlights
        highlight_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.circle(screen, highlight_color, (int(screen_x), int(screen_y)), player.width // 2, 2)

        # Face direction indicator
        end_x = screen_x + math.cos(player.facing_angle) * 22
        end_y = screen_y + math.sin(player.facing_angle) * 22
        pygame.draw.line(screen, (255, 255, 255), (screen_x, screen_y), (end_x, end_y), 4)

        # Weapon arc when attacking
        if player.attack_cooldown > 0:
            arc_progress = 1 - (player.attack_cooldown / player.attack_speed)
            arc_angle = player.facing_angle + (arc_progress * math.pi - math.pi/2)

            weapon_x = screen_x + math.cos(arc_angle) * 25
            weapon_y = screen_y + math.sin(arc_angle) * 25

            pygame.draw.line(screen, (200, 200, 255), (screen_x, screen_y), (weapon_x, weapon_y), 5)
            pygame.draw.circle(screen, (255, 255, 200), (int(weapon_x), int(weapon_y)), 6)

        # Health bar above
        self.render_health_bar(screen, screen_x, screen_y - 35, player.health, player.max_health, 45)

        # Status effects icons
        status_y = screen_y - 50
        if hasattr(player, 'status_effects'):
            for effect in player.status_effects.effects:
                self.render_status_icon(screen, screen_x, status_y, effect.effect_type)
                status_y -= 12

        # Label
        font = pygame.font.Font(None, 16)
        label = font.render("PLAYER", True, (220, 255, 220))
        label_rect = label.get_rect(center=(int(screen_x), int(screen_y - 45)))
        screen.blit(label, label_rect)

    def render_enemy(self, screen, camera, enemy):
        """Render enemy with enhanced sprite"""
        if not enemy.alive:
            return

        screen_x, screen_y = camera.world_to_screen(enemy.x, enemy.y)

        # Hurt flash
        if enemy.hurt_flash > 0:
            color = (255, 150, 150)
        else:
            color = enemy.color

        # Status effect visuals
        if hasattr(enemy, 'status_effects'):
            if enemy.status_effects.has_effect('poison'):
                color = tuple(min(255, c if i != 1 else c + 80) for i, c in enumerate(color))

        # Body shape varies by type
        if "Archer" in enemy.enemy_type:
            # Triangle for ranged
            points = [
                (screen_x, screen_y - enemy.height // 2),
                (screen_x - enemy.width // 2, screen_y + enemy.height // 2),
                (screen_x + enemy.width // 2, screen_y + enemy.height // 2)
            ]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 2)

        elif "Berserker" in enemy.enemy_type:
            # Large square
            pygame.draw.rect(
                screen, color,
                (int(screen_x - enemy.width // 2), int(screen_y - enemy.height // 2),
                 enemy.width, enemy.height)
            )

            # Angry eyes if enraged
            if hasattr(enemy, 'enraged') and enemy.enraged:
                pygame.draw.circle(screen, (255, 255, 0), (int(screen_x - 6), int(screen_y - 5)), 3)
                pygame.draw.circle(screen, (255, 255, 0), (int(screen_x + 6), int(screen_y - 5)), 3)

        elif "Stalker" in enemy.enemy_type or "Shadow" in enemy.enemy_type:
            # Diamond shape
            points = [
                (screen_x, screen_y - enemy.height // 2),
                (screen_x + enemy.width // 2, screen_y),
                (screen_x, screen_y + enemy.height // 2),
                (screen_x - enemy.width // 2, screen_y)
            ]

            if hasattr(enemy, 'invisible') and enemy.invisible:
                # Semi-transparent
                surf = pygame.Surface((enemy.width * 2, enemy.height * 2), pygame.SRCALPHA)
                adjusted_points = [(p[0] - screen_x + enemy.width, p[1] - screen_y + enemy.height) for p in points]
                pygame.draw.polygon(surf, (*color, 80), adjusted_points)
                screen.blit(surf, (int(screen_x - enemy.width), int(screen_y - enemy.height)))
            else:
                pygame.draw.polygon(screen, color, points)
                pygame.draw.polygon(screen, (255, 255, 255), points, 2)

        else:
            # Default rectangle
            pygame.draw.rect(
                screen, color,
                (int(screen_x - enemy.width // 2), int(screen_y - enemy.height // 2),
                 enemy.width, enemy.height)
            )

            # Eyes
            pygame.draw.circle(screen, (255, 200, 100), (int(screen_x - 6), int(screen_y - 4)), 3)
            pygame.draw.circle(screen, (255, 200, 100), (int(screen_x + 6), int(screen_y - 4)), 3)

        # Enemy type label
        font = pygame.font.Font(None, 14)
        label = font.render(enemy.enemy_type, True, (220, 220, 220))
        label_rect = label.get_rect(center=(int(screen_x), int(screen_y - enemy.height - 12)))
        screen.blit(label, label_rect)

        # Health bar
        self.render_health_bar(screen, screen_x, screen_y - enemy.height // 2 - 8, enemy.health, enemy.max_health, 35)

        # Status icons
        if hasattr(enemy, 'status_effects'):
            status_x = screen_x - 15
            for effect in enemy.status_effects.effects:
                self.render_status_icon(screen, status_x, screen_y - enemy.height - 22, effect.effect_type)
                status_x += 12

    def render_health_bar(self, screen, x, y, health, max_health, width=40):
        """Render health bar"""
        height = 5
        health_ratio = max(0, min(1, health / max_health))

        # Background
        pygame.draw.rect(screen, (60, 20, 20), (x - width // 2, y, width, height))

        # Health
        health_width = int(width * health_ratio)
        if health_ratio > 0.6:
            health_color = (100, 255, 100)
        elif health_ratio > 0.3:
            health_color = (255, 255, 100)
        else:
            health_color = (255, 100, 100)

        pygame.draw.rect(screen, health_color, (x - width // 2, y, health_width, height))

        # Border
        pygame.draw.rect(screen, (200, 200, 200), (x - width // 2, y, width, height), 1)

    def render_status_icon(self, screen, x, y, effect_type):
        """Render status effect icon"""
        colors = {
            'poison': (100, 255, 100),
            'slow': (100, 150, 255),
            'speed': (255, 200, 100),
            'regen': (150, 255, 150),
            'burn': (255, 150, 50)
        }

        color = colors.get(effect_type, (200, 200, 200))
        pygame.draw.circle(screen, color, (int(x), int(y)), 5)
        pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 5, 1)

    def render_npc(self, screen, camera, npc):
        """Render NPC with distinct sprite"""
        screen_x, screen_y = camera.world_to_screen(npc.x, npc.y)

        # NPC body (different shape from enemies)
        pygame.draw.circle(screen, npc.color, (int(screen_x), int(screen_y)), npc.width // 2)

        # Face
        pygame.draw.circle(screen, (255, 230, 200), (int(screen_x), int(screen_y - 3)), npc.width // 3)

        # Eyes
        pygame.draw.circle(screen, (50, 50, 100), (int(screen_x - 4), int(screen_y - 5)), 2)
        pygame.draw.circle(screen, (50, 50, 100), (int(screen_x + 4), int(screen_y - 5)), 2)

        # Hat/indicator
        if npc.npc_type == "vendor":
            pygame.draw.rect(screen, (180, 150, 50), (int(screen_x - 10), int(screen_y - 20), 20, 8))
        elif npc.npc_type == "quest_giver":
            # Exclamation mark
            font = pygame.font.Font(None, 20)
            exclaim = font.render("!", True, (255, 255, 100))
            screen.blit(exclaim, (int(screen_x - 3), int(screen_y - 25)))

        # Interaction indicator
        if npc.in_range:
            pulse = abs(math.sin(self.animation_time * 4))
            ring_radius = npc.interaction_range
            color_alpha = int(100 + pulse * 100)

            pygame.draw.circle(screen, (200, 200, 100), (int(screen_x), int(screen_y)), ring_radius, 2)

            # "F to interact" text
            font = pygame.font.Font(None, 16)
            text = font.render("Press F", True, (255, 255, 200))
            text_rect = text.get_rect(center=(int(screen_x), int(screen_y - 40)))
            screen.blit(text, text_rect)

        # Name
        font = pygame.font.Font(None, 15)
        name_text = font.render(npc.name, True, (220, 220, 255))
        name_rect = name_text.get_rect(center=(int(screen_x), int(screen_y - 28)))
        screen.blit(name_text, name_rect)
