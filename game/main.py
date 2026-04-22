"""
ECHOFRONTIER - Sci-Fantasy Action RPG
Main game entry point
"""

import pygame
import sys
from enum import Enum
from game_state import GameState
from player import Player
from dungeon import DungeonGenerator
from hub import Hub
from ui import UI
from camera import Camera

class GameMode(Enum):
    HUB = 1
    DUNGEON = 2
    DEATH = 3
    MENU = 4

class Game:
    def __init__(self):
        pygame.init()

        # Display settings
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("ECHOFRONTIER")

        # Core systems
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.running = True

        # Game state
        self.game_state = GameState()
        self.mode = GameMode.HUB

        # Initialize systems
        self.camera = Camera(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.player = Player(400, 300, self.game_state)
        self.ui = UI(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.hub = Hub(self.game_state)
        self.dungeon = None

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)

        print("ECHOFRONTIER initialized successfully")
        print("Controls:")
        print("  WASD - Move")
        print("  SPACE - Dodge/Roll")
        print("  LEFT CLICK - Attack")
        print("  Q/E - Abilities")
        print("  I - Inventory")
        print("  ESC - Menu")
        print("  F - Interact")

    def handle_events(self):
        """Handle all input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # UI event handling
            self.ui.handle_event(event)

            # Mode-specific events
            if self.mode == GameMode.HUB:
                self.hub.handle_event(event, self.player)

                # Check if player wants to enter dungeon
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.hub.can_enter_dungeon(self.player):
                            self.enter_dungeon()

            elif self.mode == GameMode.DUNGEON:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i:
                        self.ui.toggle_inventory()
                    elif event.key == pygame.K_ESCAPE:
                        self.mode = GameMode.MENU

    def update(self, dt):
        """Update game logic"""
        if self.mode == GameMode.HUB:
            self.hub.update(dt, self.player)
            self.player.update(dt, [], self.hub.npcs)

        elif self.mode == GameMode.DUNGEON:
            if self.dungeon:
                self.dungeon.update(dt, self.player)
                self.player.update(dt, self.dungeon.get_enemies(), self.dungeon.obstacles)

                # Check if player died
                if self.player.health <= 0:
                    self.handle_death()

                # Check if dungeon cleared
                if self.dungeon.is_cleared():
                    self.complete_dungeon()

        # Update camera to follow player
        self.camera.update(self.player)

    def render(self):
        """Render the game"""
        self.screen.fill((20, 15, 25))  # Dark background

        if self.mode == GameMode.HUB:
            self.hub.render(self.screen, self.camera)
            self.player.render(self.screen, self.camera)

            # Render hub UI
            self.ui.render_hub_info(self.screen, self.player, self.game_state)

        elif self.mode == GameMode.DUNGEON:
            if self.dungeon:
                self.dungeon.render(self.screen, self.camera)
                self.player.render(self.screen, self.camera)

            # Render game UI
            self.ui.render_game_hud(self.screen, self.player)

            if self.ui.show_inventory:
                self.ui.render_inventory(self.screen, self.player)

        elif self.mode == GameMode.DEATH:
            self.render_death_screen()

        elif self.mode == GameMode.MENU:
            self.render_menu()

        pygame.display.flip()

    def enter_dungeon(self):
        """Start a new dungeon run"""
        print(f"Entering dungeon - Biome: {self.game_state.current_biome}")
        self.dungeon = DungeonGenerator(self.game_state)
        self.dungeon.generate()

        # Reset player for run
        self.player.start_dungeon_run(self.dungeon.start_x, self.dungeon.start_y)

        self.mode = GameMode.DUNGEON

    def handle_death(self):
        """Handle player death"""
        print("Player died - Legacy system activated")

        # Drop core fragment
        if self.player.equipped_core_fragment:
            self.game_state.add_legacy_point(
                self.player.x,
                self.player.y,
                self.player.equipped_core_fragment
            )

        # Award some experience even on death
        xp_gain = self.game_state.current_floor * 50
        self.game_state.add_xp(xp_gain)

        self.mode = GameMode.DEATH

    def complete_dungeon(self):
        """Handle successful dungeon completion"""
        print("Dungeon cleared!")

        # Award XP and loot
        xp_gain = self.game_state.current_floor * 200
        self.game_state.add_xp(xp_gain)

        # Grant rewards
        self.game_state.dungeons_cleared += 1

        # Return to hub
        self.return_to_hub()

    def return_to_hub(self):
        """Return player to hub"""
        self.mode = GameMode.HUB
        self.dungeon = None
        self.player.return_to_hub(self.hub.spawn_x, self.hub.spawn_y)

    def render_death_screen(self):
        """Render death screen"""
        # Dark overlay
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((10, 5, 15))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.title_font.render("ECHO FADES", True, (200, 50, 50))
        title_rect = title.get_rect(center=(self.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # Stats
        stats = [
            f"Floor reached: {self.game_state.current_floor}",
            f"Enemies defeated: {self.game_state.enemies_killed_this_run}",
            f"Experience gained: {self.game_state.current_floor * 50}",
            "",
            "Press ENTER to return to hub"
        ]

        y = 300
        for stat in stats:
            text = self.font.render(stat, True, (200, 200, 200))
            text_rect = text.get_rect(center=(self.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 40

        # Check for input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            self.return_to_hub()

    def render_menu(self):
        """Render pause menu"""
        # Dark overlay
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Menu
        title = self.title_font.render("PAUSED", True, (150, 200, 255))
        title_rect = title.get_rect(center=(self.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        options = [
            "Press ESC to resume",
            "Press Q to return to hub"
        ]

        y = 350
        for option in options:
            text = self.font.render(option, True, (200, 200, 200))
            text_rect = text.get_rect(center=(self.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 50

        # Check for input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.mode = GameMode.DUNGEON
        elif keys[pygame.K_q]:
            self.return_to_hub()

    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0  # Delta time in seconds

            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
