"""
Procedural Dungeon Generation - Biomes, rooms, and encounters
"""

import pygame
import random
import math
from enemies import create_enemy
from bosses import create_boss
from items import LootGenerator

class Room:
    """Individual dungeon room"""

    def __init__(self, x, y, width, height, room_type="combat"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.room_type = room_type  # combat, treasure, event, boss

        self.cleared = False
        self.enemies = []
        self.loot = []
        self.obstacles = []

    def get_center(self):
        """Get room center position"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains_point(self, px, py):
        """Check if point is in room"""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

class BiomeData:
    """Biome visual and gameplay data"""

    def __init__(self, name, primary_color, secondary_color, enemy_types):
        self.name = name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.enemy_types = enemy_types
        self.hazards = []

class DungeonGenerator:
    """Generates procedural dungeons"""

    def __init__(self, game_state):
        self.game_state = game_state
        self.biome = game_state.current_biome

        # Biome definitions
        self.biomes = {
            "Corrupted Void Ruins": BiomeData(
                "Corrupted Void Ruins",
                (60, 40, 80),
                (40, 30, 60),
                ["Lantern Crawler", "Echo Leech", "Phase Blade"]
            ),
            "Lush Floating Forests": BiomeData(
                "Lush Floating Forests",
                (40, 80, 50),
                (30, 60, 40),
                ["Thornstalker", "Basic", "Basic"]
            ),
            "Crystallized Reality Tears": BiomeData(
                "Crystallized Reality Tears",
                (80, 120, 140),
                (60, 100, 120),
                ["Time Shard", "Phase Blade", "Basic"]
            )
        }

        self.current_biome_data = self.biomes.get(
            self.biome,
            self.biomes["Corrupted Void Ruins"]
        )

        # Dungeon structure
        self.rooms = []
        self.corridors = []
        self.obstacles = []

        # Generation parameters
        self.num_rooms = 6 + game_state.current_floor * 2
        self.room_min_size = 300
        self.room_max_size = 500

        # Spawns
        self.start_x = 0
        self.start_y = 0
        self.boss_room = None

        # Loot generator
        self.loot_gen = LootGenerator()

    def generate(self):
        """Generate the dungeon"""
        print(f"Generating dungeon: {self.biome}, Floor {self.game_state.current_floor}")

        # Generate rooms
        self._generate_rooms()

        # Connect rooms
        self._generate_corridors()

        # Populate rooms
        self._populate_rooms()

        # Create obstacles
        self._generate_obstacles()

        # Set spawn point
        if self.rooms:
            start_room = self.rooms[0]
            self.start_x, self.start_y = start_room.get_center()

    def _generate_rooms(self):
        """Generate room layout"""
        # Simple grid-based generation with randomization
        grid_size = 3
        room_spacing = 600

        for i in range(min(self.num_rooms, grid_size * grid_size)):
            grid_x = i % grid_size
            grid_y = i // grid_size

            # Add randomization
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-100, 100)

            x = grid_x * room_spacing + offset_x
            y = grid_y * room_spacing + offset_y

            width = random.randint(self.room_min_size, self.room_max_size)
            height = random.randint(self.room_min_size, self.room_max_size)

            # Determine room type
            if i == 0:
                room_type = "start"
            elif i == self.num_rooms - 1 or i == len(range(min(self.num_rooms, grid_size * grid_size))) - 1:
                room_type = "boss"
            elif random.random() < 0.2:
                room_type = "treasure"
            else:
                room_type = "combat"

            room = Room(x, y, width, height, room_type)
            self.rooms.append(room)

            if room_type == "boss":
                self.boss_room = room

    def _generate_corridors(self):
        """Connect rooms with corridors"""
        # Simple connection - each room connects to next
        for i in range(len(self.rooms) - 1):
            room1 = self.rooms[i]
            room2 = self.rooms[i + 1]

            center1 = room1.get_center()
            center2 = room2.get_center()

            self.corridors.append((center1, center2))

    def _populate_rooms(self):
        """Add enemies and loot to rooms"""
        for room in self.rooms:
            if room.room_type == "combat":
                # Spawn enemies
                num_enemies = random.randint(3, 6) + self.game_state.current_floor

                for _ in range(num_enemies):
                    # Random position in room
                    enemy_x = room.x + random.randint(50, room.width - 50)
                    enemy_y = room.y + random.randint(50, room.height - 50)

                    # Random enemy type from biome
                    enemy_type = random.choice(self.current_biome_data.enemy_types)

                    enemy = create_enemy(enemy_type, enemy_x, enemy_y)
                    room.enemies.append(enemy)

            elif room.room_type == "boss":
                # Spawn boss
                boss_x, boss_y = room.get_center()

                # Choose boss based on biome
                boss_types = {
                    "Corrupted Void Ruins": "Broken Aegis",
                    "Lush Floating Forests": "Lyra's Eclipse",
                    "Crystallized Reality Tears": "Chronomancer's Core"
                }

                boss_type = boss_types.get(self.biome, "Broken Aegis")
                boss = create_boss(boss_type, boss_x, boss_y)
                room.enemies.append(boss)

            elif room.room_type == "treasure":
                # Spawn loot
                num_items = random.randint(2, 4)

                for _ in range(num_items):
                    loot_x = room.x + random.randint(50, room.width - 50)
                    loot_y = room.y + random.randint(50, room.height - 50)

                    item = self.loot_gen.generate_loot_drop(
                        self.game_state.current_floor,
                        self.biome
                    )

                    room.loot.append({
                        'item': item,
                        'x': loot_x,
                        'y': loot_y,
                        'collected': False
                    })

    def _generate_obstacles(self):
        """Generate obstacles in rooms"""
        for room in self.rooms:
            # Add some obstacles
            num_obstacles = random.randint(2, 5)

            for _ in range(num_obstacles):
                obs_x = room.x + random.randint(50, room.width - 50)
                obs_y = room.y + random.randint(50, room.height - 50)
                obs_size = random.randint(30, 60)

                self.obstacles.append({
                    'x': obs_x,
                    'y': obs_y,
                    'size': obs_size
                })

    def update(self, dt, player):
        """Update dungeon state"""
        # Update enemies
        for room in self.rooms:
            if not room.cleared:
                # Check if player in room
                if room.contains_point(player.x, player.y):
                    # Update enemies
                    for enemy in room.enemies:
                        if enemy.alive:
                            enemy.update(dt, player)

                            # Check player attacks
                            if hasattr(player, 'last_attack_time') and player.last_attack_time > 0:
                                player.last_attack_time -= dt

                                if hasattr(player, 'last_attack_pos'):
                                    attack_x, attack_y = player.last_attack_pos
                                    dist = math.sqrt((enemy.x - attack_x)**2 + (enemy.y - attack_y)**2)

                                    if dist < 40:  # Attack radius
                                        enemy.take_damage(player.attack_damage, player)
                                        player.last_attack_time = 0

                            # Check ability damage
                            if hasattr(player, 'last_ability_damage') and hasattr(player, 'last_ability_range'):
                                dist = math.sqrt((enemy.x - player.x)**2 + (enemy.y - player.y)**2)

                                if dist < player.last_ability_range:
                                    enemy.take_damage(player.last_ability_damage, player)

                                # Clear ability damage after checking all enemies
                                player.last_ability_damage = 0

                    # Check if room cleared
                    room.enemies = [e for e in room.enemies if e.alive]

                    if len(room.enemies) == 0:
                        room.cleared = True
                        print(f"Room cleared! Type: {room.room_type}")

                        # Grant XP
                        xp_reward = 50 * self.game_state.current_floor
                        player.add_xp(xp_reward)
                        self.game_state.add_xp(xp_reward)

            # Check loot collection
            for loot_data in room.loot:
                if not loot_data['collected']:
                    dist = math.sqrt((player.x - loot_data['x'])**2 + (player.y - loot_data['y'])**2)

                    if dist < 40:
                        # Collect loot
                        loot_data['collected'] = True
                        print(f"Collected: {loot_data['item'].name} ({loot_data['item'].rarity})")

    def get_enemies(self):
        """Get all living enemies in dungeon"""
        enemies = []
        for room in self.rooms:
            enemies.extend([e for e in room.enemies if e.alive])
        return enemies

    def is_cleared(self):
        """Check if dungeon is complete"""
        if self.boss_room:
            return self.boss_room.cleared
        return False

    def render(self, screen, camera):
        """Render dungeon"""
        # Render rooms
        for room in self.rooms:
            screen_x, screen_y = camera.world_to_screen(room.x, room.y)

            # Room color based on type and state
            if room.cleared:
                color = (30, 50, 30)
            elif room.room_type == "boss":
                color = (80, 30, 30)
            elif room.room_type == "treasure":
                color = (60, 60, 30)
            else:
                color = self.current_biome_data.primary_color

            # Room floor
            pygame.draw.rect(
                screen,
                color,
                (int(screen_x), int(screen_y), room.width, room.height)
            )

            # Room walls
            pygame.draw.rect(
                screen,
                self.current_biome_data.secondary_color,
                (int(screen_x), int(screen_y), room.width, room.height),
                4
            )

        # Render corridors
        for corridor in self.corridors:
            start_screen = camera.world_to_screen(corridor[0][0], corridor[0][1])
            end_screen = camera.world_to_screen(corridor[1][0], corridor[1][1])

            pygame.draw.line(
                screen,
                self.current_biome_data.primary_color,
                start_screen,
                end_screen,
                20
            )

        # Render obstacles
        for obstacle in self.obstacles:
            screen_x, screen_y = camera.world_to_screen(obstacle['x'], obstacle['y'])

            pygame.draw.circle(
                screen,
                (60, 60, 70),
                (int(screen_x), int(screen_y)),
                obstacle['size'] // 2
            )

        # Render loot
        for room in self.rooms:
            for loot_data in room.loot:
                if not loot_data['collected']:
                    screen_x, screen_y = camera.world_to_screen(loot_data['x'], loot_data['y'])

                    # Pulsing glow
                    import time
                    pulse = math.sin(time.time() * 3) * 5 + 15

                    color = loot_data['item'].get_rarity_color()

                    pygame.draw.circle(
                        screen,
                        color,
                        (int(screen_x), int(screen_y)),
                        int(pulse)
                    )

        # Render enemies
        for room in self.rooms:
            for enemy in room.enemies:
                if enemy.alive:
                    enemy.render(screen, camera)
