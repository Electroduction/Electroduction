"""
Enhanced Village Hub - Large fantasy-style safe zone with shops and NPCs
"""

import pygame
import math
from shop_system import Shop, ShopUI

class VillageNPC:
    """Enhanced NPC with shop functionality"""

    def __init__(self, x, y, name, npc_type, shop_type=None):
        self.x = x
        self.y = y
        self.name = name
        self.npc_type = npc_type  # vendor, quest_giver, lorekeeper, forge, innkeeper
        self.shop_type = shop_type

        self.width = 32
        self.height = 32
        self.color = (100, 150, 200)

        # Shop
        self.shop = None
        if shop_type:
            self.shop = Shop(shop_type)

        # Interaction
        self.interaction_range = 70
        self.in_range = False

        # Dialogue
        self.dialogue = self._get_dialogue()

    def _get_dialogue(self):
        """Get dialogue based on NPC type"""
        dialogues = {
            "lorekeeper": [
                "The Orivians left fragments of their power scattered across the realms.",
                "Each Echo you collect brings you closer to their forgotten truths.",
                "The ruins grow more dangerous the deeper you venture..."
            ],
            "vendor": [
                "Welcome, traveler! Browse my wares.",
                "These items are freshly acquired from the ruins.",
                "Your gold is always welcome here!"
            ],
            "forge": [
                "The Forge can strengthen your Echoes.",
                "Bring me fragments and I'll enhance their power.",
                "Mastery requires dedication and fine materials."
            ],
            "quest_giver": [
                "Dangerous anomalies have been spotted in the void.",
                "We need brave souls to investigate the deeper floors.",
                "Complete my tasks and I'll reward you handsomely."
            ],
            "innkeeper": [
                "Rest here and restore your strength.",
                "A warm meal and a soft bed await.",
                "I've heard tales from other adventurers..."
            ]
        }

        return dialogues.get(self.npc_type, ["Hello, traveler."])

    def update(self, dt, player):
        """Update NPC"""
        # Check if player in range
        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        self.in_range = dist < self.interaction_range

    def interact(self, player, shop_ui=None):
        """Handle interaction"""
        import random
        print(f"{self.name}: {random.choice(self.dialogue)}")

        # Open shop if vendor
        if self.shop and shop_ui:
            shop_ui.open_shop(self.shop)
            from audio_system import get_audio_system
            get_audio_system().play_shop_sound()

class EnhancedVillage:
    """Large fantasy village hub"""

    def __init__(self, game_state):
        self.game_state = game_state

        # Village dimensions - MUCH LARGER
        self.width = 1600
        self.height = 1200

        # Spawn point (center of village)
        self.spawn_x = 800
        self.spawn_y = 600

        # NPCs with shops
        self.npcs = self._create_village_npcs()

        # Dungeon gate
        self.gate = DungeonPortal(800, 200, "Corrupted Void Ruins")

        # Village structures
        self.buildings = self._create_village_buildings()
        self.decorations = self._create_decorations()

        # Shop UI
        self.shop_ui = None

    def _create_village_npcs(self):
        """Create all village NPCs with proper placement"""
        npcs = []

        # WEAPON SHOP - West side
        npcs.append(VillageNPC(
            300, 400,
            "Ironforge the Smith",
            "vendor",
            "Weapon"
        ))

        # ARMOR SHOP - East side
        npcs.append(VillageNPC(
            1300, 400,
            "Steelheart the Armorer",
            "vendor",
            "Armor"
        ))

        # FRAGMENT SHOP - North
        npcs.append(VillageNPC(
            800, 400,
            "Whisper the Echo Merchant",
            "vendor",
            "Fragment"
        ))

        # POTION SHOP - South-West
        npcs.append(VillageNPC(
            400, 800,
            "Mixmaster Elara",
            "vendor",
            "Potion"
        ))

        # FORGE MASTER - Center-North
        npcs.append(VillageNPC(
            800, 550,
            "Kael the Forge Master",
            "forge"
        ))

        # LOREKEEPER - Library (East)
        npcs.append(VillageNPC(
            1200, 600,
            "Archivist Theron",
            "lorekeeper"
        ))

        # QUEST GIVER - Town Square
        npcs.append(VillageNPC(
            700, 700,
            "Scout Commander Mira",
            "quest_giver"
        ))

        # INNKEEPER - South
        npcs.append(VillageNPC(
            800, 900,
            "Innkeeper Brom",
            "innkeeper"
        ))

        return npcs

    def _create_village_buildings(self):
        """Create village buildings"""
        buildings = []

        # Weapon Shop
        buildings.append({
            'x': 200, 'y': 300, 'width': 200, 'height': 180,
            'color': (90, 70, 50), 'label': "WEAPON SHOP",
            'roof_color': (120, 80, 60)
        })

        # Armor Shop
        buildings.append({
            'x': 1200, 'y': 300, 'width': 200, 'height': 180,
            'color': (80, 80, 90), 'label': "ARMOR SHOP",
            'roof_color': (100, 100, 120)
        })

        # Fragment Shop
        buildings.append({
            'x': 700, 'y': 300, 'width': 200, 'height': 150,
            'color': (70, 60, 90), 'label': "ECHO EMPORIUM",
            'roof_color': (100, 80, 130)
        })

        # Potion Shop
        buildings.append({
            'x': 300, 'y': 700, 'width': 180, 'height': 160,
            'color': (60, 90, 70), 'label': "ALCHEMY",
            'roof_color': (80, 120, 90)
        })

        # Forge
        buildings.append({
            'x': 700, 'y': 480, 'width': 200, 'height': 130,
            'color': (100, 50, 40), 'label': "ECHO FORGE",
            'roof_color': (140, 70, 50)
        })

        # Library
        buildings.append({
            'x': 1100, 'y': 500, 'width': 220, 'height': 200,
            'color': (70, 70, 80), 'label': "LIBRARY",
            'roof_color': (90, 90, 100)
        })

        # Town Hall (Quest)
        buildings.append({
            'x': 600, 'y': 600, 'width': 200, 'height': 180,
            'color': (85, 75, 65), 'label': "TOWN HALL",
            'roof_color': (115, 95, 75)
        })

        # Inn
        buildings.append({
            'x': 700, 'y': 800, 'width': 200, 'height': 180,
            'color': (95, 75, 60), 'label': "THE RESTING ECHO",
            'roof_color': (125, 95, 70)
        })

        return buildings

    def _create_decorations(self):
        """Create decorative elements"""
        decorations = []

        # Trees (green circles)
        tree_positions = [
            (150, 200), (1450, 200), (150, 1000), (1450, 1000),
            (500, 200), (1100, 200), (300, 600), (1300, 600),
            (200, 900), (1400, 900)
        ]

        for pos in tree_positions:
            decorations.append({
                'type': 'tree',
                'x': pos[0],
                'y': pos[1],
                'size': 40,
                'color': (60, 120, 60)
            })

        # Fountain (center)
        decorations.append({
            'type': 'fountain',
            'x': 800,
            'y': 700,
            'size': 50,
            'color': (100, 150, 200)
        })

        # Lamp posts
        lamp_positions = [
            (600, 500), (1000, 500), (600, 800), (1000, 800)
        ]

        for pos in lamp_positions:
            decorations.append({
                'type': 'lamp',
                'x': pos[0],
                'y': pos[1],
                'height': 60,
                'color': (255, 220, 150)
            })

        return decorations

    def handle_event(self, event, player):
        """Handle village events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                # Try to interact with NPCs
                for npc in self.npcs:
                    if npc.in_range:
                        npc.interact(player, self.shop_ui)
                        break

    def update(self, dt, player):
        """Update village"""
        # Update NPCs
        for npc in self.npcs:
            npc.update(dt, player)

        # Update gate
        self.gate.update(dt, player)

    def can_enter_dungeon(self, player):
        """Check if player can enter dungeon"""
        return self.gate.in_range

    def render(self, screen, camera):
        """Render village"""
        # Background (cobblestone)
        screen_x, screen_y = camera.world_to_screen(0, 0)

        # Ground
        ground_color = (50, 55, 50)
        pygame.draw.rect(screen, ground_color,
                        (int(screen_x), int(screen_y), self.width, self.height))

        # Pathways
        path_color = (80, 80, 70)

        # Main paths (cross pattern)
        # Horizontal
        path_y_screen, _ = camera.world_to_screen(0, 650)
        pygame.draw.rect(screen, path_color,
                        (int(screen_x), int(path_y_screen), self.width, 100))

        # Vertical
        path_x_screen, _ = camera.world_to_screen(750, 0)
        pygame.draw.rect(screen, path_color,
                        (int(path_x_screen), int(screen_y), 100, self.height))

        # Render decorations (bottom layer)
        for deco in self.decorations:
            self._render_decoration(screen, camera, deco)

        # Render buildings
        for building in self.buildings:
            self._render_building(screen, camera, building)

        # Render NPCs (on top)
        for npc in self.npcs:
            self._render_npc(screen, camera, npc)

        # Render gate
        self.gate.render(screen, camera)

        # Village name
        font = pygame.font.Font(None, 48)
        title = font.render("ECHO SANCTUARY", True, (200, 220, 255))
        screen.blit(title, (20, 20))

    def _render_building(self, screen, camera, building):
        """Render a building"""
        screen_x, screen_y = camera.world_to_screen(building['x'], building['y'])

        # Roof (triangle on top)
        roof_points = [
            (screen_x + building['width'] // 2, screen_y - 20),
            (screen_x, screen_y),
            (screen_x + building['width'], screen_y)
        ]
        pygame.draw.polygon(screen, building['roof_color'], roof_points)

        # Building body
        pygame.draw.rect(screen, building['color'],
                        (int(screen_x), int(screen_y), building['width'], building['height']))

        # Windows
        window_color = (255, 255, 200)
        window_size = 20

        num_windows = building['width'] // 60
        for i in range(num_windows):
            wx = screen_x + 20 + i * 60
            wy = screen_y + 40

            pygame.draw.rect(screen, window_color,
                           (int(wx), int(wy), window_size, window_size))

        # Door
        door_color = (60, 40, 30)
        door_x = screen_x + building['width'] // 2 - 15
        door_y = screen_y + building['height'] - 50

        pygame.draw.rect(screen, door_color, (int(door_x), int(door_y), 30, 50))

        # Building outline
        pygame.draw.rect(screen, (120, 120, 120),
                        (int(screen_x), int(screen_y), building['width'], building['height']), 3)

        # Label
        font = pygame.font.Font(None, 20)
        label = font.render(building['label'], True, (255, 255, 200))
        label_rect = label.get_rect(center=(int(screen_x + building['width'] // 2), int(screen_y - 30)))
        screen.blit(label, label_rect)

    def _render_decoration(self, screen, camera, deco):
        """Render decoration"""
        screen_x, screen_y = camera.world_to_screen(deco['x'], deco['y'])

        if deco['type'] == 'tree':
            # Tree trunk
            trunk_color = (100, 70, 50)
            pygame.draw.rect(screen, trunk_color,
                           (int(screen_x - 5), int(screen_y), 10, 30))

            # Leaves
            pygame.draw.circle(screen, deco['color'], (int(screen_x), int(screen_y - 10)), deco['size'] // 2)

        elif deco['type'] == 'fountain':
            # Base
            pygame.draw.circle(screen, (120, 120, 120), (int(screen_x), int(screen_y)), deco['size'])

            # Water
            pygame.draw.circle(screen, deco['color'], (int(screen_x), int(screen_y)), deco['size'] - 10)

        elif deco['type'] == 'lamp':
            # Post
            pygame.draw.rect(screen, (80, 80, 80),
                           (int(screen_x - 3), int(screen_y), 6, deco['height']))

            # Light
            pygame.draw.circle(screen, deco['color'], (int(screen_x), int(screen_y - deco['height'])), 12)

    def _render_npc(self, screen, camera, npc):
        """Render NPC - using sprite system if available"""
        from sprite_system import SpriteRenderer

        sprite_renderer = SpriteRenderer()
        sprite_renderer.render_npc(screen, camera, npc)

class DungeonPortal:
    """Enhanced dungeon gate"""

    def __init__(self, x, y, biome):
        self.x = x
        self.y = y
        self.biome = biome
        self.width = 80
        self.height = 120
        self.interaction_range = 90
        self.in_range = False

        self.animation_time = 0

    def update(self, dt, player):
        """Update portal"""
        self.animation_time += dt

        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        self.in_range = dist < self.interaction_range

    def render(self, screen, camera):
        """Render portal"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Pulsing portal effect
        pulse = abs(math.sin(self.animation_time * 2)) * 20 + 60

        # Portal glow
        portal_color = (100, 150, 255)

        pygame.draw.ellipse(
            screen, portal_color,
            (int(screen_x - self.width // 2), int(screen_y - pulse // 2),
             self.width, int(pulse))
        )

        # Portal frame (stone archway)
        frame_color = (100, 100, 120)

        # Left pillar
        pygame.draw.rect(screen, frame_color,
                        (int(screen_x - self.width // 2 - 10), int(screen_y - self.height // 2),
                         15, self.height))

        # Right pillar
        pygame.draw.rect(screen, frame_color,
                        (int(screen_x + self.width // 2 - 5), int(screen_y - self.height // 2),
                         15, self.height))

        # Top arch
        pygame.draw.ellipse(screen, frame_color,
                           (int(screen_x - self.width // 2), int(screen_y - self.height // 2 - 20),
                            self.width, 40))

        # Interaction hint
        if self.in_range:
            font = pygame.font.Font(None, 22)
            text = font.render("Press ENTER to enter dungeon", True, (255, 255, 200))
            text_rect = text.get_rect(center=(int(screen_x), int(screen_y - self.height)))
            screen.blit(text, text_rect)

        # Biome name
        font = pygame.font.Font(None, 20)
        biome_text = font.render(self.biome, True, (200, 220, 255))
        biome_rect = biome_text.get_rect(center=(int(screen_x), int(screen_y + self.height // 2 + 30)))
        screen.blit(biome_text, biome_rect)
