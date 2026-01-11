"""
Hub Town - Safe zone with NPCs, vendors, and preparation
"""

import pygame
import random

class NPC:
    """Non-player character"""

    def __init__(self, x, y, name, npc_type, dialogue):
        self.x = x
        self.y = y
        self.name = name
        self.npc_type = npc_type  # vendor, quest_giver, lorekeeper, etc.
        self.dialogue = dialogue

        self.width = 32
        self.height = 32
        self.color = (100, 150, 200)

        # Interaction
        self.interaction_range = 60
        self.in_range = False

    def update(self, dt, player):
        """Update NPC state"""
        # Check if player in range
        dist_x = player.x - self.x
        dist_y = player.y - self.y
        distance = (dist_x**2 + dist_y**2) ** 0.5

        self.in_range = distance < self.interaction_range

    def interact(self, player):
        """Handle interaction"""
        print(f"{self.name}: {random.choice(self.dialogue)}")

        if self.npc_type == "vendor":
            self.open_shop(player)
        elif self.npc_type == "echo_forge":
            self.open_forge(player)

    def open_shop(self, player):
        """Open vendor shop"""
        print("Shop interface would open here")

    def open_forge(self, player):
        """Open Echo Forge"""
        print("Echo Forge interface would open here")

    def render(self, screen, camera):
        """Render NPC"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # NPC body
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.width // 2)

        # Interaction indicator
        if self.in_range:
            # Glowing ring
            pygame.draw.circle(screen, (200, 200, 100), (int(screen_x), int(screen_y)),
                             self.interaction_range, 2)

            # "F to interact" text
            font = pygame.font.Font(None, 18)
            text = font.render("Press F", True, (255, 255, 200))
            text_rect = text.get_rect(center=(int(screen_x), int(screen_y - 40)))
            screen.blit(text, text_rect)

        # Name
        font = pygame.font.Font(None, 16)
        name_text = font.render(self.name, True, (220, 220, 220))
        name_rect = name_text.get_rect(center=(int(screen_x), int(screen_y - 25)))
        screen.blit(name_text, name_rect)

class DungeonGate:
    """Gate to enter dungeons"""

    def __init__(self, x, y, biome):
        self.x = x
        self.y = y
        self.biome = biome
        self.width = 60
        self.height = 80
        self.interaction_range = 80
        self.in_range = False

    def update(self, dt, player):
        """Update gate"""
        dist_x = player.x - self.x
        dist_y = player.y - self.y
        distance = (dist_x**2 + dist_y**2) ** 0.5

        self.in_range = distance < self.interaction_range

    def render(self, screen, camera):
        """Render gate"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Gate portal
        import math
        import time

        pulse = math.sin(time.time() * 2) * 10 + 50

        # Portal glow
        pygame.draw.ellipse(
            screen,
            (100, 150, 255),
            (int(screen_x - self.width // 2), int(screen_y - self.height // 2),
             self.width, int(pulse))
        )

        # Gate frame
        pygame.draw.rect(
            screen,
            (80, 80, 100),
            (int(screen_x - self.width // 2), int(screen_y - self.height // 2),
             self.width, self.height),
            4
        )

        # Interaction hint
        if self.in_range:
            font = pygame.font.Font(None, 20)
            text = font.render("Press ENTER to enter", True, (255, 255, 200))
            text_rect = text.get_rect(center=(int(screen_x), int(screen_y - self.height)))
            screen.blit(text, text_rect)

        # Biome name
        font = pygame.font.Font(None, 18)
        biome_text = font.render(self.biome, True, (200, 200, 255))
        biome_rect = biome_text.get_rect(center=(int(screen_x), int(screen_y + self.height // 2 + 20)))
        screen.blit(biome_text, biome_rect)

class Hub:
    """Hub town area"""

    def __init__(self, game_state):
        self.game_state = game_state

        # Hub dimensions
        self.width = 800
        self.height = 600

        # Spawn point
        self.spawn_x = 400
        self.spawn_y = 300

        # NPCs
        self.npcs = self._create_npcs()

        # Dungeon gate
        self.gate = DungeonGate(400, 100, game_state.current_biome)

        # Decorations
        self.buildings = self._create_buildings()

    def _create_npcs(self):
        """Create hub NPCs"""
        npcs = []

        # Whispering Archivist - Lorekeeper
        npcs.append(NPC(
            200, 200,
            "Whispering Archivist",
            "lorekeeper",
            [
                "The Orivians left behind fragments of their memories...",
                "Each Echo contains a story waiting to be discovered.",
                "The ruins shift and change, as if alive with forgotten purpose."
            ]
        ))

        # Vendor
        npcs.append(NPC(
            600, 200,
            "Fragment Merchant",
            "vendor",
            [
                "Welcome, Echo-Seeker! I have rare goods for sale.",
                "These fragments were pulled from the deepest ruins.",
                "Your shards are always welcome here."
            ]
        ))

        # Echo Forge Master
        npcs.append(NPC(
            400, 450,
            "Forge Master Kael",
            "echo_forge",
            [
                "The Forge can reshape your Echoes into something greater.",
                "Bring me fragments and I'll unlock their true potential.",
                "Mastery comes through refinement and dedication."
            ]
        ))

        # Quest Giver
        npcs.append(NPC(
            100, 400,
            "Scout Mira",
            "quest_giver",
            [
                "Strange anomalies have been spotted in the Void Ruins.",
                "If you venture there, be careful - the corruption spreads.",
                "We need brave souls to investigate the deeper floors."
            ]
        ))

        return npcs

    def _create_buildings(self):
        """Create decorative buildings"""
        buildings = [
            {'x': 150, 'y': 150, 'width': 120, 'height': 100, 'color': (70, 70, 90)},
            {'x': 550, 'y': 150, 'width': 120, 'height': 100, 'color': (70, 70, 90)},
            {'x': 350, 'y': 400, 'width': 120, 'height': 100, 'color': (80, 70, 90)},
        ]
        return buildings

    def handle_event(self, event, player):
        """Handle hub events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                # Try to interact with NPCs
                for npc in self.npcs:
                    if npc.in_range:
                        npc.interact(player)
                        break

    def update(self, dt, player):
        """Update hub"""
        # Update NPCs
        for npc in self.npcs:
            npc.update(dt, player)

        # Update gate
        self.gate.update(dt, player)

    def can_enter_dungeon(self, player):
        """Check if player can enter dungeon"""
        return self.gate.in_range

    def render(self, screen, camera):
        """Render hub"""
        # Background
        hub_color = (30, 35, 45)

        # Floor
        screen_x, screen_y = camera.world_to_screen(0, 0)
        pygame.draw.rect(screen, hub_color, (int(screen_x), int(screen_y), self.width, self.height))

        # Buildings
        for building in self.buildings:
            screen_x, screen_y = camera.world_to_screen(building['x'], building['y'])
            pygame.draw.rect(
                screen,
                building['color'],
                (int(screen_x), int(screen_y), building['width'], building['height'])
            )

            # Building outline
            pygame.draw.rect(
                screen,
                (100, 100, 120),
                (int(screen_x), int(screen_y), building['width'], building['height']),
                2
            )

        # NPCs
        for npc in self.npcs:
            npc.render(screen, camera)

        # Gate
        self.gate.render(screen, camera)

        # Hub title
        font = pygame.font.Font(None, 32)
        title = font.render("ECHO SANCTUARY", True, (150, 200, 255))
        screen.blit(title, (20, 20))
