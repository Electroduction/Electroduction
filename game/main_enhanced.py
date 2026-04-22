"""
ECHOFRONTIER - Enhanced Main Game
Integrated: Combat system, Sprites, Audio, Shops, Enhanced village, Projectiles
"""

import pygame
import sys
from enum import Enum

# Core systems
from game_state import GameState
from player import Player
from camera import Camera
from ui import UI

# Enhanced systems
from combat_system import CombatSystem, Projectile
from enemies_enhanced import create_enemy
from bosses import create_boss
from sprite_system import SpriteRenderer
from audio_system import get_audio_system
from village_hub import EnhancedVillage
from shop_system import ShopUI

# Original systems (for dungeon)
from dungeon import DungeonGenerator

class GameMode(Enum):
    HUB = 1
    DUNGEON = 2
    DEATH = 3
    MENU = 4

class EnhancedGame:
    def __init__(self):
        pygame.init()

        # Display
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("ECHOFRONTIER - Enhanced Edition")

        # Core
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.running = True

        # NEW: Combat system
        self.combat_system = CombatSystem()
        self.projectiles = []

        # Game state
        self.game_state = GameState()
        self.mode = GameMode.HUB

        # Initialize systems
        self.camera = Camera(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.player = Player(800, 600, self.game_state, self.combat_system)
        self.ui = UI(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        # NEW: Enhanced systems
        self.sprite_renderer = SpriteRenderer()
        self.audio = get_audio_system()
        self.village = EnhancedVillage(self.game_state)
        self.shop_ui = ShopUI(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        # Connect shop UI to village
        self.village.shop_ui = self.shop_ui

        self.dungeon = None

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)

        print("=" * 50)
        print("ECHOFRONTIER - ENHANCED EDITION")
        print("=" * 50)
        print("\nNEW FEATURES:")
        print("  ✓ Fixed combat system - enemies can now be killed!")
        print("  ✓ Enhanced sprites and animations")
        print("  ✓ Audio system with sound effects")
        print("  ✓ Currency (Gold) system")
        print("  ✓ Working shops (Weapon, Armor, Fragment, Potion)")
        print("  ✓ Large fantasy village hub")
        print("  ✓ 6 enemy types with unique abilities:")
        print("    - Void Archer (ranged)")
        print("    - Blood Berserker (enrages)")
        print("    - Shadow Stalker (invisibility)")
        print("    - Toxic Spitter (poison)")
        print("    - Phase Walker (teleports)")
        print("  ✓ Projectile system")
        print("  ✓ Status effects (poison, slow, speed, regen)")
        print("  ✓ Harder difficulty")
        print("\nCONTROLS:")
        print("  WASD - Move")
        print("  SPACE - Dodge")
        print("  LEFT CLICK - Attack")
        print("  Q/E - Abilities")
        print("  F - Interact with NPCs/Shops")
        print("  I - Inventory")
        print("  ESC - Menu")
        print("  ENTER - Enter Dungeon (at portal)")
        print("\nVILLAGE SHOPS:")
        print("  - Ironforge (Weapons)")
        print("  - Steelheart (Armor)")
        print("  - Whisper (Echo Fragments)")
        print("  - Mixmaster Elara (Potions)")
        print("=" * 50)

    def handle_events(self):
        """Handle all input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Shop UI has priority
            if self.shop_ui.is_open:
                self.shop_ui.handle_event(event, self.player)
                continue

            # UI event handling
            self.ui.handle_event(event)

            # Mode-specific events
            if self.mode == GameMode.HUB:
                self.village.handle_event(event, self.player)

                # Check if player wants to enter dungeon
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.village.can_enter_dungeon(self.player):
                            self.enter_dungeon()

            elif self.mode == GameMode.DUNGEON:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i:
                        self.ui.toggle_inventory()
                    elif event.key == pygame.K_ESCAPE:
                        self.mode = GameMode.MENU

    def update(self, dt):
        """Update game logic"""
        # Update sprite renderer
        self.sprite_renderer.update(dt)

        if self.mode == GameMode.HUB:
            self.village.update(dt, self.player)
            self.player.update(dt, [], [])

        elif self.mode == GameMode.DUNGEON:
            if self.dungeon:
                # Get enemies
                enemies = self.dungeon.get_enemies()

                # Update combat system
                self.combat_system.update(dt, enemies, self.player)

                # Update projectiles
                for projectile in self.projectiles[:]:
                    projectile.update(dt, enemies, self.player)

                    if not projectile.alive:
                        self.projectiles.remove(projectile)

                # Update dungeon
                self.dungeon.update(dt, self.player)

                # Update player
                self.player.update(dt, enemies, self.dungeon.obstacles)

                # Check player death
                if self.player.health <= 0:
                    self.handle_death()

                # Check dungeon cleared
                if self.dungeon.is_cleared():
                    self.complete_dungeon()

        # Update camera
        self.camera.update(self.player)

    def render(self):
        """Render the game"""
        self.screen.fill((20, 15, 25))

        if self.mode == GameMode.HUB:
            self.village.render(self.screen, self.camera)
            self.sprite_renderer.render_player(self.screen, self.camera, self.player)

            # Render player particles
            self.player.particles.render(self.screen, self.camera)

            # Render hub UI
            self.ui.render_hub_info(self.screen, self.player, self.game_state)

            # Render shop UI
            if self.shop_ui.is_open:
                self.shop_ui.render(self.screen, self.player)

        elif self.mode == GameMode.DUNGEON:
            if self.dungeon:
                self.dungeon.render(self.screen, self.camera)

                # Render enemies with sprites
                for room in self.dungeon.rooms:
                    for enemy in room.enemies:
                        if enemy.alive:
                            self.sprite_renderer.render_enemy(self.screen, self.camera, enemy)

                # Render projectiles
                for projectile in self.projectiles:
                    projectile.render(self.screen, self.camera)

                # Render player with sprites
                self.sprite_renderer.render_player(self.screen, self.camera, self.player)

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
        print(f"\n{'='*50}")
        print(f"ENTERING DUNGEON - {self.game_state.current_biome}")
        print(f"Player Gold: {self.player.gold}")
        print(f"{'='*50}\n")

        # Create HARDER dungeon
        self.dungeon = self._create_enhanced_dungeon()

        # Reset player for run
        self.player.start_dungeon_run(self.dungeon.start_x, self.dungeon.start_y)

        # Clear projectiles
        self.projectiles.clear()
        self.combat_system.clear()

        self.mode = GameMode.DUNGEON

        self.audio.play_menu_sound()

    def _create_enhanced_dungeon(self):
        """Create harder dungeon with enhanced enemies"""
        # Use original dungeon structure but replace enemies
        dungeon = DungeonGenerator(self.game_state)
        dungeon.generate()

        # Replace enemies with enhanced versions
        enhanced_enemy_types = [
            "Void Archer",
            "Blood Berserker",
            "Shadow Stalker",
            "Toxic Spitter",
            "Phase Walker",
            "Basic"
        ]

        for room in dungeon.rooms:
            if room.room_type == "combat":
                # Clear old enemies
                room.enemies.clear()

                # Add MORE and HARDER enemies
                num_enemies = 5 + self.game_state.current_floor * 2

                for _ in range(num_enemies):
                    # Random position in room
                    enemy_x = room.x + (room.width * 0.3) + (room.width * 0.4 * random.random())
                    enemy_y = room.y + (room.height * 0.3) + (room.height * 0.4 * random.random())

                    # Random enhanced enemy type
                    import random
                    enemy_type = random.choice(enhanced_enemy_types)

                    enemy = create_enemy(enemy_type, enemy_x, enemy_y, self.combat_system)

                    # Scale with floor
                    enemy.max_health *= (1 + self.game_state.current_floor * 0.3)
                    enemy.health = enemy.max_health
                    enemy.damage *= (1 + self.game_state.current_floor * 0.2)

                    # Give archers projectile list
                    if "Archer" in enemy_type:
                        enemy.projectiles = self.projectiles

                    room.enemies.append(enemy)

            elif room.room_type == "boss":
                # Enhanced boss
                for enemy in room.enemies:
                    enemy.max_health *= (1 + self.game_state.current_floor * 0.5)
                    enemy.health = enemy.max_health
                    enemy.damage *= (1 + self.game_state.current_floor * 0.3)

        print(f"Dungeon generated: {len(dungeon.rooms)} rooms, {len(dungeon.get_enemies())} enemies")

        return dungeon

    def handle_death(self):
        """Handle player death"""
        print("\n" + "="*50)
        print("PLAYER DEFEATED")
        print("="*50)

        # Drop core fragment
        if self.player.equipped_core_fragment:
            self.game_state.add_legacy_point(
                self.player.x, self.player.y,
                self.player.equipped_core_fragment
            )

        # Award consolation XP
        xp_gain = self.game_state.current_floor * 50
        self.game_state.add_xp(xp_gain)

        self.mode = GameMode.DEATH

        self.audio.play_death_sound()

    def complete_dungeon(self):
        """Handle successful dungeon completion"""
        print("\n" + "="*50)
        print("DUNGEON CLEARED!")
        print("="*50)

        # Award XP and loot
        xp_gain = self.game_state.current_floor * 300
        self.game_state.add_xp(xp_gain)
        self.player.add_xp(xp_gain)

        # Gold reward
        gold_reward = 50 + self.game_state.current_floor * 30
        self.player.gold += gold_reward

        print(f"Gained {xp_gain} XP and {gold_reward} gold!")

        # Grant rewards
        self.game_state.dungeons_cleared += 1

        # Return to hub
        self.return_to_hub()

    def return_to_hub(self):
        """Return player to hub"""
        self.mode = GameMode.HUB
        self.dungeon = None
        self.projectiles.clear()
        self.combat_system.clear()

        self.player.return_to_hub(self.village.spawn_x, self.village.spawn_y)

        # Save progress
        self.game_state.save_progress()

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
            "Press ENTER to return to village"
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
            "Press Q to return to village"
        ]

        y = 350
        for option in options:
            text = self.font.render(option, True, (200, 200, 200))
            text_rect = text.get_rect(center=(self.SCREEN_WIDTH // 2, y))
            screen.blit(text, text_rect)
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
            dt = self.clock.tick(self.FPS) / 1000.0

            self.handle_events()
            self.update(dt)
            self.render()

        # Cleanup
        self.game_state.save_progress()
        pygame.quit()
        sys.exit()

def main():
    game = EnhancedGame()
    game.run()

if __name__ == "__main__":
    import random  # Import for dungeon generation
    main()
