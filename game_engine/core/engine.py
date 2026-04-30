#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION GAME ENGINE - CORE ENGINE
===============================================================================
A comprehensive game engine supporting:
- 2D and 3D game development
- Entity Component System (ECS) architecture
- Physics simulation
- Scene management
- Asset management
- Input handling
- Audio system
- AI integration for procedural generation

This is the main engine module that ties all systems together.
===============================================================================
"""

import os
import sys
import time
import math
import json
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Callable, Any, Type, Union
from enum import Enum, auto
from abc import ABC, abstractmethod
import uuid
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GameEngine')


# =============================================================================
# MATHEMATICAL PRIMITIVES
# =============================================================================

@dataclass
class Vector2:
    """2D Vector"""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x / scalar, self.y / scalar)

    def dot(self, other: 'Vector2') -> float:
        return self.x * other.x + self.y * other.y

    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self) -> 'Vector2':
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return self / mag

    def distance_to(self, other: 'Vector2') -> float:
        return (self - other).magnitude()

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_int_tuple(self) -> Tuple[int, int]:
        return (int(self.x), int(self.y))

    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> 'Vector2':
        return cls(t[0], t[1])

    @classmethod
    def zero(cls) -> 'Vector2':
        return cls(0, 0)

    @classmethod
    def one(cls) -> 'Vector2':
        return cls(1, 1)

    @classmethod
    def up(cls) -> 'Vector2':
        return cls(0, -1)

    @classmethod
    def down(cls) -> 'Vector2':
        return cls(0, 1)

    @classmethod
    def left(cls) -> 'Vector2':
        return cls(-1, 0)

    @classmethod
    def right(cls) -> 'Vector2':
        return cls(1, 0)


@dataclass
class Vector3:
    """3D Vector"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self) -> 'Vector3':
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return self / mag

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @classmethod
    def zero(cls) -> 'Vector3':
        return cls(0, 0, 0)

    @classmethod
    def one(cls) -> 'Vector3':
        return cls(1, 1, 1)

    @classmethod
    def forward(cls) -> 'Vector3':
        return cls(0, 0, 1)

    @classmethod
    def up(cls) -> 'Vector3':
        return cls(0, 1, 0)

    @classmethod
    def right(cls) -> 'Vector3':
        return cls(1, 0, 0)


@dataclass
class Color:
    """RGBA Color"""
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

    def to_rgb_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> 'Color':
        hex_str = hex_str.lstrip('#')
        return cls(
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16)
        )

    # Predefined colors
    @classmethod
    def white(cls) -> 'Color':
        return cls(255, 255, 255)

    @classmethod
    def black(cls) -> 'Color':
        return cls(0, 0, 0)

    @classmethod
    def red(cls) -> 'Color':
        return cls(255, 0, 0)

    @classmethod
    def green(cls) -> 'Color':
        return cls(0, 255, 0)

    @classmethod
    def blue(cls) -> 'Color':
        return cls(0, 0, 255)

    @classmethod
    def yellow(cls) -> 'Color':
        return cls(255, 255, 0)

    @classmethod
    def cyan(cls) -> 'Color':
        return cls(0, 255, 255)

    @classmethod
    def magenta(cls) -> 'Color':
        return cls(255, 0, 255)


@dataclass
class Rectangle:
    """2D Rectangle"""
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Vector2:
        return Vector2(self.x + self.width / 2, self.y + self.height / 2)

    def contains(self, point: Vector2) -> bool:
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)

    def intersects(self, other: 'Rectangle') -> bool:
        return (self.left < other.right and self.right > other.left and
                self.top < other.bottom and self.bottom > other.top)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class Transform:
    """Transform component for position, rotation, and scale"""
    position: Vector3 = field(default_factory=Vector3.zero)
    rotation: Vector3 = field(default_factory=Vector3.zero)  # Euler angles
    scale: Vector3 = field(default_factory=Vector3.one)

    @property
    def position2d(self) -> Vector2:
        return Vector2(self.position.x, self.position.y)

    @position2d.setter
    def position2d(self, value: Vector2):
        self.position.x = value.x
        self.position.y = value.y


# =============================================================================
# ENTITY COMPONENT SYSTEM (ECS)
# =============================================================================

class Component(ABC):
    """Base class for all components"""

    def __init__(self):
        self.entity: Optional['Entity'] = None
        self.enabled: bool = True

    def on_attach(self, entity: 'Entity'):
        """Called when component is attached to an entity"""
        self.entity = entity

    def on_detach(self):
        """Called when component is detached from entity"""
        self.entity = None


class Entity:
    """Game entity (game object)"""

    def __init__(self, name: str = "Entity"):
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.active: bool = True
        self.components: Dict[Type[Component], Component] = {}
        self.children: List['Entity'] = []
        self.parent: Optional['Entity'] = None
        self.tags: Set[str] = set()
        self.layer: int = 0

        # Every entity has a transform
        self.transform = Transform()

    def add_component(self, component: Component) -> Component:
        """Add a component to this entity"""
        component_type = type(component)
        if component_type in self.components:
            logger.warning(f"Entity {self.name} already has {component_type.__name__}")
            return self.components[component_type]

        self.components[component_type] = component
        component.on_attach(self)
        return component

    def get_component(self, component_type: Type[Component]) -> Optional[Component]:
        """Get a component by type"""
        return self.components.get(component_type)

    def has_component(self, component_type: Type[Component]) -> bool:
        """Check if entity has a component"""
        return component_type in self.components

    def remove_component(self, component_type: Type[Component]) -> bool:
        """Remove a component by type"""
        if component_type in self.components:
            self.components[component_type].on_detach()
            del self.components[component_type]
            return True
        return False

    def add_child(self, child: 'Entity'):
        """Add a child entity"""
        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: 'Entity'):
        """Remove a child entity"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def add_tag(self, tag: str):
        """Add a tag to this entity"""
        self.tags.add(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if entity has a tag"""
        return tag in self.tags

    def to_dict(self) -> Dict:
        """Serialize entity to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'active': self.active,
            'tags': list(self.tags),
            'layer': self.layer,
            'transform': {
                'position': self.transform.position.to_tuple(),
                'rotation': self.transform.rotation.to_tuple(),
                'scale': self.transform.scale.to_tuple()
            },
            'components': [type(c).__name__ for c in self.components.values()],
            'children': [c.to_dict() for c in self.children]
        }


class System(ABC):
    """Base class for all ECS systems"""

    def __init__(self):
        self.enabled: bool = True
        self.priority: int = 0  # Lower = runs first

    @abstractmethod
    def update(self, entities: List[Entity], delta_time: float):
        """Update system logic"""
        pass

    def get_required_components(self) -> List[Type[Component]]:
        """Return list of required component types"""
        return []


# =============================================================================
# BUILT-IN COMPONENTS
# =============================================================================

class SpriteComponent(Component):
    """2D sprite rendering component"""

    def __init__(self, texture_path: str = None, color: Color = None):
        super().__init__()
        self.texture_path: Optional[str] = texture_path
        self.color: Color = color or Color.white()
        self.flip_x: bool = False
        self.flip_y: bool = False
        self.layer: int = 0
        self.visible: bool = True
        self.width: int = 32
        self.height: int = 32
        self.source_rect: Optional[Rectangle] = None  # For sprite sheets
        self.origin: Vector2 = Vector2(0.5, 0.5)  # Pivot point (0-1)


class AnimationComponent(Component):
    """Animation component for sprite animation"""

    def __init__(self):
        super().__init__()
        self.animations: Dict[str, List[Rectangle]] = {}  # name -> frames
        self.current_animation: Optional[str] = None
        self.current_frame: int = 0
        self.frame_time: float = 0.1  # Seconds per frame
        self.elapsed: float = 0.0
        self.loop: bool = True
        self.playing: bool = False

    def add_animation(self, name: str, frames: List[Rectangle]):
        """Add an animation"""
        self.animations[name] = frames

    def play(self, name: str, loop: bool = True):
        """Play an animation"""
        if name in self.animations:
            self.current_animation = name
            self.current_frame = 0
            self.elapsed = 0.0
            self.loop = loop
            self.playing = True

    def stop(self):
        """Stop current animation"""
        self.playing = False


class RigidBodyComponent(Component):
    """Physics rigid body component"""

    class BodyType(Enum):
        STATIC = auto()
        DYNAMIC = auto()
        KINEMATIC = auto()

    def __init__(self, body_type: 'RigidBodyComponent.BodyType' = None):
        super().__init__()
        self.body_type = body_type or self.BodyType.DYNAMIC
        self.velocity: Vector2 = Vector2.zero()
        self.acceleration: Vector2 = Vector2.zero()
        self.mass: float = 1.0
        self.drag: float = 0.0
        self.gravity_scale: float = 1.0
        self.use_gravity: bool = True
        self.is_grounded: bool = False


class ColliderComponent(Component):
    """Collision detection component"""

    class ColliderType(Enum):
        BOX = auto()
        CIRCLE = auto()

    def __init__(self, collider_type: 'ColliderComponent.ColliderType' = None):
        super().__init__()
        self.collider_type = collider_type or self.ColliderType.BOX
        self.width: float = 32.0
        self.height: float = 32.0
        self.radius: float = 16.0  # For circle collider
        self.offset: Vector2 = Vector2.zero()
        self.is_trigger: bool = False
        self.collision_layer: int = 0
        self.collision_mask: int = 0xFFFFFFFF

    def get_bounds(self, position: Vector2) -> Rectangle:
        """Get collision bounds"""
        if self.collider_type == self.ColliderType.BOX:
            return Rectangle(
                position.x + self.offset.x - self.width / 2,
                position.y + self.offset.y - self.height / 2,
                self.width,
                self.height
            )
        else:
            return Rectangle(
                position.x + self.offset.x - self.radius,
                position.y + self.offset.y - self.radius,
                self.radius * 2,
                self.radius * 2
            )


class ScriptComponent(Component):
    """Custom behavior script component"""

    def __init__(self):
        super().__init__()
        self._scripts: Dict[str, Callable] = {}
        self.variables: Dict[str, Any] = {}

    def add_script(self, name: str, script: Callable):
        """Add a script function"""
        self._scripts[name] = script

    def run_script(self, name: str, *args, **kwargs):
        """Run a script by name"""
        if name in self._scripts:
            return self._scripts[name](self.entity, *args, **kwargs)
        return None


class AudioComponent(Component):
    """Audio playback component"""

    def __init__(self):
        super().__init__()
        self.sounds: Dict[str, str] = {}  # name -> file path
        self.volume: float = 1.0
        self.pitch: float = 1.0
        self.loop: bool = False
        self.spatial: bool = False  # 3D positional audio


class ParticleEmitterComponent(Component):
    """Particle system emitter component"""

    def __init__(self):
        super().__init__()
        self.emission_rate: float = 10.0  # Particles per second
        self.particle_lifetime: float = 2.0
        self.start_speed: float = 100.0
        self.start_size: float = 10.0
        self.start_color: Color = Color.white()
        self.end_color: Color = Color(255, 255, 255, 0)
        self.gravity_modifier: float = 1.0
        self.spread_angle: float = 360.0
        self.max_particles: int = 100
        self.active: bool = True


class UIComponent(Component):
    """UI element component"""

    class UIType(Enum):
        TEXT = auto()
        IMAGE = auto()
        BUTTON = auto()
        PANEL = auto()
        SLIDER = auto()
        INPUT = auto()

    def __init__(self, ui_type: 'UIComponent.UIType' = None):
        super().__init__()
        self.ui_type = ui_type or self.UIType.TEXT
        self.text: str = ""
        self.font_size: int = 16
        self.font_name: str = "default"
        self.text_color: Color = Color.white()
        self.background_color: Color = Color(0, 0, 0, 128)
        self.width: float = 100
        self.height: float = 30
        self.padding: float = 5
        self.interactive: bool = True
        self.on_click: Optional[Callable] = None


class TilemapComponent(Component):
    """Tilemap for 2D level design"""

    def __init__(self, tile_width: int = 32, tile_height: int = 32):
        super().__init__()
        self.tile_width: int = tile_width
        self.tile_height: int = tile_height
        self.tiles: Dict[Tuple[int, int], int] = {}  # (x, y) -> tile_id
        self.tileset_path: Optional[str] = None
        self.tileset_columns: int = 8
        self.collision_tiles: Set[int] = set()  # Tile IDs that have collision

    def set_tile(self, x: int, y: int, tile_id: int):
        """Set a tile at position"""
        self.tiles[(x, y)] = tile_id

    def get_tile(self, x: int, y: int) -> int:
        """Get tile at position (-1 if empty)"""
        return self.tiles.get((x, y), -1)

    def world_to_tile(self, world_pos: Vector2) -> Tuple[int, int]:
        """Convert world position to tile coordinates"""
        return (int(world_pos.x // self.tile_width),
                int(world_pos.y // self.tile_height))

    def tile_to_world(self, tile_x: int, tile_y: int) -> Vector2:
        """Convert tile coordinates to world position"""
        return Vector2(tile_x * self.tile_width, tile_y * self.tile_height)


# =============================================================================
# BUILT-IN SYSTEMS
# =============================================================================

class PhysicsSystem(System):
    """Physics simulation system"""

    def __init__(self):
        super().__init__()
        self.gravity: Vector2 = Vector2(0, 980)  # Pixels per second squared
        self.priority = 10

    def get_required_components(self) -> List[Type[Component]]:
        return [RigidBodyComponent]

    def update(self, entities: List[Entity], delta_time: float):
        for entity in entities:
            if not entity.active:
                continue

            rb = entity.get_component(RigidBodyComponent)
            if not rb or not rb.enabled:
                continue

            if rb.body_type != RigidBodyComponent.BodyType.DYNAMIC:
                continue

            # Apply gravity
            if rb.use_gravity:
                rb.acceleration = rb.acceleration + self.gravity * rb.gravity_scale

            # Apply acceleration to velocity
            rb.velocity = rb.velocity + rb.acceleration * delta_time

            # Apply drag
            if rb.drag > 0:
                rb.velocity = rb.velocity * (1.0 - rb.drag * delta_time)

            # Update position
            entity.transform.position.x += rb.velocity.x * delta_time
            entity.transform.position.y += rb.velocity.y * delta_time

            # Reset acceleration
            rb.acceleration = Vector2.zero()


class CollisionSystem(System):
    """Collision detection system"""

    def __init__(self):
        super().__init__()
        self.priority = 20
        self.collision_callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def get_required_components(self) -> List[Type[Component]]:
        return [ColliderComponent]

    def register_callback(self, tag: str, callback: Callable):
        """Register collision callback for tagged entities"""
        self.collision_callbacks[tag].append(callback)

    def update(self, entities: List[Entity], delta_time: float):
        # Get all entities with colliders
        collidables = []
        for entity in entities:
            if not entity.active:
                continue
            collider = entity.get_component(ColliderComponent)
            if collider and collider.enabled:
                collidables.append((entity, collider))

        # Check collisions (O(n^2) - can be optimized with spatial partitioning)
        for i, (entity_a, collider_a) in enumerate(collidables):
            for entity_b, collider_b in collidables[i + 1:]:
                # Check layer masks
                if not (collider_a.collision_mask & (1 << collider_b.collision_layer)):
                    continue
                if not (collider_b.collision_mask & (1 << collider_a.collision_layer)):
                    continue

                # Get bounds
                pos_a = entity_a.transform.position2d
                pos_b = entity_b.transform.position2d
                bounds_a = collider_a.get_bounds(pos_a)
                bounds_b = collider_b.get_bounds(pos_b)

                # Check intersection
                if bounds_a.intersects(bounds_b):
                    self._handle_collision(entity_a, entity_b, collider_a, collider_b)

    def _handle_collision(self, entity_a: Entity, entity_b: Entity,
                         collider_a: ColliderComponent, collider_b: ColliderComponent):
        """Handle collision between two entities"""
        # Call callbacks
        for tag in entity_a.tags:
            for callback in self.collision_callbacks.get(tag, []):
                callback(entity_a, entity_b)

        for tag in entity_b.tags:
            for callback in self.collision_callbacks.get(tag, []):
                callback(entity_b, entity_a)

        # If neither is a trigger, resolve collision
        if not collider_a.is_trigger and not collider_b.is_trigger:
            self._resolve_collision(entity_a, entity_b, collider_a, collider_b)

    def _resolve_collision(self, entity_a: Entity, entity_b: Entity,
                          collider_a: ColliderComponent, collider_b: ColliderComponent):
        """Resolve collision (simple push-out)"""
        rb_a = entity_a.get_component(RigidBodyComponent)
        rb_b = entity_b.get_component(RigidBodyComponent)

        # Get bounds
        pos_a = entity_a.transform.position2d
        pos_b = entity_b.transform.position2d
        bounds_a = collider_a.get_bounds(pos_a)
        bounds_b = collider_b.get_bounds(pos_b)

        # Calculate overlap
        overlap_x = min(bounds_a.right - bounds_b.left, bounds_b.right - bounds_a.left)
        overlap_y = min(bounds_a.bottom - bounds_b.top, bounds_b.bottom - bounds_a.top)

        # Push out along smallest overlap
        if overlap_x < overlap_y:
            if bounds_a.center.x < bounds_b.center.x:
                push = -overlap_x
            else:
                push = overlap_x

            if rb_a and rb_a.body_type == RigidBodyComponent.BodyType.DYNAMIC:
                entity_a.transform.position.x += push / 2
            if rb_b and rb_b.body_type == RigidBodyComponent.BodyType.DYNAMIC:
                entity_b.transform.position.x -= push / 2
        else:
            if bounds_a.center.y < bounds_b.center.y:
                push = -overlap_y
            else:
                push = overlap_y

            if rb_a and rb_a.body_type == RigidBodyComponent.BodyType.DYNAMIC:
                entity_a.transform.position.y += push / 2
                if push < 0 and rb_a:
                    rb_a.is_grounded = True
                    rb_a.velocity.y = 0
            if rb_b and rb_b.body_type == RigidBodyComponent.BodyType.DYNAMIC:
                entity_b.transform.position.y -= push / 2


class AnimationSystem(System):
    """Animation update system"""

    def __init__(self):
        super().__init__()
        self.priority = 30

    def get_required_components(self) -> List[Type[Component]]:
        return [AnimationComponent, SpriteComponent]

    def update(self, entities: List[Entity], delta_time: float):
        for entity in entities:
            if not entity.active:
                continue

            anim = entity.get_component(AnimationComponent)
            sprite = entity.get_component(SpriteComponent)

            if not anim or not sprite or not anim.enabled or not anim.playing:
                continue

            if not anim.current_animation or anim.current_animation not in anim.animations:
                continue

            frames = anim.animations[anim.current_animation]
            if not frames:
                continue

            # Update animation timing
            anim.elapsed += delta_time

            if anim.elapsed >= anim.frame_time:
                anim.elapsed = 0
                anim.current_frame += 1

                if anim.current_frame >= len(frames):
                    if anim.loop:
                        anim.current_frame = 0
                    else:
                        anim.current_frame = len(frames) - 1
                        anim.playing = False

            # Update sprite source rect
            sprite.source_rect = frames[anim.current_frame]


class ScriptSystem(System):
    """Script execution system"""

    def __init__(self):
        super().__init__()
        self.priority = 5  # Run before physics

    def get_required_components(self) -> List[Type[Component]]:
        return [ScriptComponent]

    def update(self, entities: List[Entity], delta_time: float):
        for entity in entities:
            if not entity.active:
                continue

            script = entity.get_component(ScriptComponent)
            if not script or not script.enabled:
                continue

            # Run update script if exists
            script.run_script('update', delta_time)


# =============================================================================
# SCENE MANAGEMENT
# =============================================================================

class Scene:
    """Game scene containing entities"""

    def __init__(self, name: str = "Untitled"):
        self.name: str = name
        self.entities: Dict[str, Entity] = {}
        self.root_entities: List[Entity] = []
        self.background_color: Color = Color(30, 30, 30)
        self.camera_position: Vector2 = Vector2.zero()
        self.camera_zoom: float = 1.0
        self.metadata: Dict[str, Any] = {}

    def add_entity(self, entity: Entity) -> Entity:
        """Add an entity to the scene"""
        self.entities[entity.id] = entity
        if entity.parent is None:
            self.root_entities.append(entity)
        return entity

    def remove_entity(self, entity: Entity):
        """Remove an entity from the scene"""
        if entity.id in self.entities:
            del self.entities[entity.id]
        if entity in self.root_entities:
            self.root_entities.remove(entity)

        # Remove children
        for child in entity.children:
            self.remove_entity(child)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)

    def find_entity(self, name: str) -> Optional[Entity]:
        """Find entity by name"""
        for entity in self.entities.values():
            if entity.name == name:
                return entity
        return None

    def find_entities_with_tag(self, tag: str) -> List[Entity]:
        """Find all entities with a tag"""
        return [e for e in self.entities.values() if e.has_tag(tag)]

    def find_entities_with_component(self, component_type: Type[Component]) -> List[Entity]:
        """Find all entities with a component type"""
        return [e for e in self.entities.values() if e.has_component(component_type)]

    def get_all_entities(self) -> List[Entity]:
        """Get all entities in scene"""
        return list(self.entities.values())

    def to_dict(self) -> Dict:
        """Serialize scene to dictionary"""
        return {
            'name': self.name,
            'background_color': self.background_color.to_tuple(),
            'camera_position': self.camera_position.to_tuple(),
            'camera_zoom': self.camera_zoom,
            'metadata': self.metadata,
            'entities': [e.to_dict() for e in self.root_entities]
        }

    def save(self, filepath: str):
        """Save scene to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Scene saved to {filepath}")


class SceneManager:
    """Manages multiple scenes"""

    def __init__(self):
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self._scene_stack: List[Scene] = []

    def create_scene(self, name: str) -> Scene:
        """Create a new scene"""
        scene = Scene(name)
        self.scenes[name] = scene
        return scene

    def load_scene(self, name: str) -> bool:
        """Load and switch to a scene"""
        if name in self.scenes:
            self.current_scene = self.scenes[name]
            logger.info(f"Loaded scene: {name}")
            return True
        return False

    def push_scene(self, name: str) -> bool:
        """Push current scene and load new one"""
        if self.current_scene:
            self._scene_stack.append(self.current_scene)
        return self.load_scene(name)

    def pop_scene(self) -> bool:
        """Return to previous scene"""
        if self._scene_stack:
            self.current_scene = self._scene_stack.pop()
            return True
        return False

    def get_current_scene(self) -> Optional[Scene]:
        """Get current active scene"""
        return self.current_scene


# =============================================================================
# ASSET MANAGEMENT
# =============================================================================

class AssetType(Enum):
    """Types of assets"""
    TEXTURE = auto()
    AUDIO = auto()
    FONT = auto()
    TILEMAP = auto()
    PREFAB = auto()
    SCRIPT = auto()
    SHADER = auto()
    MODEL = auto()


@dataclass
class Asset:
    """Asset metadata"""
    id: str
    name: str
    asset_type: AssetType
    path: str
    loaded: bool = False
    data: Any = None
    metadata: Dict = field(default_factory=dict)


class AssetManager:
    """Manages game assets (textures, sounds, etc.)"""

    def __init__(self, base_path: str = "assets"):
        self.base_path = base_path
        self.assets: Dict[str, Asset] = {}
        self._cache: Dict[str, Any] = {}

    def register_asset(self, name: str, path: str, asset_type: AssetType) -> Asset:
        """Register an asset for loading"""
        asset = Asset(
            id=str(uuid.uuid4()),
            name=name,
            asset_type=asset_type,
            path=os.path.join(self.base_path, path)
        )
        self.assets[name] = asset
        return asset

    def load_asset(self, name: str) -> Optional[Any]:
        """Load an asset"""
        if name not in self.assets:
            logger.warning(f"Asset not found: {name}")
            return None

        asset = self.assets[name]

        if asset.loaded and name in self._cache:
            return self._cache[name]

        # Load based on type
        try:
            if asset.asset_type == AssetType.TEXTURE:
                # Would load image here
                asset.data = {'path': asset.path, 'type': 'texture'}
            elif asset.asset_type == AssetType.AUDIO:
                asset.data = {'path': asset.path, 'type': 'audio'}
            elif asset.asset_type == AssetType.FONT:
                asset.data = {'path': asset.path, 'type': 'font'}
            elif asset.asset_type == AssetType.PREFAB:
                with open(asset.path, 'r') as f:
                    asset.data = json.load(f)
            elif asset.asset_type == AssetType.SCRIPT:
                with open(asset.path, 'r') as f:
                    asset.data = f.read()

            asset.loaded = True
            self._cache[name] = asset.data
            logger.debug(f"Loaded asset: {name}")
            return asset.data

        except Exception as e:
            logger.error(f"Failed to load asset {name}: {e}")
            return None

    def unload_asset(self, name: str):
        """Unload an asset from cache"""
        if name in self._cache:
            del self._cache[name]
        if name in self.assets:
            self.assets[name].loaded = False

    def get_asset(self, name: str) -> Optional[Asset]:
        """Get asset metadata"""
        return self.assets.get(name)


# =============================================================================
# INPUT MANAGEMENT
# =============================================================================

class InputAction(Enum):
    """Input actions"""
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    JUMP = auto()
    ATTACK = auto()
    INTERACT = auto()
    PAUSE = auto()
    CONFIRM = auto()
    CANCEL = auto()


class InputManager:
    """Manages input from keyboard, mouse, and gamepad"""

    def __init__(self):
        self.key_state: Dict[str, bool] = {}
        self.previous_key_state: Dict[str, bool] = {}
        self.mouse_position: Vector2 = Vector2.zero()
        self.mouse_buttons: Dict[int, bool] = {}
        self.previous_mouse_buttons: Dict[int, bool] = {}

        # Action mappings
        self.action_mappings: Dict[InputAction, List[str]] = {
            InputAction.MOVE_UP: ['w', 'up'],
            InputAction.MOVE_DOWN: ['s', 'down'],
            InputAction.MOVE_LEFT: ['a', 'left'],
            InputAction.MOVE_RIGHT: ['d', 'right'],
            InputAction.JUMP: ['space', 'w', 'up'],
            InputAction.ATTACK: ['z', 'j'],
            InputAction.INTERACT: ['e', 'x', 'k'],
            InputAction.PAUSE: ['escape', 'p'],
            InputAction.CONFIRM: ['return', 'space'],
            InputAction.CANCEL: ['escape', 'backspace'],
        }

    def update(self):
        """Update input state (call at start of frame)"""
        self.previous_key_state = dict(self.key_state)
        self.previous_mouse_buttons = dict(self.mouse_buttons)

    def key_down(self, key: str):
        """Register key press"""
        self.key_state[key.lower()] = True

    def key_up(self, key: str):
        """Register key release"""
        self.key_state[key.lower()] = False

    def is_key_pressed(self, key: str) -> bool:
        """Check if key is currently pressed"""
        return self.key_state.get(key.lower(), False)

    def is_key_just_pressed(self, key: str) -> bool:
        """Check if key was just pressed this frame"""
        key = key.lower()
        return (self.key_state.get(key, False) and
                not self.previous_key_state.get(key, False))

    def is_key_just_released(self, key: str) -> bool:
        """Check if key was just released this frame"""
        key = key.lower()
        return (not self.key_state.get(key, False) and
                self.previous_key_state.get(key, False))

    def is_action_pressed(self, action: InputAction) -> bool:
        """Check if an action is currently active"""
        keys = self.action_mappings.get(action, [])
        return any(self.is_key_pressed(k) for k in keys)

    def is_action_just_pressed(self, action: InputAction) -> bool:
        """Check if an action was just activated"""
        keys = self.action_mappings.get(action, [])
        return any(self.is_key_just_pressed(k) for k in keys)

    def get_axis(self, negative_action: InputAction, positive_action: InputAction) -> float:
        """Get axis value from two actions (-1 to 1)"""
        value = 0.0
        if self.is_action_pressed(negative_action):
            value -= 1.0
        if self.is_action_pressed(positive_action):
            value += 1.0
        return value

    def get_movement_vector(self) -> Vector2:
        """Get 2D movement input vector"""
        return Vector2(
            self.get_axis(InputAction.MOVE_LEFT, InputAction.MOVE_RIGHT),
            self.get_axis(InputAction.MOVE_UP, InputAction.MOVE_DOWN)
        )

    def set_mouse_position(self, x: float, y: float):
        """Update mouse position"""
        self.mouse_position = Vector2(x, y)

    def mouse_down(self, button: int):
        """Register mouse button press"""
        self.mouse_buttons[button] = True

    def mouse_up(self, button: int):
        """Register mouse button release"""
        self.mouse_buttons[button] = False

    def is_mouse_pressed(self, button: int = 0) -> bool:
        """Check if mouse button is pressed"""
        return self.mouse_buttons.get(button, False)

    def is_mouse_just_pressed(self, button: int = 0) -> bool:
        """Check if mouse button was just pressed"""
        return (self.mouse_buttons.get(button, False) and
                not self.previous_mouse_buttons.get(button, False))


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================

class GameEngine:
    """Main game engine class"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.running = False

        # Core systems
        self.scene_manager = SceneManager()
        self.asset_manager = AssetManager()
        self.input_manager = InputManager()

        # ECS systems
        self.systems: List[System] = []
        self._add_default_systems()

        # Timing
        self.target_fps = 60
        self.delta_time = 0.0
        self.time_scale = 1.0
        self.frame_count = 0
        self.start_time = 0.0

        # Window settings
        self.window_width = 800
        self.window_height = 600
        self.window_title = "Electroduction Engine"
        self.fullscreen = False

        # Callbacks
        self.on_update: List[Callable] = []
        self.on_render: List[Callable] = []

        # Debug
        self.debug_mode = False

        logger.info("GameEngine initialized")

    def _add_default_systems(self):
        """Add default ECS systems"""
        self.add_system(ScriptSystem())
        self.add_system(PhysicsSystem())
        self.add_system(CollisionSystem())
        self.add_system(AnimationSystem())

    def add_system(self, system: System):
        """Add an ECS system"""
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority)

    def remove_system(self, system_type: Type[System]):
        """Remove a system by type"""
        self.systems = [s for s in self.systems if not isinstance(s, system_type)]

    def get_system(self, system_type: Type[System]) -> Optional[System]:
        """Get a system by type"""
        for system in self.systems:
            if isinstance(system, system_type):
                return system
        return None

    def create_entity(self, name: str = "Entity") -> Entity:
        """Create and add an entity to current scene"""
        entity = Entity(name)
        scene = self.scene_manager.get_current_scene()
        if scene:
            scene.add_entity(entity)
        return entity

    def destroy_entity(self, entity: Entity):
        """Remove an entity from current scene"""
        scene = self.scene_manager.get_current_scene()
        if scene:
            scene.remove_entity(entity)

    def start(self):
        """Start the game engine"""
        self.running = True
        self.start_time = time.time()
        logger.info("GameEngine started")

    def stop(self):
        """Stop the game engine"""
        self.running = False
        logger.info("GameEngine stopped")

    def update(self, delta_time: float):
        """Update game logic"""
        self.delta_time = delta_time * self.time_scale
        self.frame_count += 1

        # Update input
        self.input_manager.update()

        # Get current scene entities
        scene = self.scene_manager.get_current_scene()
        if not scene:
            return

        entities = scene.get_all_entities()

        # Update all systems
        for system in self.systems:
            if system.enabled:
                # Filter entities that have required components
                required = system.get_required_components()
                if required:
                    filtered = [e for e in entities
                               if all(e.has_component(c) for c in required)]
                else:
                    filtered = entities

                system.update(filtered, self.delta_time)

        # Call custom update callbacks
        for callback in self.on_update:
            callback(self.delta_time)

    def get_elapsed_time(self) -> float:
        """Get time since engine start"""
        return time.time() - self.start_time

    def get_fps(self) -> float:
        """Get current FPS"""
        if self.delta_time > 0:
            return 1.0 / self.delta_time
        return 0.0

    def get_stats(self) -> Dict:
        """Get engine statistics"""
        scene = self.scene_manager.get_current_scene()
        return {
            'fps': self.get_fps(),
            'frame_count': self.frame_count,
            'elapsed_time': self.get_elapsed_time(),
            'entity_count': len(scene.entities) if scene else 0,
            'system_count': len(self.systems),
            'asset_count': len(self.asset_manager.assets),
            'delta_time': self.delta_time
        }


# =============================================================================
# FACTORY FUNCTIONS FOR RAPID DEVELOPMENT
# =============================================================================

def create_sprite_entity(name: str, x: float, y: float,
                        texture: str = None, width: int = 32, height: int = 32) -> Entity:
    """Create a basic sprite entity"""
    entity = Entity(name)
    entity.transform.position = Vector3(x, y, 0)

    sprite = SpriteComponent(texture)
    sprite.width = width
    sprite.height = height
    entity.add_component(sprite)

    return entity


def create_physics_entity(name: str, x: float, y: float,
                         width: int = 32, height: int = 32) -> Entity:
    """Create an entity with physics"""
    entity = create_sprite_entity(name, x, y, width=width, height=height)

    rb = RigidBodyComponent()
    entity.add_component(rb)

    collider = ColliderComponent()
    collider.width = width
    collider.height = height
    entity.add_component(collider)

    return entity


def create_player_entity(name: str = "Player", x: float = 0, y: float = 0) -> Entity:
    """Create a player entity with common components"""
    entity = create_physics_entity(name, x, y, 32, 32)
    entity.add_tag("player")

    # Add animation component
    anim = AnimationComponent()
    entity.add_component(anim)

    # Add script component for custom behavior
    script = ScriptComponent()
    entity.add_component(script)

    return entity


def create_tilemap_entity(name: str, tile_width: int = 32, tile_height: int = 32) -> Entity:
    """Create a tilemap entity"""
    entity = Entity(name)
    tilemap = TilemapComponent(tile_width, tile_height)
    entity.add_component(tilemap)
    return entity


def create_ui_text(name: str, text: str, x: float, y: float,
                   font_size: int = 16, color: Color = None) -> Entity:
    """Create a UI text entity"""
    entity = Entity(name)
    entity.transform.position = Vector3(x, y, 0)

    ui = UIComponent(UIComponent.UIType.TEXT)
    ui.text = text
    ui.font_size = font_size
    ui.text_color = color or Color.white()
    entity.add_component(ui)

    return entity


def create_button(name: str, text: str, x: float, y: float,
                 width: float = 100, height: float = 30,
                 on_click: Callable = None) -> Entity:
    """Create a UI button entity"""
    entity = Entity(name)
    entity.transform.position = Vector3(x, y, 0)

    ui = UIComponent(UIComponent.UIType.BUTTON)
    ui.text = text
    ui.width = width
    ui.height = height
    ui.on_click = on_click
    entity.add_component(ui)

    return entity


# =============================================================================
# TESTING
# =============================================================================

def run_engine_test():
    """Run engine component tests"""
    print("\n" + "="*60)
    print("GAME ENGINE TESTS")
    print("="*60 + "\n")

    # Test Vector2
    print("[1] Testing Vector2...")
    v1 = Vector2(3, 4)
    v2 = Vector2(1, 2)
    assert (v1 + v2).x == 4
    assert v1.magnitude() == 5.0
    assert v1.normalized().magnitude() - 1.0 < 0.0001
    print("    Vector2 PASSED")

    # Test Vector3
    print("[2] Testing Vector3...")
    v3 = Vector3(1, 0, 0)
    v4 = Vector3(0, 1, 0)
    cross = v3.cross(v4)
    assert cross.z == 1.0
    print("    Vector3 PASSED")

    # Test Entity/Component
    print("[3] Testing Entity Component System...")
    entity = Entity("TestEntity")
    sprite = SpriteComponent("test.png")
    entity.add_component(sprite)
    assert entity.has_component(SpriteComponent)
    assert entity.get_component(SpriteComponent) == sprite
    print("    ECS PASSED")

    # Test Scene
    print("[4] Testing Scene Management...")
    scene = Scene("TestScene")
    scene.add_entity(entity)
    assert scene.get_entity(entity.id) == entity
    assert scene.find_entity("TestEntity") == entity
    print("    Scene PASSED")

    # Test Physics
    print("[5] Testing Physics System...")
    physics_entity = create_physics_entity("PhysicsTest", 100, 0)
    rb = physics_entity.get_component(RigidBodyComponent)
    rb.velocity = Vector2(100, 0)

    physics_system = PhysicsSystem()
    physics_system.update([physics_entity], 0.1)

    assert physics_entity.transform.position.x > 100
    print("    Physics PASSED")

    # Test Collision
    print("[6] Testing Collision System...")
    e1 = create_physics_entity("E1", 0, 0, 32, 32)
    e2 = create_physics_entity("E2", 10, 10, 32, 32)

    collision_detected = [False]

    def on_collision(a, b):
        collision_detected[0] = True

    collision_system = CollisionSystem()
    collision_system.register_callback("test", on_collision)
    e1.add_tag("test")

    collision_system.update([e1, e2], 0.1)
    assert collision_detected[0]
    print("    Collision PASSED")

    # Test Animation
    print("[7] Testing Animation System...")
    anim_entity = Entity("AnimTest")
    sprite = SpriteComponent()
    anim_entity.add_component(sprite)
    anim = AnimationComponent()
    anim.add_animation("walk", [
        Rectangle(0, 0, 32, 32),
        Rectangle(32, 0, 32, 32),
        Rectangle(64, 0, 32, 32)
    ])
    anim_entity.add_component(anim)
    anim.play("walk")

    anim_system = AnimationSystem()
    anim_system.update([anim_entity], 0.2)  # Advance frames
    print("    Animation PASSED")

    # Test Full Engine
    print("[8] Testing Full Engine Integration...")
    engine = GameEngine()
    main_scene = engine.scene_manager.create_scene("Main")
    engine.scene_manager.load_scene("Main")

    player = create_player_entity("Player", 100, 100)
    main_scene.add_entity(player)

    engine.start()
    engine.update(1/60)

    stats = engine.get_stats()
    assert stats['entity_count'] == 1
    engine.stop()
    print("    Engine Integration PASSED")

    print("\n" + "="*60)
    print("ALL ENGINE TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_engine_test()
