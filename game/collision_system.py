"""
AAA-Quality Collision System - Inspired by Hades/Enter the Gungeon
Proper wall collision, tile-based system, smooth movement
"""

import pygame
import math

class CollisionSystem:
    """Handles all collision detection and resolution"""

    def __init__(self):
        self.walls = []
        self.obstacles = []
        self.collision_grid = {}
        self.grid_size = 50

    def add_wall(self, x, y, width, height):
        """Add a wall rectangle"""
        self.walls.append(pygame.Rect(x, y, width, height))

    def add_obstacle(self, x, y, radius):
        """Add circular obstacle"""
        self.obstacles.append({'x': x, 'y': y, 'radius': radius})

    def clear(self):
        """Clear all collision objects"""
        self.walls.clear()
        self.obstacles.clear()
        self.collision_grid.clear()

    def check_entity_collision(self, entity_x, entity_y, entity_radius, exclude_entity=None):
        """Check if entity collides with world"""
        # Check walls
        entity_rect = pygame.Rect(
            entity_x - entity_radius,
            entity_y - entity_radius,
            entity_radius * 2,
            entity_radius * 2
        )

        for wall in self.walls:
            if entity_rect.colliderect(wall):
                return True, wall

        # Check obstacles
        for obs in self.obstacles:
            dist = math.sqrt((entity_x - obs['x'])**2 + (entity_y - obs['y'])**2)
            if dist < entity_radius + obs['radius']:
                return True, obs

        return False, None

    def resolve_collision(self, entity_x, entity_y, entity_radius, velocity_x, velocity_y):
        """Resolve collision and return valid position"""
        new_x = entity_x + velocity_x
        new_y = entity_y + velocity_y

        # Check X movement
        collides_x, wall_x = self.check_entity_collision(new_x, entity_y, entity_radius)

        # Check Y movement
        collides_y, wall_y = self.check_entity_collision(entity_x, new_y, entity_radius)

        # Slide along walls
        if collides_x:
            new_x = entity_x

        if collides_y:
            new_y = entity_y

        # Both axis blocked - no movement
        if collides_x and collides_y:
            return entity_x, entity_y

        return new_x, new_y

    def get_push_out_vector(self, entity_x, entity_y, entity_radius):
        """Get vector to push entity out of collision"""
        # Check walls
        entity_rect = pygame.Rect(
            entity_x - entity_radius,
            entity_y - entity_radius,
            entity_radius * 2,
            entity_radius * 2
        )

        for wall in self.walls:
            if entity_rect.colliderect(wall):
                # Calculate push direction
                center_x = wall.x + wall.width / 2
                center_y = wall.y + wall.height / 2

                dx = entity_x - center_x
                dy = entity_y - center_y

                # Find closest edge
                if abs(dx) > abs(dy):
                    # Push horizontally
                    if dx > 0:
                        return wall.right + entity_radius - entity_x, 0
                    else:
                        return wall.left - entity_radius - entity_x, 0
                else:
                    # Push vertically
                    if dy > 0:
                        return 0, wall.bottom + entity_radius - entity_y
                    else:
                        return 0, wall.top - entity_radius - entity_y

        return 0, 0

    def raycast(self, start_x, start_y, end_x, end_y):
        """Check if ray hits a wall"""
        # Simple line-rectangle intersection
        for wall in self.walls:
            if self._line_rect_intersect(start_x, start_y, end_x, end_y, wall):
                return True, wall

        return False, None

    def _line_rect_intersect(self, x1, y1, x2, y2, rect):
        """Check if line intersects rectangle"""
        # Check if either endpoint is inside
        if rect.collidepoint(x1, y1) or rect.collidepoint(x2, y2):
            return True

        # Check line intersection with each edge
        # Top edge
        if self._line_segment_intersect(x1, y1, x2, y2, rect.left, rect.top, rect.right, rect.top):
            return True
        # Bottom edge
        if self._line_segment_intersect(x1, y1, x2, y2, rect.left, rect.bottom, rect.right, rect.bottom):
            return True
        # Left edge
        if self._line_segment_intersect(x1, y1, x2, y2, rect.left, rect.top, rect.left, rect.bottom):
            return True
        # Right edge
        if self._line_segment_intersect(x1, y1, x2, y2, rect.right, rect.top, rect.right, rect.bottom):
            return True

        return False

    def _line_segment_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Check if two line segments intersect"""
        denom = ((y4 - y3) * (x2 - x1)) - ((x4 - x3) * (y2 - y1))

        if denom == 0:
            return False

        ua = (((x4 - x3) * (y1 - y3)) - ((y4 - y3) * (x1 - x3))) / denom
        ub = (((x2 - x1) * (y1 - y3)) - ((y2 - y1) * (x1 - x3))) / denom

        return (0 <= ua <= 1) and (0 <= ub <= 1)

class TileMap:
    """Tile-based map system for dungeon rooms"""

    TILE_SIZE = 32

    TILE_TYPES = {
        'floor': 0,
        'wall': 1,
        'door': 2,
        'void': 3,
        'decoration': 4
    }

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[0 for _ in range(width)] for _ in range(height)]

    def set_tile(self, x, y, tile_type):
        """Set tile at grid position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile_type

    def get_tile(self, x, y):
        """Get tile at grid position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return self.TILE_TYPES['wall']  # Out of bounds is wall

    def world_to_tile(self, world_x, world_y):
        """Convert world coordinates to tile coordinates"""
        return int(world_x // self.TILE_SIZE), int(world_y // self.TILE_SIZE)

    def tile_to_world(self, tile_x, tile_y):
        """Convert tile coordinates to world coordinates (center)"""
        return (tile_x * self.TILE_SIZE + self.TILE_SIZE // 2,
                tile_y * self.TILE_SIZE + self.TILE_SIZE // 2)

    def is_walkable(self, tile_x, tile_y):
        """Check if tile is walkable"""
        tile = self.get_tile(tile_x, tile_y)
        return tile in [self.TILE_TYPES['floor'], self.TILE_TYPES['door']]

    def generate_room_walls(self, collision_system, offset_x=0, offset_y=0):
        """Generate collision rectangles for walls

        Args:
            collision_system: CollisionSystem to add walls to
            offset_x: X offset for the room in world coordinates
            offset_y: Y offset for the room in world coordinates
        """
        # Convert tile walls to collision rectangles
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == self.TILE_TYPES['wall']:
                    world_x, world_y = self.tile_to_world(x, y)
                    collision_system.add_wall(
                        offset_x + world_x - self.TILE_SIZE // 2,
                        offset_y + world_y - self.TILE_SIZE // 2,
                        self.TILE_SIZE,
                        self.TILE_SIZE
                    )

    def create_rectangular_room(self, offset_x=0, offset_y=0):
        """Create a simple rectangular room with walls"""
        # Fill with walls
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x] = self.TILE_TYPES['wall']

        # Create floor area
        for y in range(2, self.height - 2):
            for x in range(2, self.width - 2):
                self.tiles[y][x] = self.TILE_TYPES['floor']

        # Add doors (top, bottom, left, right)
        mid_x = self.width // 2
        mid_y = self.height // 2

        # Top door
        self.tiles[1][mid_x] = self.TILE_TYPES['door']
        self.tiles[1][mid_x - 1] = self.TILE_TYPES['door']
        self.tiles[1][mid_x + 1] = self.TILE_TYPES['door']

        # Bottom door
        self.tiles[self.height - 2][mid_x] = self.TILE_TYPES['door']
        self.tiles[self.height - 2][mid_x - 1] = self.TILE_TYPES['door']
        self.tiles[self.height - 2][mid_x + 1] = self.TILE_TYPES['door']

        # Left door
        self.tiles[mid_y][1] = self.TILE_TYPES['door']
        self.tiles[mid_y - 1][1] = self.TILE_TYPES['door']
        self.tiles[mid_y + 1][1] = self.TILE_TYPES['door']

        # Right door
        self.tiles[mid_y][self.width - 2] = self.TILE_TYPES['door']
        self.tiles[mid_y - 1][self.width - 2] = self.TILE_TYPES['door']
        self.tiles[mid_y + 1][self.width - 2] = self.TILE_TYPES['door']

    def render(self, screen, camera):
        """Render tilemap"""
        # Tile colors
        tile_colors = {
            self.TILE_TYPES['floor']: (40, 40, 50),
            self.TILE_TYPES['wall']: (80, 80, 90),
            self.TILE_TYPES['door']: (60, 80, 100),
            self.TILE_TYPES['void']: (10, 10, 15),
            self.TILE_TYPES['decoration']: (70, 60, 80)
        }

        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]
                world_x, world_y = self.tile_to_world(x, y)

                screen_x, screen_y = camera.world_to_screen(
                    world_x - self.TILE_SIZE // 2,
                    world_y - self.TILE_SIZE // 2
                )

                color = tile_colors.get(tile_type, (50, 50, 50))

                pygame.draw.rect(screen, color,
                               (int(screen_x), int(screen_y), self.TILE_SIZE, self.TILE_SIZE))

                # Add wall shading
                if tile_type == self.TILE_TYPES['wall']:
                    # Top highlight
                    pygame.draw.line(screen, (100, 100, 110),
                                   (int(screen_x), int(screen_y)),
                                   (int(screen_x + self.TILE_SIZE), int(screen_y)), 2)
                    # Left highlight
                    pygame.draw.line(screen, (100, 100, 110),
                                   (int(screen_x), int(screen_y)),
                                   (int(screen_x), int(screen_y + self.TILE_SIZE)), 2)
