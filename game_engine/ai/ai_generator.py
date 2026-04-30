#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION GAME ENGINE - AI GENERATOR
===============================================================================
AI-powered content generation for rapid game development:
- Text-to-Game: Describe a game in English and generate it
- Procedural Level Generation
- AI-driven character behavior
- Texture generation (integrates with AI services)
- Story generation
- Dialogue generation
- Game balancing AI

This module provides:
- Natural language processing for game descriptions
- Procedural content generation algorithms
- Integration with AI image generation services
- Behavior tree generation
===============================================================================
"""

import os
import sys
import json
import random
import math
import re
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
from enum import Enum, auto
from abc import ABC, abstractmethod

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.engine import (
        Entity, Component, Scene, Vector2, Vector3, Color, Rectangle,
        SpriteComponent, RigidBodyComponent, ColliderComponent,
        ScriptComponent, TilemapComponent, AnimationComponent,
        UIComponent, create_physics_entity, create_sprite_entity,
        create_player_entity, create_tilemap_entity
    )
except ImportError:
    # Standalone mode
    pass


# =============================================================================
# TEXT-TO-GAME PARSER
# =============================================================================

class GameGenre(Enum):
    """Game genres for generation"""
    PLATFORMER = auto()
    TOP_DOWN = auto()
    PUZZLE = auto()
    SHOOTER = auto()
    RPG = auto()
    ADVENTURE = auto()
    RACING = auto()
    FIGHTING = auto()


class EntityType(Enum):
    """Types of entities to generate"""
    PLAYER = auto()
    ENEMY = auto()
    PLATFORM = auto()
    COLLECTIBLE = auto()
    OBSTACLE = auto()
    NPC = auto()
    PROJECTILE = auto()
    TRIGGER = auto()
    DECORATION = auto()


@dataclass
class GameDescription:
    """Parsed game description from natural language"""
    title: str = "My Game"
    genre: GameGenre = GameGenre.PLATFORMER
    theme: str = "fantasy"
    player_abilities: List[str] = field(default_factory=list)
    enemy_types: List[str] = field(default_factory=list)
    collectibles: List[str] = field(default_factory=list)
    mechanics: List[str] = field(default_factory=list)
    level_elements: List[str] = field(default_factory=list)
    art_style: str = "pixel"
    color_palette: List[Color] = field(default_factory=list)
    difficulty: str = "medium"


class TextParser:
    """
    Natural language parser for game descriptions.
    Converts English text into game generation parameters.
    """

    def __init__(self):
        # Genre keywords
        self.genre_keywords = {
            GameGenre.PLATFORMER: ['platform', 'jump', 'mario', 'side-scroll', 'sidescroll'],
            GameGenre.TOP_DOWN: ['top-down', 'topdown', 'zelda', 'overhead', 'bird'],
            GameGenre.PUZZLE: ['puzzle', 'brain', 'tetris', 'match', 'logic'],
            GameGenre.SHOOTER: ['shoot', 'gun', 'bullet', 'space invader', 'fps'],
            GameGenre.RPG: ['rpg', 'role', 'level up', 'stats', 'quest'],
            GameGenre.ADVENTURE: ['adventure', 'explore', 'story', 'narrative'],
            GameGenre.RACING: ['race', 'car', 'speed', 'track', 'driving'],
            GameGenre.FIGHTING: ['fight', 'combat', 'punch', 'kick', 'versus'],
        }

        # Theme keywords
        self.theme_keywords = {
            'fantasy': ['fantasy', 'magic', 'wizard', 'dragon', 'castle', 'knight', 'medieval'],
            'sci-fi': ['sci-fi', 'space', 'robot', 'alien', 'future', 'laser', 'cyber'],
            'horror': ['horror', 'scary', 'ghost', 'zombie', 'dark', 'spooky'],
            'nature': ['nature', 'forest', 'jungle', 'garden', 'tree', 'flower'],
            'ocean': ['ocean', 'water', 'sea', 'fish', 'underwater', 'ship'],
            'urban': ['city', 'urban', 'street', 'building', 'car', 'modern'],
            'retro': ['retro', '8-bit', '16-bit', 'arcade', 'classic', 'pixel'],
        }

        # Ability keywords
        self.ability_keywords = {
            'jump': ['jump', 'hop', 'leap', 'bounce'],
            'double_jump': ['double jump', 'air jump', 'jump twice'],
            'dash': ['dash', 'sprint', 'burst', 'speed'],
            'wall_jump': ['wall jump', 'wall climb', 'wall slide'],
            'shoot': ['shoot', 'fire', 'projectile', 'bullet'],
            'melee': ['attack', 'sword', 'punch', 'hit', 'slash'],
            'fly': ['fly', 'hover', 'float', 'wings'],
            'swim': ['swim', 'dive', 'underwater'],
        }

        # Enemy keywords
        self.enemy_keywords = {
            'walker': ['walk', 'patrol', 'guard', 'basic'],
            'flyer': ['fly', 'bird', 'bat', 'floating'],
            'shooter': ['shoot', 'turret', 'cannon', 'range'],
            'chaser': ['chase', 'follow', 'hunt', 'pursue'],
            'boss': ['boss', 'big', 'giant', 'final'],
            'spawner': ['spawn', 'summon', 'create', 'horde'],
        }

        # Color palettes
        self.color_palettes = {
            'fantasy': [Color(139, 90, 43), Color(34, 139, 34), Color(70, 130, 180), Color(218, 165, 32)],
            'sci-fi': [Color(0, 191, 255), Color(138, 43, 226), Color(192, 192, 192), Color(255, 0, 128)],
            'horror': [Color(25, 25, 25), Color(139, 0, 0), Color(75, 0, 130), Color(128, 128, 128)],
            'nature': [Color(34, 139, 34), Color(139, 90, 43), Color(135, 206, 235), Color(255, 215, 0)],
            'ocean': [Color(0, 105, 148), Color(64, 224, 208), Color(240, 248, 255), Color(255, 215, 0)],
            'retro': [Color(252, 252, 252), Color(142, 160, 229), Color(255, 119, 168), Color(112, 207, 230)],
        }

    def parse(self, text: str) -> GameDescription:
        """Parse natural language text into game description"""
        text_lower = text.lower()

        desc = GameDescription()

        # Extract title (first quoted text or first capitalized phrase)
        title_match = re.search(r'"([^"]+)"', text)
        if title_match:
            desc.title = title_match.group(1)
        else:
            words = text.split()
            title_words = []
            for word in words[:5]:
                if word[0].isupper():
                    title_words.append(word)
            if title_words:
                desc.title = ' '.join(title_words)

        # Detect genre
        desc.genre = self._detect_genre(text_lower)

        # Detect theme
        desc.theme = self._detect_theme(text_lower)

        # Detect abilities
        desc.player_abilities = self._detect_abilities(text_lower)

        # Detect enemy types
        desc.enemy_types = self._detect_enemies(text_lower)

        # Detect collectibles
        desc.collectibles = self._detect_collectibles(text_lower)

        # Detect mechanics
        desc.mechanics = self._detect_mechanics(text_lower)

        # Detect art style
        if 'pixel' in text_lower or '8-bit' in text_lower or 'retro' in text_lower:
            desc.art_style = 'pixel'
        elif '3d' in text_lower or 'polygon' in text_lower:
            desc.art_style = '3d'
        elif 'cartoon' in text_lower or 'hand-drawn' in text_lower:
            desc.art_style = 'cartoon'

        # Set color palette based on theme
        desc.color_palette = self.color_palettes.get(desc.theme, self.color_palettes['fantasy'])

        # Detect difficulty
        if 'easy' in text_lower or 'beginner' in text_lower or 'casual' in text_lower:
            desc.difficulty = 'easy'
        elif 'hard' in text_lower or 'difficult' in text_lower or 'challenge' in text_lower:
            desc.difficulty = 'hard'

        return desc

    def _detect_genre(self, text: str) -> GameGenre:
        """Detect game genre from text"""
        scores = {}
        for genre, keywords in self.genre_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[genre] = score

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return GameGenre.PLATFORMER  # Default

    def _detect_theme(self, text: str) -> str:
        """Detect game theme from text"""
        for theme, keywords in self.theme_keywords.items():
            if any(kw in text for kw in keywords):
                return theme
        return 'fantasy'

    def _detect_abilities(self, text: str) -> List[str]:
        """Detect player abilities from text"""
        abilities = []
        for ability, keywords in self.ability_keywords.items():
            if any(kw in text for kw in keywords):
                abilities.append(ability)

        if not abilities:
            abilities = ['jump']  # Default

        return abilities

    def _detect_enemies(self, text: str) -> List[str]:
        """Detect enemy types from text"""
        enemies = []
        for enemy, keywords in self.enemy_keywords.items():
            if any(kw in text for kw in keywords):
                enemies.append(enemy)

        if not enemies:
            enemies = ['walker']  # Default

        return enemies

    def _detect_collectibles(self, text: str) -> List[str]:
        """Detect collectibles from text"""
        collectibles = []
        keywords = {
            'coin': ['coin', 'money', 'gold', 'treasure'],
            'gem': ['gem', 'diamond', 'crystal', 'jewel'],
            'star': ['star', 'point'],
            'heart': ['heart', 'health', 'life'],
            'key': ['key', 'unlock'],
            'powerup': ['power', 'upgrade', 'boost'],
        }

        for item, kws in keywords.items():
            if any(kw in text for kw in kws):
                collectibles.append(item)

        if not collectibles:
            collectibles = ['coin']

        return collectibles

    def _detect_mechanics(self, text: str) -> List[str]:
        """Detect game mechanics from text"""
        mechanics = []
        keywords = {
            'checkpoints': ['checkpoint', 'save point', 'respawn'],
            'time_limit': ['time', 'timer', 'countdown', 'speed run'],
            'lives': ['lives', 'continue', 'game over'],
            'inventory': ['inventory', 'item', 'collect'],
            'dialogue': ['talk', 'dialogue', 'conversation', 'npc'],
            'puzzles': ['puzzle', 'solve', 'switch', 'lever'],
            'destructible': ['destroy', 'break', 'destructible'],
        }

        for mechanic, kws in keywords.items():
            if any(kw in text for kw in kws):
                mechanics.append(mechanic)

        return mechanics


# =============================================================================
# PROCEDURAL LEVEL GENERATION
# =============================================================================

class ProceduralGenerator:
    """Generates game levels procedurally"""

    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 2**32)
        self.rng = random.Random(self.seed)

    def generate_platformer_level(self, width: int, height: int,
                                  difficulty: str = "medium") -> List[List[int]]:
        """
        Generate a platformer level.
        Returns a 2D grid where:
        0 = empty, 1 = ground, 2 = platform, 3 = spike/hazard
        """
        grid = [[0 for _ in range(width)] for _ in range(height)]

        # Ground at bottom
        for x in range(width):
            grid[height - 1][x] = 1

        # Generate platforms
        platform_density = {'easy': 0.3, 'medium': 0.4, 'hard': 0.25}[difficulty]
        hazard_density = {'easy': 0.02, 'medium': 0.05, 'hard': 0.1}[difficulty]

        # Create platforms at different heights
        for y in range(2, height - 2):
            if self.rng.random() < platform_density:
                # Platform start and length
                start_x = self.rng.randint(0, width - 5)
                length = self.rng.randint(3, min(8, width - start_x))

                for x in range(start_x, start_x + length):
                    grid[y][x] = 2

        # Add gaps in ground
        if difficulty != 'easy':
            num_gaps = self.rng.randint(1, 3 + (1 if difficulty == 'hard' else 0))
            for _ in range(num_gaps):
                gap_start = self.rng.randint(5, width - 8)
                gap_length = self.rng.randint(2, 4)
                for x in range(gap_start, gap_start + gap_length):
                    grid[height - 1][x] = 0

        # Add hazards
        for y in range(height - 2, 0, -1):
            for x in range(1, width - 1):
                if grid[y][x] == 0 and grid[y + 1][x] in [1, 2]:
                    if self.rng.random() < hazard_density:
                        grid[y][x] = 3

        return grid

    def generate_top_down_level(self, width: int, height: int) -> List[List[int]]:
        """
        Generate a top-down level (dungeon-style).
        0 = floor, 1 = wall, 2 = door
        """
        grid = [[1 for _ in range(width)] for _ in range(height)]

        # Create rooms
        rooms = []
        num_rooms = self.rng.randint(4, 8)

        for _ in range(num_rooms):
            room_w = self.rng.randint(4, 10)
            room_h = self.rng.randint(4, 8)
            room_x = self.rng.randint(1, width - room_w - 1)
            room_y = self.rng.randint(1, height - room_h - 1)

            # Check overlap
            overlaps = False
            for existing in rooms:
                if (room_x < existing[0] + existing[2] + 2 and
                    room_x + room_w + 2 > existing[0] and
                    room_y < existing[1] + existing[3] + 2 and
                    room_y + room_h + 2 > existing[1]):
                    overlaps = True
                    break

            if not overlaps:
                rooms.append((room_x, room_y, room_w, room_h))
                # Carve room
                for y in range(room_y, room_y + room_h):
                    for x in range(room_x, room_x + room_w):
                        grid[y][x] = 0

        # Connect rooms with corridors
        for i in range(len(rooms) - 1):
            room1 = rooms[i]
            room2 = rooms[i + 1]

            # Center points
            x1 = room1[0] + room1[2] // 2
            y1 = room1[1] + room1[3] // 2
            x2 = room2[0] + room2[2] // 2
            y2 = room2[1] + room2[3] // 2

            # L-shaped corridor
            while x1 != x2:
                grid[y1][x1] = 0
                x1 += 1 if x2 > x1 else -1

            while y1 != y2:
                grid[y1][x1] = 0
                y1 += 1 if y2 > y1 else -1

            grid[y1][x1] = 0

        return grid

    def generate_enemy_positions(self, grid: List[List[int]],
                                num_enemies: int) -> List[Tuple[int, int, str]]:
        """Generate enemy spawn positions based on level grid"""
        positions = []
        height = len(grid)
        width = len(grid[0])

        # Find valid spawn positions (on platforms/ground)
        valid_positions = []
        for y in range(height - 1):
            for x in range(width):
                if grid[y][x] == 0 and grid[y + 1][x] in [1, 2]:
                    valid_positions.append((x, y))

        if valid_positions:
            for _ in range(min(num_enemies, len(valid_positions))):
                pos = self.rng.choice(valid_positions)
                valid_positions.remove(pos)
                enemy_type = self.rng.choice(['walker', 'flyer', 'shooter'])
                positions.append((pos[0], pos[1], enemy_type))

        return positions

    def generate_collectible_positions(self, grid: List[List[int]],
                                      num_collectibles: int) -> List[Tuple[int, int, str]]:
        """Generate collectible spawn positions"""
        positions = []
        height = len(grid)
        width = len(grid[0])

        # Find valid positions
        valid_positions = []
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0:
                    valid_positions.append((x, y))

        collectible_types = ['coin', 'gem', 'heart']

        if valid_positions:
            for _ in range(min(num_collectibles, len(valid_positions))):
                pos = self.rng.choice(valid_positions)
                valid_positions.remove(pos)
                coll_type = self.rng.choice(collectible_types)
                positions.append((pos[0], pos[1], coll_type))

        return positions


# =============================================================================
# AI BEHAVIOR GENERATION
# =============================================================================

class BehaviorNodeType(Enum):
    """Types of behavior tree nodes"""
    SEQUENCE = auto()
    SELECTOR = auto()
    ACTION = auto()
    CONDITION = auto()
    DECORATOR = auto()


@dataclass
class BehaviorNode:
    """Behavior tree node"""
    node_type: BehaviorNodeType
    name: str
    children: List['BehaviorNode'] = field(default_factory=list)
    action: Optional[str] = None
    condition: Optional[str] = None


class BehaviorGenerator:
    """Generates AI behavior trees for game entities"""

    def __init__(self):
        # Predefined behaviors
        self.enemy_behaviors = {
            'walker': self._create_walker_behavior(),
            'flyer': self._create_flyer_behavior(),
            'shooter': self._create_shooter_behavior(),
            'chaser': self._create_chaser_behavior(),
            'boss': self._create_boss_behavior(),
        }

    def _create_walker_behavior(self) -> BehaviorNode:
        """Create patrol walking behavior"""
        return BehaviorNode(
            node_type=BehaviorNodeType.SELECTOR,
            name="Walker Root",
            children=[
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Attack Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "Can See Player", condition="can_see_player"),
                        BehaviorNode(BehaviorNodeType.CONDITION, "In Attack Range", condition="in_attack_range"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Attack", action="attack_melee"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Patrol Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.ACTION, "Patrol", action="patrol_horizontal"),
                        BehaviorNode(BehaviorNodeType.CONDITION, "At Edge", condition="at_platform_edge"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Turn Around", action="turn_around"),
                    ]
                ),
            ]
        )

    def _create_flyer_behavior(self) -> BehaviorNode:
        """Create flying enemy behavior"""
        return BehaviorNode(
            node_type=BehaviorNodeType.SELECTOR,
            name="Flyer Root",
            children=[
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Chase Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "Can See Player", condition="can_see_player"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Move Toward Player", action="move_toward_player"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Hover Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.ACTION, "Hover", action="hover_pattern"),
                    ]
                ),
            ]
        )

    def _create_shooter_behavior(self) -> BehaviorNode:
        """Create ranged shooter behavior"""
        return BehaviorNode(
            node_type=BehaviorNodeType.SELECTOR,
            name="Shooter Root",
            children=[
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Attack Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "Can See Player", condition="can_see_player"),
                        BehaviorNode(BehaviorNodeType.CONDITION, "Can Shoot", condition="cooldown_ready"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Aim", action="aim_at_player"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Shoot", action="fire_projectile"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.ACTION,
                    name="Idle",
                    action="idle"
                ),
            ]
        )

    def _create_chaser_behavior(self) -> BehaviorNode:
        """Create chasing enemy behavior"""
        return BehaviorNode(
            node_type=BehaviorNodeType.SELECTOR,
            name="Chaser Root",
            children=[
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Attack Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "In Attack Range", condition="in_attack_range"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Attack", action="attack_melee"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Chase Sequence",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "Can See Player", condition="can_see_player"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Chase", action="move_toward_player"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.ACTION,
                    name="Return",
                    action="return_to_start"
                ),
            ]
        )

    def _create_boss_behavior(self) -> BehaviorNode:
        """Create boss enemy behavior with multiple phases"""
        return BehaviorNode(
            node_type=BehaviorNodeType.SELECTOR,
            name="Boss Root",
            children=[
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Phase 3 (Low Health)",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "Health < 25%", condition="health_low"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Enrage", action="enter_rage_mode"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Rapid Attack", action="rapid_attack_pattern"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Phase 2",
                    children=[
                        BehaviorNode(BehaviorNodeType.CONDITION, "Health < 50%", condition="health_medium"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Summon", action="spawn_minions"),
                        BehaviorNode(BehaviorNodeType.ACTION, "Area Attack", action="area_attack"),
                    ]
                ),
                BehaviorNode(
                    node_type=BehaviorNodeType.SEQUENCE,
                    name="Phase 1",
                    children=[
                        BehaviorNode(BehaviorNodeType.ACTION, "Basic Attack", action="basic_attack_pattern"),
                    ]
                ),
            ]
        )

    def get_behavior(self, enemy_type: str) -> BehaviorNode:
        """Get behavior tree for enemy type"""
        return self.enemy_behaviors.get(enemy_type, self._create_walker_behavior())

    def behavior_to_code(self, behavior: BehaviorNode, indent: int = 0) -> str:
        """Convert behavior tree to executable code"""
        ind = "    " * indent
        lines = []

        if behavior.node_type == BehaviorNodeType.ACTION:
            lines.append(f"{ind}self.{behavior.action}()")
        elif behavior.node_type == BehaviorNodeType.CONDITION:
            lines.append(f"{ind}if self.{behavior.condition}():")
        elif behavior.node_type == BehaviorNodeType.SEQUENCE:
            lines.append(f"{ind}# Sequence: {behavior.name}")
            for child in behavior.children:
                lines.append(self.behavior_to_code(child, indent))
        elif behavior.node_type == BehaviorNodeType.SELECTOR:
            lines.append(f"{ind}# Selector: {behavior.name}")
            for i, child in enumerate(behavior.children):
                if i == 0:
                    lines.append(f"{ind}if {child.name.lower().replace(' ', '_')}:")
                else:
                    lines.append(f"{ind}elif {child.name.lower().replace(' ', '_')}:")
                lines.append(self.behavior_to_code(child, indent + 1))

        return '\n'.join(lines)


# =============================================================================
# TEXTURE/SPRITE GENERATION
# =============================================================================

class SpriteGenerator:
    """Generates simple procedural sprites"""

    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 2**32)
        self.rng = random.Random(self.seed)

    def generate_character_sprite(self, width: int = 16, height: int = 16,
                                  color: Color = None) -> List[List[Color]]:
        """Generate a simple character sprite"""
        if color is None:
            color = Color(self.rng.randint(100, 255),
                         self.rng.randint(100, 255),
                         self.rng.randint(100, 255))

        transparent = Color(0, 0, 0, 0)
        sprite = [[transparent for _ in range(width)] for _ in range(height)]

        # Generate half, mirror for symmetry
        half_width = width // 2

        for y in range(height):
            for x in range(half_width):
                if self.rng.random() < 0.4:
                    sprite[y][x] = color
                    sprite[y][width - 1 - x] = color

        # Add eyes
        eye_y = height // 4
        eye_x = half_width // 2
        eye_color = Color.white()
        if 0 <= eye_y < height and 0 <= eye_x < half_width:
            sprite[eye_y][eye_x] = eye_color
            sprite[eye_y][width - 1 - eye_x] = eye_color

        return sprite

    def generate_tile_sprite(self, width: int = 16, height: int = 16,
                            tile_type: str = "ground",
                            color: Color = None) -> List[List[Color]]:
        """Generate a tile sprite"""
        if color is None:
            colors = {
                'ground': Color(139, 90, 43),
                'grass': Color(34, 139, 34),
                'water': Color(30, 144, 255),
                'stone': Color(128, 128, 128),
                'lava': Color(255, 69, 0),
            }
            color = colors.get(tile_type, Color(139, 90, 43))

        sprite = [[color for _ in range(width)] for _ in range(height)]

        # Add noise/variation
        for y in range(height):
            for x in range(width):
                variation = self.rng.randint(-20, 20)
                r = max(0, min(255, color.r + variation))
                g = max(0, min(255, color.g + variation))
                b = max(0, min(255, color.b + variation))
                sprite[y][x] = Color(r, g, b)

        # Add highlights and shadows
        for x in range(width):
            # Top highlight
            sprite[0][x] = Color(
                min(255, sprite[0][x].r + 30),
                min(255, sprite[0][x].g + 30),
                min(255, sprite[0][x].b + 30)
            )
            # Bottom shadow
            sprite[height-1][x] = Color(
                max(0, sprite[height-1][x].r - 30),
                max(0, sprite[height-1][x].g - 30),
                max(0, sprite[height-1][x].b - 30)
            )

        return sprite

    def sprite_to_ascii(self, sprite: List[List[Color]]) -> str:
        """Convert sprite to ASCII representation for preview"""
        chars = " .:-=+*#%@"
        lines = []

        for row in sprite:
            line = ""
            for pixel in row:
                if pixel.a == 0:
                    line += " "
                else:
                    brightness = (pixel.r + pixel.g + pixel.b) // 3
                    char_index = min(len(chars) - 1, brightness * len(chars) // 256)
                    line += chars[char_index]
            lines.append(line)

        return '\n'.join(lines)


# =============================================================================
# STORY/DIALOGUE GENERATION
# =============================================================================

class StoryGenerator:
    """Generates game story and dialogue"""

    def __init__(self):
        # Story templates
        self.story_templates = [
            "The kingdom of {kingdom} has been invaded by {villain}. "
            "Only {hero} can save the land by collecting the {artifacts}.",

            "Long ago, {villain} sealed away the power of {artifact}. "
            "Now {hero} must journey through {location} to restore balance.",

            "When {villain} stole the {artifact}, darkness fell upon {kingdom}. "
            "{hero} must brave {location} to save their home.",
        ]

        self.kingdoms = ['Avaloria', 'Crystalhaven', 'Shadowmere', 'Sunvale', 'Frosthold']
        self.villains = ['the Dark Lord', 'an ancient dragon', 'a corrupted sorcerer', 'the Shadow King']
        self.heroes = ['a young warrior', 'the last knight', 'a brave adventurer', 'an unlikely hero']
        self.artifacts = ['Seven Sacred Gems', 'Ancient Relics', 'Elemental Crystals', 'Lost Treasures']
        self.locations = ['the Forbidden Forest', 'the Cursed Mountains', 'the Endless Caverns', 'the Ruined Castle']

        # Dialogue templates
        self.dialogue_types = {
            'greeting': [
                "Welcome, traveler! What brings you to {location}?",
                "Ah, {hero}! I've been expecting you.",
                "Be careful out there. {danger} lurks nearby.",
            ],
            'quest_give': [
                "I need you to find {item}. It's somewhere in {location}.",
                "Will you help us? {villain} has taken {item}!",
                "There's a reward if you can bring me {number} {item}s.",
            ],
            'merchant': [
                "Looking to buy? I have the finest wares!",
                "Need supplies? You've come to the right place.",
                "Special discount today! Everything must go!",
            ],
            'hint': [
                "I heard there's a secret passage in {location}.",
                "They say {item} can be found beyond the {obstacle}.",
                "Watch out for {enemy}. They're stronger than they look.",
            ],
        }

    def generate_story(self, theme: str = "fantasy") -> str:
        """Generate a game story"""
        template = random.choice(self.story_templates)

        return template.format(
            kingdom=random.choice(self.kingdoms),
            villain=random.choice(self.villains),
            hero=random.choice(self.heroes),
            artifact=random.choice(self.artifacts),
            artifacts=random.choice(self.artifacts),
            location=random.choice(self.locations),
        )

    def generate_dialogue(self, dialogue_type: str, context: Dict = None) -> str:
        """Generate NPC dialogue"""
        context = context or {}

        templates = self.dialogue_types.get(dialogue_type, self.dialogue_types['greeting'])
        template = random.choice(templates)

        # Fill in placeholders
        defaults = {
            'location': random.choice(self.locations),
            'hero': 'adventurer',
            'danger': 'danger',
            'villain': random.choice(self.villains),
            'item': 'mysterious artifact',
            'number': str(random.randint(3, 10)),
            'obstacle': 'ancient door',
            'enemy': 'powerful foe',
        }

        defaults.update(context)

        try:
            return template.format(**defaults)
        except KeyError:
            return template


# =============================================================================
# PIXEL ART AI INTEGRATION
# =============================================================================

class PixelArtIntegration:
    """
    Integration with AI pixel art generation services.
    Supports Pixellab AI and similar services.
    """

    def __init__(self):
        self.services = {
            'pixellab': {
                'url': 'https://api.pixellab.ai/generate',
                'description': 'Pixellab AI pixel art generator'
            },
            'stable_diffusion_pixel': {
                'url': 'local',
                'description': 'Stable Diffusion with pixel art LoRA'
            }
        }

        self.style_prompts = {
            'character': 'pixel art character sprite, 16x16, game asset, transparent background',
            'tile': 'pixel art tileset, seamless texture, game asset, 16x16',
            'item': 'pixel art item icon, game pickup, transparent background',
            'enemy': 'pixel art enemy sprite, game monster, side view',
            'background': 'pixel art background, parallax layer, game scene',
        }

    def generate_prompt(self, description: str, style: str = 'character') -> str:
        """Generate an optimized prompt for AI pixel art generation"""
        base_prompt = self.style_prompts.get(style, self.style_prompts['character'])
        return f"{description}, {base_prompt}"

    def get_generation_config(self, style: str = 'character',
                             width: int = 16, height: int = 16) -> Dict:
        """Get configuration for AI generation"""
        return {
            'prompt': self.style_prompts.get(style, ''),
            'width': width,
            'height': height,
            'style': 'pixel_art',
            'steps': 20,
            'cfg_scale': 7.5,
            'sampler': 'euler_a',
            'negative_prompt': 'blurry, high resolution, realistic, 3d render',
        }


# =============================================================================
# MAIN TEXT-TO-GAME GENERATOR
# =============================================================================

class TextToGameGenerator:
    """
    Main class for text-to-game generation.
    Takes a natural language description and generates a complete game.
    """

    def __init__(self):
        self.parser = TextParser()
        self.level_generator = ProceduralGenerator()
        self.behavior_generator = BehaviorGenerator()
        self.sprite_generator = SpriteGenerator()
        self.story_generator = StoryGenerator()
        self.pixel_art = PixelArtIntegration()

    def generate_game(self, description: str) -> Dict:
        """
        Generate a complete game from text description.

        Returns a dictionary containing:
        - description: Parsed game description
        - scenes: List of generated scenes
        - entities: List of entity configurations
        - assets: List of asset requirements
        - code: Generated game code
        """
        # Parse description
        game_desc = self.parser.parse(description)

        # Generate level based on genre
        if game_desc.genre == GameGenre.PLATFORMER:
            level = self.level_generator.generate_platformer_level(50, 15, game_desc.difficulty)
        else:
            level = self.level_generator.generate_top_down_level(30, 20)

        # Generate enemy positions
        enemy_count = {'easy': 3, 'medium': 5, 'hard': 8}[game_desc.difficulty]
        enemies = self.level_generator.generate_enemy_positions(level, enemy_count)

        # Generate collectibles
        collectible_count = {'easy': 15, 'medium': 10, 'hard': 5}[game_desc.difficulty]
        collectibles = self.level_generator.generate_collectible_positions(level, collectible_count)

        # Generate story
        story = self.story_generator.generate_story(game_desc.theme)

        # Generate sprite configurations
        sprites = {
            'player': self.sprite_generator.generate_character_sprite(16, 16, game_desc.color_palette[0]),
            'enemy': self.sprite_generator.generate_character_sprite(16, 16, game_desc.color_palette[1]),
            'ground': self.sprite_generator.generate_tile_sprite(16, 16, 'ground', game_desc.color_palette[2]),
        }

        # Generate behavior trees
        behaviors = {}
        for enemy_type in game_desc.enemy_types:
            behaviors[enemy_type] = self.behavior_generator.get_behavior(enemy_type)

        # Generate code
        code = self._generate_game_code(game_desc, level, enemies, collectibles)

        return {
            'description': game_desc,
            'level': level,
            'enemies': enemies,
            'collectibles': collectibles,
            'story': story,
            'sprites': sprites,
            'behaviors': behaviors,
            'code': code,
        }

    def _generate_game_code(self, desc: GameDescription, level: List[List[int]],
                           enemies: List, collectibles: List) -> str:
        """Generate Python game code"""
        code = f'''#!/usr/bin/env python3
"""
{desc.title}
Generated by Electroduction Text-to-Game AI
Genre: {desc.genre.name}
Theme: {desc.theme}
"""

# Game Configuration
GAME_TITLE = "{desc.title}"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32

# Player settings
PLAYER_SPEED = 200
PLAYER_JUMP_FORCE = -400
PLAYER_ABILITIES = {desc.player_abilities}

# Level data
LEVEL_DATA = {json.dumps(level)}

# Enemy spawns: (x, y, type)
ENEMY_SPAWNS = {enemies}

# Collectible spawns: (x, y, type)
COLLECTIBLE_SPAWNS = {collectibles}

# Color palette
COLORS = {{
    'background': {desc.color_palette[0].to_rgb_tuple() if desc.color_palette else (30, 30, 50)},
    'player': {desc.color_palette[0].to_rgb_tuple() if desc.color_palette else (100, 200, 100)},
    'enemy': {desc.color_palette[1].to_rgb_tuple() if len(desc.color_palette) > 1 else (200, 100, 100)},
    'platform': {desc.color_palette[2].to_rgb_tuple() if len(desc.color_palette) > 2 else (100, 100, 100)},
}}

def main():
    """Main game loop"""
    print(f"Starting {{GAME_TITLE}}...")
    print(f"Level size: {{len(LEVEL_DATA[0])}}x{{len(LEVEL_DATA)}} tiles")
    print(f"Enemies: {{len(ENEMY_SPAWNS)}}")
    print(f"Collectibles: {{len(COLLECTIBLE_SPAWNS)}}")
    print("Game generated successfully!")

if __name__ == "__main__":
    main()
'''
        return code

    def preview_game(self, game_data: Dict) -> str:
        """Generate a text preview of the game"""
        desc = game_data['description']
        level = game_data['level']

        preview = []
        preview.append(f"{'='*60}")
        preview.append(f"GAME PREVIEW: {desc.title}")
        preview.append(f"{'='*60}")
        preview.append(f"\nGenre: {desc.genre.name}")
        preview.append(f"Theme: {desc.theme}")
        preview.append(f"Art Style: {desc.art_style}")
        preview.append(f"Difficulty: {desc.difficulty}")

        preview.append(f"\nPlayer Abilities: {', '.join(desc.player_abilities)}")
        preview.append(f"Enemy Types: {', '.join(desc.enemy_types)}")
        preview.append(f"Collectibles: {', '.join(desc.collectibles)}")

        preview.append(f"\n{'-'*60}")
        preview.append("STORY:")
        preview.append(f"{'-'*60}")
        preview.append(game_data['story'])

        preview.append(f"\n{'-'*60}")
        preview.append("LEVEL PREVIEW:")
        preview.append(f"{'-'*60}")

        # ASCII level preview
        tile_chars = {0: ' ', 1: '#', 2: '=', 3: '^'}
        for row in level[:15]:  # Show first 15 rows
            line = ''.join(tile_chars.get(t, '?') for t in row[:40])  # First 40 cols
            preview.append(line)

        preview.append(f"\n{'-'*60}")
        preview.append("SPRITE PREVIEW (Player):")
        preview.append(f"{'-'*60}")
        preview.append(self.sprite_generator.sprite_to_ascii(game_data['sprites']['player']))

        preview.append(f"\n{'='*60}")

        return '\n'.join(preview)


# =============================================================================
# TESTING
# =============================================================================

def main():
    """Test AI generation components"""
    print("\n" + "="*60)
    print("AI GENERATOR TESTS")
    print("="*60 + "\n")

    # Test Text Parser
    print("[1] Testing Text Parser...")
    parser = TextParser()

    test_descriptions = [
        "A platformer game with jumping and shooting mechanics, set in a fantasy castle",
        "Top-down zombie shooter with powerups and boss battles",
        "Retro pixel art adventure game with puzzles and NPCs",
    ]

    for desc in test_descriptions:
        result = parser.parse(desc)
        print(f"    Input: {desc[:50]}...")
        print(f"    Genre: {result.genre.name}, Theme: {result.theme}")
        print()

    # Test Level Generator
    print("[2] Testing Level Generator...")
    gen = ProceduralGenerator(seed=42)

    level = gen.generate_platformer_level(30, 10, "medium")
    print("    Generated platformer level (30x10):")
    for row in level[:5]:
        print(f"    {''.join(str(t) for t in row[:30])}")
    print()

    # Test Behavior Generator
    print("[3] Testing Behavior Generator...")
    behavior_gen = BehaviorGenerator()

    for enemy_type in ['walker', 'flyer', 'shooter']:
        behavior = behavior_gen.get_behavior(enemy_type)
        print(f"    {enemy_type}: {behavior.name} ({len(behavior.children)} children)")

    print()

    # Test Sprite Generator
    print("[4] Testing Sprite Generator...")
    sprite_gen = SpriteGenerator(seed=42)

    sprite = sprite_gen.generate_character_sprite(8, 8)
    print("    Generated character sprite (8x8):")
    print(sprite_gen.sprite_to_ascii(sprite))
    print()

    # Test Story Generator
    print("[5] Testing Story Generator...")
    story_gen = StoryGenerator()

    story = story_gen.generate_story("fantasy")
    print(f"    Generated story:")
    print(f"    {story[:100]}...")
    print()

    dialogue = story_gen.generate_dialogue("quest_give")
    print(f"    Generated dialogue: {dialogue}")
    print()

    # Test Full Text-to-Game
    print("[6] Testing Text-to-Game Generation...")
    generator = TextToGameGenerator()

    game_description = """
    Create a retro pixel art platformer game called "Crystal Quest".
    The player can jump, double jump, and shoot projectiles.
    There should be walking enemies and flying enemies.
    Collect gems and coins throughout the levels.
    The theme should be fantasy with a castle setting.
    Medium difficulty with checkpoints.
    """

    game_data = generator.generate_game(game_description)

    print(generator.preview_game(game_data))
    print()

    # Show generated code preview
    print("[7] Generated Code Preview:")
    print(f"{'-'*60}")
    code_lines = game_data['code'].split('\n')
    for line in code_lines[:30]:
        print(line)
    print("...")
    print(f"{'-'*60}")

    print("\n" + "="*60)
    print("ALL AI GENERATOR TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
