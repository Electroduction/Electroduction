#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION GAME ENGINE - VISUAL EDITOR
===============================================================================
A visual drag-and-drop game editor featuring:
- Scene hierarchy view
- Properties inspector
- Asset browser
- Tilemap editor
- Visual scripting nodes
- Real-time preview
- Undo/redo support

This editor provides an intuitive interface for:
- Creating and placing game objects
- Editing entity properties
- Designing levels with tilemaps
- Setting up animations
- Configuring physics
- Creating UI layouts
===============================================================================
"""

import os
import sys
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any, Callable, Type
from enum import Enum, auto
from abc import ABC, abstractmethod

# Try to import tkinter for GUI
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, colorchooser
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
    print("Note: tkinter not available, running in headless mode")

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.engine import (
        Entity, Component, Scene, Vector2, Vector3, Color, Rectangle,
        SpriteComponent, RigidBodyComponent, ColliderComponent,
        ScriptComponent, TilemapComponent, AnimationComponent,
        UIComponent, GameEngine
    )
except ImportError:
    pass


# =============================================================================
# EDITOR DATA STRUCTURES
# =============================================================================

class EditorTool(Enum):
    """Editor tools"""
    SELECT = auto()
    MOVE = auto()
    ROTATE = auto()
    SCALE = auto()
    PAINT_TILE = auto()
    ERASE_TILE = auto()
    PLACE_ENTITY = auto()


@dataclass
class EditorAction:
    """Represents an undoable editor action"""
    action_type: str
    entity_id: Optional[str] = None
    component_type: Optional[str] = None
    property_name: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            'type': self.action_type,
            'entity': self.entity_id,
            'component': self.component_type,
            'property': self.property_name,
            'old': str(self.old_value),
            'new': str(self.new_value),
        }


class UndoRedoManager:
    """Manages undo/redo operations"""

    def __init__(self, max_history: int = 100):
        self.undo_stack: List[EditorAction] = []
        self.redo_stack: List[EditorAction] = []
        self.max_history = max_history

    def record_action(self, action: EditorAction):
        """Record a new action"""
        self.undo_stack.append(action)
        self.redo_stack.clear()

        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self) -> Optional[EditorAction]:
        if self.undo_stack:
            action = self.undo_stack.pop()
            self.redo_stack.append(action)
            return action
        return None

    def redo(self) -> Optional[EditorAction]:
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.undo_stack.append(action)
            return action
        return None


class EntityTemplate:
    """Template for creating entities (prefabs)"""

    def __init__(self, name: str):
        self.name = name
        self.components: Dict[str, Dict] = {}
        self.tags: List[str] = []
        self.children: List['EntityTemplate'] = []

    def add_component(self, component_type: str, properties: Dict):
        """Add a component configuration"""
        self.components[component_type] = properties

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'components': self.components,
            'tags': self.tags,
            'children': [c.to_dict() for c in self.children]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EntityTemplate':
        template = cls(data.get('name', 'Template'))
        template.components = data.get('components', {})
        template.tags = data.get('tags', [])
        template.children = [cls.from_dict(c) for c in data.get('children', [])]
        return template


# =============================================================================
# BUILT-IN ENTITY TEMPLATES
# =============================================================================

class TemplateLibrary:
    """Library of built-in entity templates"""

    def __init__(self):
        self.templates: Dict[str, EntityTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Load built-in templates"""
        # Player template
        player = EntityTemplate("Player")
        player.add_component("SpriteComponent", {
            "color": [100, 200, 100],
            "width": 32, "height": 32
        })
        player.add_component("RigidBodyComponent", {
            "body_type": "DYNAMIC",
            "mass": 1.0,
            "gravity_scale": 1.0
        })
        player.add_component("ColliderComponent", {
            "collider_type": "BOX",
            "width": 32, "height": 32
        })
        player.add_component("AnimationComponent", {})
        player.tags = ["player", "controllable"]
        self.templates["Player"] = player

        # Enemy template
        enemy = EntityTemplate("Enemy")
        enemy.add_component("SpriteComponent", {
            "color": [200, 100, 100],
            "width": 32, "height": 32
        })
        enemy.add_component("RigidBodyComponent", {
            "body_type": "DYNAMIC"
        })
        enemy.add_component("ColliderComponent", {
            "collider_type": "BOX",
            "width": 32, "height": 32
        })
        enemy.tags = ["enemy", "hostile"]
        self.templates["Enemy"] = enemy

        # Platform template
        platform = EntityTemplate("Platform")
        platform.add_component("SpriteComponent", {
            "color": [100, 100, 100],
            "width": 128, "height": 32
        })
        platform.add_component("ColliderComponent", {
            "collider_type": "BOX",
            "width": 128, "height": 32
        })
        platform.tags = ["platform", "solid"]
        self.templates["Platform"] = platform

        # Collectible template
        collectible = EntityTemplate("Collectible")
        collectible.add_component("SpriteComponent", {
            "color": [255, 215, 0],
            "width": 16, "height": 16
        })
        collectible.add_component("ColliderComponent", {
            "collider_type": "CIRCLE",
            "radius": 8,
            "is_trigger": True
        })
        collectible.tags = ["collectible", "pickup"]
        self.templates["Collectible"] = collectible

        # Camera template
        camera = EntityTemplate("Camera")
        camera.tags = ["camera", "main_camera"]
        self.templates["Camera"] = camera

        # Light template (for 2D lighting)
        light = EntityTemplate("Light")
        light.add_component("LightComponent", {
            "color": [255, 255, 200],
            "intensity": 1.0,
            "radius": 200
        })
        light.tags = ["light"]
        self.templates["Light"] = light

        # Spawn Point template
        spawn = EntityTemplate("SpawnPoint")
        spawn.tags = ["spawn", "checkpoint"]
        self.templates["SpawnPoint"] = spawn

        # Trigger Zone template
        trigger = EntityTemplate("TriggerZone")
        trigger.add_component("ColliderComponent", {
            "collider_type": "BOX",
            "width": 64, "height": 64,
            "is_trigger": True
        })
        trigger.tags = ["trigger"]
        self.templates["TriggerZone"] = trigger

    def get_template(self, name: str) -> Optional[EntityTemplate]:
        return self.templates.get(name)

    def get_all_templates(self) -> List[str]:
        return list(self.templates.keys())

    def add_template(self, template: EntityTemplate):
        self.templates[template.name] = template


# =============================================================================
# PROPERTY EDITORS
# =============================================================================

class PropertyEditor(ABC):
    """Base class for property editors"""

    @abstractmethod
    def get_widget_data(self) -> Dict:
        """Get widget configuration for GUI"""
        pass

    @abstractmethod
    def validate(self, value: Any) -> Tuple[bool, Any]:
        """Validate and convert input value"""
        pass


class NumberEditor(PropertyEditor):
    """Editor for numeric properties"""

    def __init__(self, min_val: float = None, max_val: float = None,
                 step: float = 1.0, integer: bool = False):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.integer = integer

    def get_widget_data(self) -> Dict:
        return {
            'type': 'number',
            'min': self.min_val,
            'max': self.max_val,
            'step': self.step,
            'integer': self.integer
        }

    def validate(self, value: Any) -> Tuple[bool, Any]:
        try:
            num = int(value) if self.integer else float(value)
            if self.min_val is not None and num < self.min_val:
                return False, self.min_val
            if self.max_val is not None and num > self.max_val:
                return False, self.max_val
            return True, num
        except:
            return False, None


class Vector2Editor(PropertyEditor):
    """Editor for Vector2 properties"""

    def get_widget_data(self) -> Dict:
        return {'type': 'vector2', 'components': ['x', 'y']}

    def validate(self, value: Any) -> Tuple[bool, Any]:
        if isinstance(value, (list, tuple)) and len(value) == 2:
            try:
                return True, Vector2(float(value[0]), float(value[1]))
            except:
                pass
        return False, Vector2.zero()


class ColorEditor(PropertyEditor):
    """Editor for Color properties"""

    def get_widget_data(self) -> Dict:
        return {'type': 'color'}

    def validate(self, value: Any) -> Tuple[bool, Any]:
        if isinstance(value, (list, tuple)):
            try:
                if len(value) >= 3:
                    return True, Color(int(value[0]), int(value[1]), int(value[2]),
                                      int(value[3]) if len(value) > 3 else 255)
            except:
                pass
        return False, Color.white()


class StringEditor(PropertyEditor):
    """Editor for string properties"""

    def __init__(self, multiline: bool = False, options: List[str] = None):
        self.multiline = multiline
        self.options = options

    def get_widget_data(self) -> Dict:
        return {
            'type': 'dropdown' if self.options else ('textarea' if self.multiline else 'text'),
            'options': self.options
        }

    def validate(self, value: Any) -> Tuple[bool, Any]:
        return True, str(value)


class BoolEditor(PropertyEditor):
    """Editor for boolean properties"""

    def get_widget_data(self) -> Dict:
        return {'type': 'checkbox'}

    def validate(self, value: Any) -> Tuple[bool, Any]:
        return True, bool(value)


# =============================================================================
# COMPONENT EDITORS
# =============================================================================

COMPONENT_EDITORS = {
    'SpriteComponent': {
        'texture_path': StringEditor(),
        'color': ColorEditor(),
        'width': NumberEditor(min_val=1, max_val=1024, integer=True),
        'height': NumberEditor(min_val=1, max_val=1024, integer=True),
        'flip_x': BoolEditor(),
        'flip_y': BoolEditor(),
        'layer': NumberEditor(min_val=0, max_val=100, integer=True),
        'visible': BoolEditor(),
    },
    'RigidBodyComponent': {
        'body_type': StringEditor(options=['STATIC', 'DYNAMIC', 'KINEMATIC']),
        'mass': NumberEditor(min_val=0.01, max_val=1000, step=0.1),
        'drag': NumberEditor(min_val=0, max_val=10, step=0.1),
        'gravity_scale': NumberEditor(min_val=-10, max_val=10, step=0.1),
        'use_gravity': BoolEditor(),
    },
    'ColliderComponent': {
        'collider_type': StringEditor(options=['BOX', 'CIRCLE']),
        'width': NumberEditor(min_val=1, max_val=1024),
        'height': NumberEditor(min_val=1, max_val=1024),
        'radius': NumberEditor(min_val=1, max_val=512),
        'offset': Vector2Editor(),
        'is_trigger': BoolEditor(),
        'collision_layer': NumberEditor(min_val=0, max_val=31, integer=True),
    },
    'AnimationComponent': {
        'frame_time': NumberEditor(min_val=0.01, max_val=5, step=0.01),
        'loop': BoolEditor(),
    },
    'UIComponent': {
        'ui_type': StringEditor(options=['TEXT', 'IMAGE', 'BUTTON', 'PANEL', 'SLIDER', 'INPUT']),
        'text': StringEditor(multiline=True),
        'font_size': NumberEditor(min_val=8, max_val=72, integer=True),
        'text_color': ColorEditor(),
        'background_color': ColorEditor(),
        'width': NumberEditor(min_val=10, max_val=2000),
        'height': NumberEditor(min_val=10, max_val=2000),
        'interactive': BoolEditor(),
    },
    'TilemapComponent': {
        'tile_width': NumberEditor(min_val=8, max_val=128, integer=True),
        'tile_height': NumberEditor(min_val=8, max_val=128, integer=True),
        'tileset_path': StringEditor(),
        'tileset_columns': NumberEditor(min_val=1, max_val=100, integer=True),
    },
}


# =============================================================================
# VISUAL SCRIPTING
# =============================================================================

class ScriptNodeType(Enum):
    """Types of visual script nodes"""
    EVENT = auto()      # Triggers (on_start, on_update, on_collision)
    ACTION = auto()     # Do something
    CONDITION = auto()  # Branch based on condition
    VARIABLE = auto()   # Get/Set variables
    MATH = auto()       # Math operations
    FLOW = auto()       # Flow control (loops, sequences)


@dataclass
class ScriptNode:
    """Visual script node"""
    id: str
    node_type: ScriptNodeType
    name: str
    position: Tuple[float, float]
    inputs: Dict[str, str] = field(default_factory=dict)  # name -> type
    outputs: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    connections: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # output -> (node_id, input)


class VisualScriptGraph:
    """Visual script graph (behavior graph)"""

    def __init__(self, name: str = "Script"):
        self.name = name
        self.nodes: Dict[str, ScriptNode] = {}
        self.variables: Dict[str, Any] = {}

    def add_node(self, node: ScriptNode):
        self.nodes[node.id] = node

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]

    def connect(self, from_node: str, from_output: str,
                to_node: str, to_input: str):
        """Connect two nodes"""
        if from_node in self.nodes:
            self.nodes[from_node].connections[from_output] = (to_node, to_input)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'nodes': {k: {
                'id': n.id,
                'type': n.node_type.name,
                'name': n.name,
                'position': n.position,
                'inputs': n.inputs,
                'outputs': n.outputs,
                'properties': n.properties,
                'connections': n.connections
            } for k, n in self.nodes.items()},
            'variables': self.variables
        }


# Built-in visual script nodes
SCRIPT_NODE_LIBRARY = {
    # Events
    'OnStart': {
        'type': ScriptNodeType.EVENT,
        'outputs': {'exec': 'flow'},
        'description': 'Triggered when the game starts'
    },
    'OnUpdate': {
        'type': ScriptNodeType.EVENT,
        'outputs': {'exec': 'flow', 'delta_time': 'float'},
        'description': 'Triggered every frame'
    },
    'OnCollision': {
        'type': ScriptNodeType.EVENT,
        'outputs': {'exec': 'flow', 'other': 'entity'},
        'description': 'Triggered on collision'
    },
    'OnTriggerEnter': {
        'type': ScriptNodeType.EVENT,
        'outputs': {'exec': 'flow', 'other': 'entity'},
        'description': 'Triggered when entering a trigger'
    },

    # Actions
    'Move': {
        'type': ScriptNodeType.ACTION,
        'inputs': {'exec': 'flow', 'direction': 'vector2', 'speed': 'float'},
        'outputs': {'exec': 'flow'},
        'description': 'Move the entity'
    },
    'Jump': {
        'type': ScriptNodeType.ACTION,
        'inputs': {'exec': 'flow', 'force': 'float'},
        'outputs': {'exec': 'flow'},
        'description': 'Make the entity jump'
    },
    'PlayAnimation': {
        'type': ScriptNodeType.ACTION,
        'inputs': {'exec': 'flow', 'name': 'string'},
        'outputs': {'exec': 'flow'},
        'description': 'Play an animation'
    },
    'PlaySound': {
        'type': ScriptNodeType.ACTION,
        'inputs': {'exec': 'flow', 'sound': 'string'},
        'outputs': {'exec': 'flow'},
        'description': 'Play a sound effect'
    },
    'Destroy': {
        'type': ScriptNodeType.ACTION,
        'inputs': {'exec': 'flow', 'target': 'entity'},
        'outputs': {'exec': 'flow'},
        'description': 'Destroy an entity'
    },
    'Spawn': {
        'type': ScriptNodeType.ACTION,
        'inputs': {'exec': 'flow', 'template': 'string', 'position': 'vector2'},
        'outputs': {'exec': 'flow', 'spawned': 'entity'},
        'description': 'Spawn a new entity'
    },

    # Conditions
    'If': {
        'type': ScriptNodeType.CONDITION,
        'inputs': {'exec': 'flow', 'condition': 'bool'},
        'outputs': {'true': 'flow', 'false': 'flow'},
        'description': 'Branch based on condition'
    },
    'Compare': {
        'type': ScriptNodeType.CONDITION,
        'inputs': {'a': 'float', 'b': 'float'},
        'outputs': {'equal': 'bool', 'greater': 'bool', 'less': 'bool'},
        'description': 'Compare two values'
    },

    # Variables
    'GetVariable': {
        'type': ScriptNodeType.VARIABLE,
        'inputs': {'name': 'string'},
        'outputs': {'value': 'any'},
        'description': 'Get a variable value'
    },
    'SetVariable': {
        'type': ScriptNodeType.VARIABLE,
        'inputs': {'exec': 'flow', 'name': 'string', 'value': 'any'},
        'outputs': {'exec': 'flow'},
        'description': 'Set a variable value'
    },

    # Math
    'Add': {
        'type': ScriptNodeType.MATH,
        'inputs': {'a': 'float', 'b': 'float'},
        'outputs': {'result': 'float'},
        'description': 'Add two numbers'
    },
    'Multiply': {
        'type': ScriptNodeType.MATH,
        'inputs': {'a': 'float', 'b': 'float'},
        'outputs': {'result': 'float'},
        'description': 'Multiply two numbers'
    },
    'Random': {
        'type': ScriptNodeType.MATH,
        'inputs': {'min': 'float', 'max': 'float'},
        'outputs': {'result': 'float'},
        'description': 'Generate random number'
    },

    # Flow
    'Sequence': {
        'type': ScriptNodeType.FLOW,
        'inputs': {'exec': 'flow'},
        'outputs': {'out_1': 'flow', 'out_2': 'flow', 'out_3': 'flow'},
        'description': 'Execute outputs in sequence'
    },
    'ForLoop': {
        'type': ScriptNodeType.FLOW,
        'inputs': {'exec': 'flow', 'count': 'int'},
        'outputs': {'body': 'flow', 'index': 'int', 'complete': 'flow'},
        'description': 'Loop a number of times'
    },
    'Delay': {
        'type': ScriptNodeType.FLOW,
        'inputs': {'exec': 'flow', 'seconds': 'float'},
        'outputs': {'exec': 'flow'},
        'description': 'Wait before continuing'
    },
}


# =============================================================================
# EDITOR STATE
# =============================================================================

class EditorState:
    """Manages the editor state"""

    def __init__(self):
        self.current_scene: Optional[Scene] = None
        self.selected_entities: List[str] = []
        self.current_tool: EditorTool = EditorTool.SELECT
        self.current_layer: int = 0
        self.grid_size: int = 32
        self.snap_to_grid: bool = True
        self.show_colliders: bool = True
        self.show_grid: bool = True
        self.zoom: float = 1.0
        self.camera_offset: Vector2 = Vector2.zero()

        # Undo/Redo
        self.undo_manager = UndoRedoManager()

        # Templates
        self.template_library = TemplateLibrary()

        # Clipboard
        self.clipboard: List[EntityTemplate] = []

        # Project
        self.project_path: Optional[str] = None
        self.unsaved_changes: bool = False

    def select_entity(self, entity_id: str, add_to_selection: bool = False):
        """Select an entity"""
        if not add_to_selection:
            self.selected_entities.clear()
        if entity_id not in self.selected_entities:
            self.selected_entities.append(entity_id)

    def deselect_all(self):
        """Deselect all entities"""
        self.selected_entities.clear()

    def copy_selection(self):
        """Copy selected entities to clipboard"""
        if not self.current_scene:
            return

        self.clipboard.clear()
        for entity_id in self.selected_entities:
            entity = self.current_scene.get_entity(entity_id)
            if entity:
                template = EntityTemplate(entity.name)
                template.tags = list(entity.tags)
                # Copy component data
                for comp_type, comp in entity.components.items():
                    template.components[comp_type.__name__] = {}
                self.clipboard.append(template)

    def paste(self):
        """Paste entities from clipboard"""
        if not self.current_scene or not self.clipboard:
            return []

        pasted = []
        for template in self.clipboard:
            entity = Entity(f"{template.name}_copy")
            entity.tags = set(template.tags)
            self.current_scene.add_entity(entity)
            pasted.append(entity.id)

            # Record action
            self.undo_manager.record_action(EditorAction(
                action_type="create_entity",
                entity_id=entity.id
            ))

        self.unsaved_changes = True
        return pasted


# =============================================================================
# TKINTER GUI EDITOR (if available)
# =============================================================================

if TK_AVAILABLE:
    class GameEditor:
        """Main editor window using Tkinter"""

        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Electroduction Game Editor")
            self.root.geometry("1400x900")

            self.state = EditorState()
            self.engine = None

            self._setup_menu()
            self._setup_ui()

        def _setup_menu(self):
            """Setup menu bar"""
            menubar = tk.Menu(self.root)

            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label="New Project", command=self._new_project)
            file_menu.add_command(label="Open Project", command=self._open_project)
            file_menu.add_command(label="Save", command=self._save_project)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.root.quit)
            menubar.add_cascade(label="File", menu=file_menu)

            # Edit menu
            edit_menu = tk.Menu(menubar, tearoff=0)
            edit_menu.add_command(label="Undo", command=self._undo)
            edit_menu.add_command(label="Redo", command=self._redo)
            edit_menu.add_separator()
            edit_menu.add_command(label="Copy", command=self._copy)
            edit_menu.add_command(label="Paste", command=self._paste)
            edit_menu.add_command(label="Delete", command=self._delete_selected)
            menubar.add_cascade(label="Edit", menu=edit_menu)

            # View menu
            view_menu = tk.Menu(menubar, tearoff=0)
            view_menu.add_checkbutton(label="Show Grid")
            view_menu.add_checkbutton(label="Show Colliders")
            view_menu.add_separator()
            view_menu.add_command(label="Reset Zoom", command=self._reset_zoom)
            menubar.add_cascade(label="View", menu=view_menu)

            # Entity menu
            entity_menu = tk.Menu(menubar, tearoff=0)
            entity_menu.add_command(label="Create Empty", command=self._create_empty_entity)
            entity_menu.add_separator()
            for template_name in self.state.template_library.get_all_templates():
                entity_menu.add_command(
                    label=f"Create {template_name}",
                    command=lambda n=template_name: self._create_from_template(n)
                )
            menubar.add_cascade(label="Entity", menu=entity_menu)

            self.root.config(menu=menubar)

        def _setup_ui(self):
            """Setup main UI layout"""
            # Main paned window
            main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            main_pane.pack(fill=tk.BOTH, expand=True)

            # Left panel - Hierarchy
            left_frame = ttk.Frame(main_pane, width=250)
            ttk.Label(left_frame, text="Scene Hierarchy", font=('Arial', 10, 'bold')).pack(pady=5)

            self.hierarchy_tree = ttk.Treeview(left_frame)
            self.hierarchy_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.hierarchy_tree.bind('<<TreeviewSelect>>', self._on_hierarchy_select)

            main_pane.add(left_frame)

            # Center panel - Viewport
            center_frame = ttk.Frame(main_pane)

            # Toolbar
            toolbar = ttk.Frame(center_frame)
            toolbar.pack(fill=tk.X, pady=5)

            self.tool_buttons = {}
            for tool in [EditorTool.SELECT, EditorTool.MOVE, EditorTool.PAINT_TILE]:
                btn = ttk.Button(toolbar, text=tool.name, command=lambda t=tool: self._set_tool(t))
                btn.pack(side=tk.LEFT, padx=2)
                self.tool_buttons[tool] = btn

            # Canvas (viewport)
            self.canvas = tk.Canvas(center_frame, bg='#2d2d2d', highlightthickness=0)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.bind('<Button-1>', self._on_canvas_click)
            self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
            self.canvas.bind('<MouseWheel>', self._on_canvas_scroll)

            main_pane.add(center_frame)

            # Right panel - Inspector
            right_frame = ttk.Frame(main_pane, width=300)
            ttk.Label(right_frame, text="Inspector", font=('Arial', 10, 'bold')).pack(pady=5)

            self.inspector_frame = ttk.Frame(right_frame)
            self.inspector_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            main_pane.add(right_frame)

            # Status bar
            self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
            self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        def _set_tool(self, tool: EditorTool):
            """Set current editor tool"""
            self.state.current_tool = tool
            self.status_bar.config(text=f"Tool: {tool.name}")

        def _new_project(self):
            """Create new project"""
            self.state.current_scene = Scene("Main")
            self._refresh_hierarchy()
            self.status_bar.config(text="New project created")

        def _open_project(self):
            """Open existing project"""
            path = filedialog.askdirectory(title="Open Project")
            if path:
                self.state.project_path = path
                self.status_bar.config(text=f"Opened: {path}")

        def _save_project(self):
            """Save current project"""
            if self.state.current_scene:
                if not self.state.project_path:
                    path = filedialog.asksaveasfilename(
                        defaultextension=".json",
                        filetypes=[("JSON files", "*.json")]
                    )
                    if path:
                        self.state.project_path = path

                if self.state.project_path:
                    self.state.current_scene.save(self.state.project_path)
                    self.state.unsaved_changes = False
                    self.status_bar.config(text=f"Saved: {self.state.project_path}")

        def _undo(self):
            """Undo last action"""
            action = self.state.undo_manager.undo()
            if action:
                self.status_bar.config(text=f"Undo: {action.action_type}")
                self._refresh_hierarchy()

        def _redo(self):
            """Redo last undone action"""
            action = self.state.undo_manager.redo()
            if action:
                self.status_bar.config(text=f"Redo: {action.action_type}")
                self._refresh_hierarchy()

        def _copy(self):
            """Copy selected entities"""
            self.state.copy_selection()
            self.status_bar.config(text="Copied to clipboard")

        def _paste(self):
            """Paste from clipboard"""
            pasted = self.state.paste()
            if pasted:
                self._refresh_hierarchy()
                self.status_bar.config(text=f"Pasted {len(pasted)} entities")

        def _delete_selected(self):
            """Delete selected entities"""
            if self.state.current_scene and self.state.selected_entities:
                for entity_id in self.state.selected_entities:
                    entity = self.state.current_scene.get_entity(entity_id)
                    if entity:
                        self.state.current_scene.remove_entity(entity)
                self.state.selected_entities.clear()
                self._refresh_hierarchy()
                self.status_bar.config(text="Deleted selected entities")

        def _reset_zoom(self):
            """Reset viewport zoom"""
            self.state.zoom = 1.0
            self._refresh_canvas()

        def _create_empty_entity(self):
            """Create empty entity"""
            if self.state.current_scene:
                entity = Entity("New Entity")
                self.state.current_scene.add_entity(entity)
                self._refresh_hierarchy()

        def _create_from_template(self, template_name: str):
            """Create entity from template"""
            template = self.state.template_library.get_template(template_name)
            if template and self.state.current_scene:
                entity = Entity(template_name)
                entity.tags = set(template.tags)
                self.state.current_scene.add_entity(entity)
                self._refresh_hierarchy()
                self.status_bar.config(text=f"Created {template_name}")

        def _refresh_hierarchy(self):
            """Refresh hierarchy tree"""
            self.hierarchy_tree.delete(*self.hierarchy_tree.get_children())

            if self.state.current_scene:
                for entity in self.state.current_scene.root_entities:
                    self._add_entity_to_tree(entity, '')

        def _add_entity_to_tree(self, entity: Entity, parent: str):
            """Add entity to hierarchy tree"""
            item = self.hierarchy_tree.insert(parent, 'end', entity.id, text=entity.name)
            for child in entity.children:
                self._add_entity_to_tree(child, item)

        def _on_hierarchy_select(self, event):
            """Handle hierarchy selection"""
            selection = self.hierarchy_tree.selection()
            if selection:
                self.state.select_entity(selection[0])
                self._refresh_inspector()

        def _refresh_inspector(self):
            """Refresh inspector panel"""
            # Clear inspector
            for widget in self.inspector_frame.winfo_children():
                widget.destroy()

            if not self.state.selected_entities or not self.state.current_scene:
                ttk.Label(self.inspector_frame, text="No selection").pack()
                return

            entity_id = self.state.selected_entities[0]
            entity = self.state.current_scene.get_entity(entity_id)
            if not entity:
                return

            # Entity name
            ttk.Label(self.inspector_frame, text="Name:").pack(anchor=tk.W)
            name_entry = ttk.Entry(self.inspector_frame)
            name_entry.insert(0, entity.name)
            name_entry.pack(fill=tk.X, pady=2)

            # Tags
            ttk.Label(self.inspector_frame, text="Tags:").pack(anchor=tk.W)
            tags_entry = ttk.Entry(self.inspector_frame)
            tags_entry.insert(0, ', '.join(entity.tags))
            tags_entry.pack(fill=tk.X, pady=2)

            # Transform
            ttk.Separator(self.inspector_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            ttk.Label(self.inspector_frame, text="Transform", font=('Arial', 9, 'bold')).pack(anchor=tk.W)

            pos_frame = ttk.Frame(self.inspector_frame)
            pos_frame.pack(fill=tk.X)
            ttk.Label(pos_frame, text="Position:").pack(side=tk.LEFT)
            ttk.Entry(pos_frame, width=8).pack(side=tk.LEFT, padx=2)
            ttk.Entry(pos_frame, width=8).pack(side=tk.LEFT, padx=2)
            ttk.Entry(pos_frame, width=8).pack(side=tk.LEFT, padx=2)

            # Components
            ttk.Separator(self.inspector_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            ttk.Label(self.inspector_frame, text="Components", font=('Arial', 9, 'bold')).pack(anchor=tk.W)

            for comp_type, comp in entity.components.items():
                comp_frame = ttk.LabelFrame(self.inspector_frame, text=comp_type.__name__)
                comp_frame.pack(fill=tk.X, pady=5)
                ttk.Label(comp_frame, text=f"[{comp_type.__name__}]").pack()

            # Add Component button
            add_btn = ttk.Button(self.inspector_frame, text="Add Component")
            add_btn.pack(pady=10)

        def _refresh_canvas(self):
            """Refresh canvas viewport"""
            self.canvas.delete('all')

            if not self.state.current_scene:
                return

            # Draw grid
            if self.state.show_grid:
                self._draw_grid()

            # Draw entities
            for entity in self.state.current_scene.get_all_entities():
                self._draw_entity(entity)

        def _draw_grid(self):
            """Draw editor grid"""
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            size = int(self.state.grid_size * self.state.zoom)

            for x in range(0, w, size):
                self.canvas.create_line(x, 0, x, h, fill='#3d3d3d')
            for y in range(0, h, size):
                self.canvas.create_line(0, y, w, y, fill='#3d3d3d')

        def _draw_entity(self, entity: Entity):
            """Draw an entity on canvas"""
            x = entity.transform.position.x * self.state.zoom
            y = entity.transform.position.y * self.state.zoom

            sprite = entity.get_component(SpriteComponent) if hasattr(entity, 'get_component') else None

            if sprite:
                w = sprite.width * self.state.zoom
                h = sprite.height * self.state.zoom
                color = sprite.color.to_hex() if hasattr(sprite.color, 'to_hex') else '#ffffff'
            else:
                w = 32 * self.state.zoom
                h = 32 * self.state.zoom
                color = '#ffffff'

            # Draw rectangle
            rect = self.canvas.create_rectangle(
                x - w/2, y - h/2, x + w/2, y + h/2,
                fill=color, outline='#ffffff'
            )

            # Highlight if selected
            if entity.id in self.state.selected_entities:
                self.canvas.create_rectangle(
                    x - w/2 - 2, y - h/2 - 2, x + w/2 + 2, y + h/2 + 2,
                    outline='#00ff00', width=2
                )

        def _on_canvas_click(self, event):
            """Handle canvas click"""
            if self.state.current_tool == EditorTool.SELECT:
                # Find entity at position
                x = event.x / self.state.zoom
                y = event.y / self.state.zoom

                if self.state.current_scene:
                    for entity in self.state.current_scene.get_all_entities():
                        ex = entity.transform.position.x
                        ey = entity.transform.position.y
                        if abs(x - ex) < 16 and abs(y - ey) < 16:
                            self.state.select_entity(entity.id)
                            self._refresh_inspector()
                            self._refresh_canvas()
                            return

                self.state.deselect_all()
                self._refresh_inspector()
                self._refresh_canvas()

        def _on_canvas_drag(self, event):
            """Handle canvas drag"""
            if self.state.current_tool == EditorTool.MOVE and self.state.selected_entities:
                if self.state.current_scene:
                    for entity_id in self.state.selected_entities:
                        entity = self.state.current_scene.get_entity(entity_id)
                        if entity:
                            x = event.x / self.state.zoom
                            y = event.y / self.state.zoom

                            if self.state.snap_to_grid:
                                x = round(x / self.state.grid_size) * self.state.grid_size
                                y = round(y / self.state.grid_size) * self.state.grid_size

                            entity.transform.position.x = x
                            entity.transform.position.y = y

                    self._refresh_canvas()

        def _on_canvas_scroll(self, event):
            """Handle canvas scroll (zoom)"""
            if event.delta > 0:
                self.state.zoom = min(4.0, self.state.zoom * 1.1)
            else:
                self.state.zoom = max(0.25, self.state.zoom / 1.1)
            self._refresh_canvas()

        def run(self):
            """Run the editor"""
            self._new_project()
            self._refresh_canvas()
            self.root.mainloop()


# =============================================================================
# CONSOLE EDITOR (Fallback)
# =============================================================================

class ConsoleEditor:
    """Console-based editor for when GUI is not available"""

    def __init__(self):
        self.state = EditorState()
        self.running = False

    def run(self):
        """Run console editor"""
        print("\n" + "="*60)
        print("ELECTRODUCTION GAME EDITOR - Console Mode")
        print("="*60)
        print("\nCommands:")
        print("  new              - Create new scene")
        print("  create <type>    - Create entity from template")
        print("  list             - List all entities")
        print("  select <id>      - Select entity")
        print("  move <x> <y>     - Move selected entity")
        print("  delete           - Delete selected entity")
        print("  templates        - List available templates")
        print("  save <file>      - Save scene")
        print("  quit             - Exit editor")
        print()

        self.running = True
        while self.running:
            try:
                cmd = input("editor> ").strip().split()
                if not cmd:
                    continue

                self._process_command(cmd)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        print("Editor closed.")

    def _process_command(self, cmd: List[str]):
        """Process editor command"""
        action = cmd[0].lower()

        if action == 'quit' or action == 'exit':
            self.running = False

        elif action == 'new':
            self.state.current_scene = Scene("Main")
            print("Created new scene")

        elif action == 'templates':
            print("Available templates:")
            for name in self.state.template_library.get_all_templates():
                print(f"  - {name}")

        elif action == 'create':
            if len(cmd) < 2:
                print("Usage: create <template_name>")
                return
            template = self.state.template_library.get_template(cmd[1])
            if template and self.state.current_scene:
                entity = Entity(cmd[1])
                entity.tags = set(template.tags)
                self.state.current_scene.add_entity(entity)
                print(f"Created {cmd[1]} with ID: {entity.id[:8]}...")

        elif action == 'list':
            if self.state.current_scene:
                print("Entities:")
                for entity in self.state.current_scene.get_all_entities():
                    selected = "*" if entity.id in self.state.selected_entities else " "
                    pos = entity.transform.position
                    print(f"  {selected} {entity.id[:8]}... - {entity.name} ({pos.x:.0f}, {pos.y:.0f})")

        elif action == 'select':
            if len(cmd) < 2:
                print("Usage: select <entity_id>")
                return
            if self.state.current_scene:
                for entity in self.state.current_scene.get_all_entities():
                    if entity.id.startswith(cmd[1]):
                        self.state.select_entity(entity.id)
                        print(f"Selected: {entity.name}")
                        return
                print("Entity not found")

        elif action == 'move':
            if len(cmd) < 3:
                print("Usage: move <x> <y>")
                return
            if self.state.selected_entities and self.state.current_scene:
                entity = self.state.current_scene.get_entity(self.state.selected_entities[0])
                if entity:
                    entity.transform.position.x = float(cmd[1])
                    entity.transform.position.y = float(cmd[2])
                    print(f"Moved {entity.name} to ({cmd[1]}, {cmd[2]})")

        elif action == 'delete':
            if self.state.selected_entities and self.state.current_scene:
                entity = self.state.current_scene.get_entity(self.state.selected_entities[0])
                if entity:
                    self.state.current_scene.remove_entity(entity)
                    self.state.deselect_all()
                    print(f"Deleted {entity.name}")

        elif action == 'save':
            if len(cmd) < 2:
                print("Usage: save <filename>")
                return
            if self.state.current_scene:
                self.state.current_scene.save(cmd[1])
                print(f"Saved to {cmd[1]}")

        else:
            print(f"Unknown command: {action}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the game editor"""
    print("\nStarting Electroduction Game Editor...")

    if TK_AVAILABLE:
        editor = GameEditor()
        editor.run()
    else:
        print("GUI not available, using console mode")
        editor = ConsoleEditor()
        editor.run()


if __name__ == "__main__":
    main()
