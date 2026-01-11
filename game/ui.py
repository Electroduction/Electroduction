"""
UI System - HUD, menus, inventory
"""

import pygame
import math

class UI:
    """Game UI system"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Fonts
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 36)

        # State
        self.show_inventory = False
        self.selected_item = None

        # Colors
        self.color_bg = (20, 20, 30)
        self.color_panel = (40, 40, 50)
        self.color_highlight = (80, 120, 180)
        self.color_text = (220, 220, 220)
        self.color_health = (200, 50, 50)
        self.color_xp = (100, 200, 255)

    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.toggle_inventory()

    def toggle_inventory(self):
        """Toggle inventory display"""
        self.show_inventory = not self.show_inventory

    def render_game_hud(self, screen, player):
        """Render in-game HUD"""
        # Health bar
        self.render_health_bar(screen, 20, 20, player)

        # XP bar
        self.render_xp_bar(screen, 20, 60, player)

        # Level
        level_text = self.font_medium.render(f"Level {player.level}", True, self.color_text)
        screen.blit(level_text, (20, 85))

        # Abilities cooldowns
        self.render_ability_icons(screen, player)

        # Stats (top right)
        self.render_stats_panel(screen, player)

    def render_health_bar(self, screen, x, y, player):
        """Render health bar"""
        bar_width = 250
        bar_height = 25
        health_ratio = player.health / player.max_health

        # Background
        pygame.draw.rect(screen, (60, 20, 20), (x, y, bar_width, bar_height))

        # Health
        health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, self.color_health, (x, y, health_width, bar_height))

        # Border
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height), 2)

        # Text
        health_text = self.font_small.render(
            f"HP: {int(player.health)}/{int(player.max_health)}",
            True, (255, 255, 255)
        )
        screen.blit(health_text, (x + 10, y + 5))

    def render_xp_bar(self, screen, x, y, player):
        """Render XP bar"""
        bar_width = 250
        bar_height = 15
        xp_ratio = player.xp / player.xp_to_next_level

        # Background
        pygame.draw.rect(screen, (20, 40, 60), (x, y, bar_width, bar_height))

        # XP
        xp_width = int(bar_width * xp_ratio)
        pygame.draw.rect(screen, self.color_xp, (x, y, xp_width, bar_height))

        # Border
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height), 2)

        # Text
        xp_text = self.font_small.render(
            f"XP: {int(player.xp)}/{int(player.xp_to_next_level)}",
            True, (200, 200, 200)
        )
        screen.blit(xp_text, (x + 10, y))

    def render_ability_icons(self, screen, player):
        """Render ability icons with cooldowns"""
        x = 20
        y = self.screen_height - 80

        icon_size = 50
        spacing = 10

        ability_keys = ['Q', 'E', 'R', 'F']

        for i in range(4):
            # Icon background
            icon_x = x + i * (icon_size + spacing)

            # Cooldown overlay
            if i < len(player.ability_cooldowns):
                cooldown = player.ability_cooldowns[i]

                # Get ability if equipped
                ability = None
                if i < len(player.equipped_abilities):
                    ability = player.equipped_abilities[i]

                if ability:
                    # Background (colored by ability type)
                    color = ability.get_color()
                else:
                    color = (60, 60, 60)

                pygame.draw.rect(screen, color, (icon_x, y, icon_size, icon_size))

                # Cooldown overlay
                if cooldown > 0 and ability:
                    cooldown_ratio = cooldown / ability.cooldown
                    overlay_height = int(icon_size * cooldown_ratio)

                    overlay = pygame.Surface((icon_size, overlay_height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, (icon_x, y + icon_size - overlay_height))

                    # Cooldown text
                    cd_text = self.font_small.render(f"{cooldown:.1f}", True, (255, 255, 255))
                    text_rect = cd_text.get_rect(center=(icon_x + icon_size // 2, y + icon_size // 2))
                    screen.blit(cd_text, text_rect)

                # Border
                pygame.draw.rect(screen, (100, 100, 100), (icon_x, y, icon_size, icon_size), 2)

                # Key label
                key_text = self.font_small.render(ability_keys[i], True, self.color_text)
                screen.blit(key_text, (icon_x + 5, y + icon_size + 5))

        # Dodge cooldown
        dodge_x = x + 4 * (icon_size + spacing) + 20
        pygame.draw.rect(screen, (80, 100, 120), (dodge_x, y, icon_size, icon_size))

        if player.dodge_cooldown > 0:
            cooldown_ratio = player.dodge_cooldown / 1.0
            overlay_height = int(icon_size * cooldown_ratio)

            overlay = pygame.Surface((icon_size, overlay_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (dodge_x, y + icon_size - overlay_height))

        pygame.draw.rect(screen, (100, 100, 100), (dodge_x, y, icon_size, icon_size), 2)

        dodge_text = self.font_small.render("SPACE", True, self.color_text)
        screen.blit(dodge_text, (dodge_x + 3, y + icon_size + 5))

    def render_stats_panel(self, screen, player):
        """Render player stats"""
        x = self.screen_width - 200
        y = 20

        panel_width = 180
        panel_height = 150

        # Background
        pygame.draw.rect(screen, self.color_panel, (x, y, panel_width, panel_height))
        pygame.draw.rect(screen, (80, 80, 90), (x, y, panel_width, panel_height), 2)

        # Stats
        stats = [
            f"Level: {player.level}",
            f"Power: {int(player.power)}",
            f"Vitality: {int(player.vitality)}",
            f"Focus: {int(player.focus)}",
            f"Celerity: {int(player.celerity)}",
        ]

        text_y = y + 10
        for stat in stats:
            text = self.font_small.render(stat, True, self.color_text)
            screen.blit(text, (x + 10, text_y))
            text_y += 25

    def render_hub_info(self, screen, player, game_state):
        """Render hub-specific UI"""
        # Echo Rank
        rank_text = self.font_large.render(f"Echo Rank {game_state.echo_rank}", True, (150, 200, 255))
        screen.blit(rank_text, (self.screen_width // 2 - 120, 20))

        # Resources
        x = 20
        y = 120

        resources = [
            f"Echo Shards: {game_state.echo_shards}",
            f"Void Essence: {game_state.void_essence}",
            f"Solar Essence: {game_state.solar_essence}",
            f"Temporal Essence: {game_state.temporal_essence}"
        ]

        for resource in resources:
            text = self.font_medium.render(resource, True, self.color_text)
            screen.blit(text, (x, y))
            y += 30

        # Instructions
        instructions = [
            "Press ENTER to enter dungeon",
            "Press F to interact with NPCs",
            "Press I for inventory"
        ]

        y = self.screen_height - 100
        for instruction in instructions:
            text = self.font_small.render(instruction, True, (180, 180, 180))
            screen.blit(text, (20, y))
            y += 25

    def render_inventory(self, screen, player):
        """Render inventory screen"""
        # Background overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Inventory panel
        panel_width = 800
        panel_height = 600
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2

        pygame.draw.rect(screen, self.color_panel, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, self.color_highlight, (panel_x, panel_y, panel_width, panel_height), 3)

        # Title
        title = self.font_large.render("INVENTORY", True, self.color_text)
        screen.blit(title, (panel_x + 20, panel_y + 20))

        # TODO: Render inventory items
        # This would show equipped items, inventory grid, item stats, etc.

        # Placeholder
        placeholder = self.font_medium.render("Inventory system - Items will appear here", True, (150, 150, 150))
        screen.blit(placeholder, (panel_x + 200, panel_y + 200))

        # Close instruction
        close_text = self.font_small.render("Press I to close", True, self.color_text)
        screen.blit(close_text, (panel_x + panel_width - 150, panel_y + panel_height - 30))

    def render_minimap(self, screen, dungeon, player):
        """Render minimap"""
        # TODO: Implement minimap showing explored rooms
        pass
