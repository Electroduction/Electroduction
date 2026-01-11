"""
AAA-Quality Menu System - Inspired by Hades
Main menu, settings, pause menu, upgrade menu, death screen
"""

import pygame
import json
import os

class MenuItem:
    """Single menu item"""

    def __init__(self, text, action, description=""):
        self.text = text
        self.action = action
        self.description = description
        self.selected = False

class Menu:
    """Base menu class"""

    def __init__(self, title, items):
        self.title = title
        self.items = items
        self.selected_index = 0
        self.active = True

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.item_font = pygame.font.Font(None, 36)
        self.desc_font = pygame.font.Font(None, 24)

        # Colors
        self.bg_color = (15, 12, 20)
        self.title_color = (255, 220, 150)
        self.item_color = (200, 200, 220)
        self.selected_color = (255, 200, 100)
        self.desc_color = (150, 150, 170)

    def handle_input(self, event):
        """Handle menu input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_index = (self.selected_index - 1) % len(self.items)
                return 'menu_move'

            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_index = (self.selected_index + 1) % len(self.items)
                return 'menu_move'

            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.items[self.selected_index].action

            elif event.key == pygame.K_ESCAPE:
                return 'back'

        return None

    def render(self, screen):
        """Render menu"""
        width, height = screen.get_size()

        # Background
        screen.fill(self.bg_color)

        # Add subtle pattern
        for i in range(0, width, 40):
            for j in range(0, height, 40):
                alpha = 20
                surf = pygame.Surface((2, 2), pygame.SRCALPHA)
                surf.fill((255, 255, 255, alpha))
                screen.blit(surf, (i, j))

        # Title
        title_surf = self.title_font.render(self.title, True, self.title_color)
        title_rect = title_surf.get_rect(center=(width // 2, 150))
        screen.blit(title_surf, title_rect)

        # Title underline
        pygame.draw.line(screen, self.title_color,
                        (title_rect.left, title_rect.bottom + 10),
                        (title_rect.right, title_rect.bottom + 10), 3)

        # Menu items
        start_y = 300
        spacing = 80

        for i, item in enumerate(self.items):
            is_selected = (i == self.selected_index)

            # Item text
            color = self.selected_color if is_selected else self.item_color
            font_size = 40 if is_selected else 36

            item_font = pygame.font.Font(None, font_size)
            item_surf = item_font.render(item.text, True, color)
            item_rect = item_surf.get_rect(center=(width // 2, start_y + i * spacing))

            # Selection indicator
            if is_selected:
                indicator = "►"
                ind_surf = item_font.render(indicator, True, color)
                ind_rect = ind_surf.get_rect(right=item_rect.left - 20, centery=item_rect.centery)
                screen.blit(ind_surf, ind_rect)

                # Glow effect
                glow_surf = pygame.Surface((item_rect.width + 40, item_rect.height + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 200, 100, 30),
                               (0, 0, item_rect.width + 40, item_rect.height + 20),
                               border_radius=10)
                screen.blit(glow_surf, (item_rect.x - 20, item_rect.y - 10))

            screen.blit(item_surf, item_rect)

            # Description
            if is_selected and item.description:
                desc_surf = self.desc_font.render(item.description, True, self.desc_color)
                desc_rect = desc_surf.get_rect(center=(width // 2, height - 100))
                screen.blit(desc_surf, desc_rect)

class MainMenu(Menu):
    """Main menu"""

    def __init__(self, game):
        items = [
            MenuItem("New Run", "new_run", "Begin a new journey into the Orivian ruins"),
            MenuItem("Continue", "continue", "Resume your last save"),
            MenuItem("Upgrades", "upgrades", "Spend Echo Shards on permanent upgrades"),
            MenuItem("Settings", "settings", "Configure game options"),
            MenuItem("Quit", "quit", "Exit ECHOFRONTIER")
        ]

        super().__init__("ECHOFRONTIER", items)
        self.game = game

class PauseMenu(Menu):
    """Pause menu during gameplay"""

    def __init__(self):
        items = [
            MenuItem("Resume", "resume", "Continue your run"),
            MenuItem("Restart Run", "restart", "Start over from the beginning"),
            MenuItem("Settings", "settings", "Adjust game settings"),
            MenuItem("Abandon Run", "abandon", "Return to main menu (lose progress)"),
        ]

        super().__init__("PAUSED", items)

class SettingsMenu(Menu):
    """Settings menu"""

    def __init__(self):
        self.settings = self.load_settings()

        items = [
            MenuItem(f"Music Volume: {int(self.settings['music_volume'] * 100)}%", "music_volume"),
            MenuItem(f"SFX Volume: {int(self.settings['sfx_volume'] * 100)}%", "sfx_volume"),
            MenuItem(f"Screen Shake: {'ON' if self.settings['screen_shake'] else 'OFF'}", "screen_shake"),
            MenuItem(f"Show Damage Numbers: {'ON' if self.settings['damage_numbers'] else 'OFF'}", "damage_numbers"),
            MenuItem(f"Auto-Pickup Items: {'ON' if self.settings['auto_pickup'] else 'OFF'}", "auto_pickup"),
            MenuItem("Back", "back", "Return to previous menu")
        ]

        super().__init__("SETTINGS", items)

    def load_settings(self):
        """Load settings from file"""
        default_settings = {
            'music_volume': 0.5,
            'sfx_volume': 0.7,
            'screen_shake': True,
            'damage_numbers': True,
            'auto_pickup': True
        }

        try:
            if os.path.exists('save/settings.json'):
                with open('save/settings.json', 'r') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
        except:
            pass

        return default_settings

    def save_settings(self):
        """Save settings to file"""
        try:
            os.makedirs('save', exist_ok=True)
            with open('save/settings.json', 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def handle_input(self, event):
        """Handle settings input"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                self.adjust_setting(-1)
                return 'setting_changed'

            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                self.adjust_setting(1)
                return 'setting_changed'

        return super().handle_input(event)

    def adjust_setting(self, direction):
        """Adjust selected setting"""
        selected = self.items[self.selected_index]

        if "Music Volume" in selected.text:
            self.settings['music_volume'] = max(0, min(1, self.settings['music_volume'] + direction * 0.1))
            selected.text = f"Music Volume: {int(self.settings['music_volume'] * 100)}%"

        elif "SFX Volume" in selected.text:
            self.settings['sfx_volume'] = max(0, min(1, self.settings['sfx_volume'] + direction * 0.1))
            selected.text = f"SFX Volume: {int(self.settings['sfx_volume'] * 100)}%"

        elif "Screen Shake" in selected.text:
            self.settings['screen_shake'] = not self.settings['screen_shake']
            selected.text = f"Screen Shake: {'ON' if self.settings['screen_shake'] else 'OFF'}"

        elif "Show Damage Numbers" in selected.text:
            self.settings['damage_numbers'] = not self.settings['damage_numbers']
            selected.text = f"Show Damage Numbers: {'ON' if self.settings['damage_numbers'] else 'OFF'}"

        elif "Auto-Pickup Items" in selected.text:
            self.settings['auto_pickup'] = not self.settings['auto_pickup']
            selected.text = f"Auto-Pickup Items: {'ON' if self.settings['auto_pickup'] else 'OFF'}"

        self.save_settings()

class DeathScreen:
    """Death/game over screen with stats"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 72)
        self.stat_font = pygame.font.Font(None, 32)
        self.desc_font = pygame.font.Font(None, 24)

        self.stats = {}

    def set_stats(self, stats):
        """Set run statistics"""
        self.stats = stats

    def render(self, screen):
        """Render death screen"""
        width, height = screen.get_size()

        # Dark overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((10, 5, 15, 220))
        screen.blit(overlay, (0, 0))

        # Title
        title = self.title_font.render("ECHO FADES...", True, (200, 80, 80))
        title_rect = title.get_rect(center=(width // 2, 120))
        screen.blit(title, title_rect)

        # Stats
        stat_list = [
            f"Floor Reached: {self.stats.get('floor', 1)}",
            f"Enemies Defeated: {self.stats.get('kills', 0)}",
            f"Gold Collected: {self.stats.get('gold', 0)}",
            f"Time Survived: {self.format_time(self.stats.get('time', 0))}",
            f"Damage Dealt: {self.stats.get('damage_dealt', 0)}",
            f"Damage Taken: {self.stats.get('damage_taken', 0)}",
        ]

        start_y = 250
        for stat in stat_list:
            stat_surf = self.stat_font.render(stat, True, (200, 200, 220))
            stat_rect = stat_surf.get_rect(center=(width // 2, start_y))
            screen.blit(stat_surf, stat_rect)
            start_y += 50

        # Instructions
        inst = self.desc_font.render("Press ENTER to continue", True, (150, 150, 170))
        inst_rect = inst.get_rect(center=(width // 2, height - 80))
        screen.blit(inst, inst_rect)

    def format_time(self, seconds):
        """Format time as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

class UpgradeMenu:
    """Meta-progression upgrade menu"""

    def __init__(self, game_state):
        self.game_state = game_state
        self.selected_index = 0

        # Define upgrades
        self.upgrades = [
            {
                'name': 'Health Boost',
                'description': 'Increase starting health by 20',
                'cost': 100,
                'max_level': 5,
                'current_level': 0,
                'stat': 'max_health',
                'value': 20
            },
            {
                'name': 'Power Boost',
                'description': 'Increase base damage by 5',
                'cost': 150,
                'max_level': 5,
                'current_level': 0,
                'stat': 'power',
                'value': 5
            },
            {
                'name': 'Speed Boost',
                'description': 'Increase movement speed by 10%',
                'cost': 120,
                'max_level': 3,
                'current_level': 0,
                'stat': 'speed_mult',
                'value': 0.1
            },
            {
                'name': 'Starting Gold',
                'description': 'Start each run with +50 gold',
                'cost': 200,
                'max_level': 3,
                'current_level': 0,
                'stat': 'starting_gold',
                'value': 50
            },
            {
                'name': 'Dodge Master',
                'description': 'Reduce dodge cooldown by 20%',
                'cost': 250,
                'max_level': 2,
                'current_level': 0,
                'stat': 'dodge_cooldown_reduction',
                'value': 0.2
            }
        ]

        # Fonts
        self.title_font = pygame.font.Font(None, 60)
        self.upgrade_font = pygame.font.Font(None, 32)
        self.desc_font = pygame.font.Font(None, 22)

    def handle_input(self, event):
        """Handle input"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_w]:
                self.selected_index = (self.selected_index - 1) % len(self.upgrades)
                return 'menu_move'

            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.selected_index = (self.selected_index + 1) % len(self.upgrades)
                return 'menu_move'

            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                return self.purchase_upgrade()

            elif event.key == pygame.K_ESCAPE:
                return 'back'

        return None

    def purchase_upgrade(self):
        """Try to purchase selected upgrade"""
        upgrade = self.upgrades[self.selected_index]

        if upgrade['current_level'] >= upgrade['max_level']:
            return 'max_level'

        cost = upgrade['cost'] * (upgrade['current_level'] + 1)

        if self.game_state.echo_shards >= cost:
            self.game_state.echo_shards -= cost
            upgrade['current_level'] += 1
            self.game_state.save_progress()
            return 'purchase_success'

        return 'insufficient_funds'

    def render(self, screen):
        """Render upgrade menu"""
        width, height = screen.get_size()

        # Background
        screen.fill((20, 18, 28))

        # Title
        title = self.title_font.render("ECHO UPGRADES", True, (150, 200, 255))
        title_rect = title.get_rect(center=(width // 2, 80))
        screen.blit(title, title_rect)

        # Echo shards display
        shards_text = self.upgrade_font.render(
            f"Echo Shards: {self.game_state.echo_shards}",
            True, (255, 215, 0)
        )
        screen.blit(shards_text, (width - 300, 30))

        # Upgrades list
        start_y = 150
        item_height = 100

        for i, upgrade in enumerate(self.upgrades):
            is_selected = (i == self.selected_index)
            y_pos = start_y + i * item_height

            # Background panel
            panel_color = (50, 80, 120) if is_selected else (40, 40, 50)
            panel_rect = pygame.Rect(100, y_pos, width - 200, item_height - 10)
            pygame.draw.rect(screen, panel_color, panel_rect, border_radius=8)

            if is_selected:
                pygame.draw.rect(screen, (100, 150, 200), panel_rect, 3, border_radius=8)

            # Upgrade name
            name_color = (255, 220, 150) if is_selected else (200, 200, 220)
            name_surf = self.upgrade_font.render(upgrade['name'], True, name_color)
            screen.blit(name_surf, (120, y_pos + 15))

            # Level
            level_text = f"Level: {upgrade['current_level']}/{upgrade['max_level']}"
            level_surf = self.desc_font.render(level_text, True, (150, 200, 150))
            screen.blit(level_surf, (width - 250, y_pos + 15))

            # Description
            desc_surf = self.desc_font.render(upgrade['description'], True, (180, 180, 190))
            screen.blit(desc_surf, (120, y_pos + 50))

            # Cost
            if upgrade['current_level'] < upgrade['max_level']:
                cost = upgrade['cost'] * (upgrade['current_level'] + 1)
                can_afford = self.game_state.echo_shards >= cost
                cost_color = (100, 255, 100) if can_afford else (255, 100, 100)
                cost_text = f"Cost: {cost} shards"
            else:
                cost_color = (150, 150, 150)
                cost_text = "MAX LEVEL"

            cost_surf = self.desc_font.render(cost_text, True, cost_color)
            screen.blit(cost_surf, (width - 250, y_pos + 50))

        # Instructions
        inst_font = pygame.font.Font(None, 20)
        instructions = [
            "↑↓ - Navigate",
            "ENTER - Purchase",
            "ESC - Back"
        ]

        inst_y = height - 80
        for inst in instructions:
            inst_surf = inst_font.render(inst, True, (150, 150, 170))
            screen.blit(inst_surf, (width // 2 - 100, inst_y))
            inst_y += 25
