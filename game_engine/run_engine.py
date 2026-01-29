#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION GAME ENGINE - MASTER RUN SCRIPT
===============================================================================
Run and test all game engine components:
- Core Engine (ECS, Physics, Collision)
- AI Generator (Text-to-Game)
- Visual Editor

Usage:
    python run_engine.py                 # Run all tests
    python run_engine.py core           # Test core engine
    python run_engine.py ai             # Test AI generator
    python run_engine.py editor         # Launch editor
    python run_engine.py demo           # Run full demo
    python run_engine.py text2game "description"  # Generate game from text
===============================================================================
"""

import sys
import os
import time
import json

# Add directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ███████╗██╗     ███████╗ ██████╗████████╗██████╗  ██████╗                ║
║     ██╔════╝██║     ██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗               ║
║     █████╗  ██║     █████╗  ██║        ██║   ██████╔╝██║   ██║               ║
║     ██╔══╝  ██║     ██╔══╝  ██║        ██║   ██╔══██╗██║   ██║               ║
║     ███████╗███████╗███████╗╚██████╗   ██║   ██║  ██║╚██████╔╝               ║
║     ╚══════╝╚══════╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝               ║
║                                                                              ║
║                    GAME ENGINE v1.0                                          ║
║                    2D/3D • AI • Visual Editor                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def test_core_engine():
    """Test core game engine"""
    print("\n" + "="*70)
    print("                    CORE ENGINE TEST")
    print("="*70 + "\n")

    try:
        from core.engine import (
            Vector2, Vector3, Color, Rectangle, Transform,
            Entity, Component, Scene, GameEngine,
            SpriteComponent, RigidBodyComponent, ColliderComponent,
            AnimationComponent, ScriptComponent,
            PhysicsSystem, CollisionSystem, AnimationSystem,
            create_sprite_entity, create_physics_entity, create_player_entity
        )

        # Test 1: Math Primitives
        print("[1] Testing Math Primitives...")
        v1 = Vector2(3, 4)
        assert v1.magnitude() == 5.0
        v2 = Vector3(1, 0, 0)
        v3 = Vector3(0, 1, 0)
        cross = v2.cross(v3)
        assert cross.z == 1.0
        color = Color.from_hex("#FF5500")
        assert color.r == 255
        print("    PASSED: Vector2, Vector3, Color working")

        # Test 2: Entity Component System
        print("[2] Testing Entity Component System...")
        entity = Entity("TestEntity")
        sprite = SpriteComponent("texture.png")
        entity.add_component(sprite)
        assert entity.has_component(SpriteComponent)
        assert entity.get_component(SpriteComponent) == sprite
        entity.add_tag("player")
        assert entity.has_tag("player")
        print("    PASSED: ECS working")

        # Test 3: Scene Management
        print("[3] Testing Scene Management...")
        scene = Scene("TestScene")
        scene.add_entity(entity)
        assert scene.get_entity(entity.id) == entity
        assert scene.find_entity("TestEntity") == entity
        found = scene.find_entities_with_tag("player")
        assert len(found) == 1
        print("    PASSED: Scene management working")

        # Test 4: Physics System
        print("[4] Testing Physics System...")
        physics_entity = create_physics_entity("PhysicsTest", 100, 0)
        rb = physics_entity.get_component(RigidBodyComponent)
        rb.velocity = Vector2(100, 0)
        initial_x = physics_entity.transform.position.x

        physics_system = PhysicsSystem()
        physics_system.update([physics_entity], 0.1)

        assert physics_entity.transform.position.x > initial_x
        print(f"    Entity moved from {initial_x} to {physics_entity.transform.position.x}")
        print("    PASSED: Physics working")

        # Test 5: Collision System
        print("[5] Testing Collision System...")
        e1 = create_physics_entity("E1", 0, 0, 32, 32)
        e2 = create_physics_entity("E2", 10, 10, 32, 32)  # Overlapping

        collision_detected = [False]

        def on_collision(a, b):
            collision_detected[0] = True

        collision_system = CollisionSystem()
        collision_system.register_callback("test", on_collision)
        e1.add_tag("test")

        collision_system.update([e1, e2], 0.1)
        assert collision_detected[0]
        print("    PASSED: Collision detection working")

        # Test 6: Animation System
        print("[6] Testing Animation System...")
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
        anim_system.update([anim_entity], 0.2)
        print("    PASSED: Animation system working")

        # Test 7: Full Engine Integration
        print("[7] Testing Full Engine Integration...")
        engine = GameEngine()
        main_scene = engine.scene_manager.create_scene("Main")
        engine.scene_manager.load_scene("Main")

        player = create_player_entity("Player", 100, 100)
        main_scene.add_entity(player)

        engine.start()
        engine.update(1/60)

        stats = engine.get_stats()
        print(f"    Engine stats: {stats['entity_count']} entities, {stats['fps']:.0f} FPS")
        assert stats['entity_count'] >= 1
        engine.stop()
        print("    PASSED: Engine integration working")

        # Test 8: Factory Functions
        print("[8] Testing Factory Functions...")
        sprite_entity = create_sprite_entity("Sprite", 50, 50, "test.png", 64, 64)
        assert sprite_entity.has_component(SpriteComponent)

        player_entity = create_player_entity("Hero", 200, 200)
        assert player_entity.has_component(RigidBodyComponent)
        assert player_entity.has_component(ColliderComponent)
        assert player_entity.has_tag("player")
        print("    PASSED: Factory functions working")

        print("\n" + "-"*70)
        print("CORE ENGINE: ALL TESTS PASSED!")
        print("-"*70)
        return True

    except Exception as e:
        print(f"CORE ENGINE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_generator():
    """Test AI generator system"""
    print("\n" + "="*70)
    print("                    AI GENERATOR TEST")
    print("="*70 + "\n")

    try:
        from ai.ai_generator import (
            TextParser, ProceduralGenerator, BehaviorGenerator,
            SpriteGenerator, StoryGenerator, TextToGameGenerator,
            GameGenre
        )

        # Test 1: Text Parser
        print("[1] Testing Text Parser...")
        parser = TextParser()
        result = parser.parse("A platformer game with jumping and shooting in a fantasy castle")
        assert result.genre == GameGenre.PLATFORMER
        assert 'jump' in result.player_abilities
        print(f"    Detected genre: {result.genre.name}")
        print(f"    Detected theme: {result.theme}")
        print(f"    Detected abilities: {result.player_abilities}")
        print("    PASSED: Text parser working")

        # Test 2: Level Generator
        print("[2] Testing Level Generator...")
        gen = ProceduralGenerator(seed=42)

        platformer_level = gen.generate_platformer_level(30, 10, "medium")
        print(f"    Generated platformer level: {len(platformer_level[0])}x{len(platformer_level)}")

        topdown_level = gen.generate_top_down_level(20, 15)
        print(f"    Generated top-down level: {len(topdown_level[0])}x{len(topdown_level)}")

        enemies = gen.generate_enemy_positions(platformer_level, 5)
        print(f"    Generated {len(enemies)} enemy positions")

        collectibles = gen.generate_collectible_positions(platformer_level, 10)
        print(f"    Generated {len(collectibles)} collectible positions")
        print("    PASSED: Level generation working")

        # Test 3: Behavior Generator
        print("[3] Testing Behavior Generator...")
        behavior_gen = BehaviorGenerator()
        for enemy_type in ['walker', 'flyer', 'shooter', 'chaser', 'boss']:
            behavior = behavior_gen.get_behavior(enemy_type)
            print(f"    {enemy_type}: {behavior.name} ({len(behavior.children)} children)")
        print("    PASSED: Behavior generation working")

        # Test 4: Sprite Generator
        print("[4] Testing Sprite Generator...")
        sprite_gen = SpriteGenerator(seed=42)

        character = sprite_gen.generate_character_sprite(8, 8)
        print("    Generated character sprite (8x8):")
        print(sprite_gen.sprite_to_ascii(character))

        tile = sprite_gen.generate_tile_sprite(8, 8, "ground")
        print("    Generated ground tile (8x8)")
        print("    PASSED: Sprite generation working")

        # Test 5: Story Generator
        print("[5] Testing Story Generator...")
        story_gen = StoryGenerator()
        story = story_gen.generate_story("fantasy")
        print(f"    Story: {story[:80]}...")
        dialogue = story_gen.generate_dialogue("quest_give")
        print(f"    Dialogue: {dialogue}")
        print("    PASSED: Story generation working")

        # Test 6: Full Text-to-Game
        print("[6] Testing Text-to-Game Generation...")
        generator = TextToGameGenerator()

        game_description = """
        Create a retro pixel art platformer game called "Crystal Quest".
        The player can jump, double jump, and shoot projectiles.
        There should be walking enemies and flying enemies.
        Collect gems and coins. Fantasy castle theme. Medium difficulty.
        """

        game_data = generator.generate_game(game_description)

        print(f"    Game title: {game_data['description'].title}")
        print(f"    Genre: {game_data['description'].genre.name}")
        print(f"    Level size: {len(game_data['level'][0])}x{len(game_data['level'])}")
        print(f"    Enemies: {len(game_data['enemies'])}")
        print(f"    Collectibles: {len(game_data['collectibles'])}")
        print(f"    Code generated: {len(game_data['code'])} characters")
        print("    PASSED: Text-to-game working")

        print("\n" + "-"*70)
        print("AI GENERATOR: ALL TESTS PASSED!")
        print("-"*70)
        return True

    except Exception as e:
        print(f"AI GENERATOR TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_editor():
    """Test visual editor components"""
    print("\n" + "="*70)
    print("                    EDITOR TEST")
    print("="*70 + "\n")

    try:
        from ui.editor import (
            EditorState, EditorTool, UndoRedoManager, EntityTemplate,
            TemplateLibrary, ScriptNode, VisualScriptGraph, ScriptNodeType
        )

        # Test 1: Undo/Redo Manager
        print("[1] Testing Undo/Redo Manager...")
        from ui.editor import EditorAction
        undo_manager = UndoRedoManager()
        undo_manager.record_action(EditorAction(action_type="create", entity_id="123"))
        undo_manager.record_action(EditorAction(action_type="move", entity_id="123"))
        assert undo_manager.can_undo()
        action = undo_manager.undo()
        assert action.action_type == "move"
        assert undo_manager.can_redo()
        print("    PASSED: Undo/Redo working")

        # Test 2: Template Library
        print("[2] Testing Template Library...")
        library = TemplateLibrary()
        templates = library.get_all_templates()
        print(f"    Loaded templates: {templates}")
        assert 'Player' in templates
        assert 'Enemy' in templates
        player_template = library.get_template('Player')
        assert player_template is not None
        print("    PASSED: Template library working")

        # Test 3: Entity Template
        print("[3] Testing Entity Template...")
        template = EntityTemplate("CustomEntity")
        template.add_component("SpriteComponent", {"color": [255, 0, 0]})
        template.tags = ["custom", "test"]
        data = template.to_dict()
        restored = EntityTemplate.from_dict(data)
        assert restored.name == "CustomEntity"
        assert "custom" in restored.tags
        print("    PASSED: Entity template working")

        # Test 4: Visual Script Graph
        print("[4] Testing Visual Script Graph...")
        graph = VisualScriptGraph("TestScript")

        on_start = ScriptNode(
            id="node1",
            node_type=ScriptNodeType.EVENT,
            name="OnStart",
            position=(100, 100),
            outputs={"exec": "flow"}
        )
        graph.add_node(on_start)

        move_action = ScriptNode(
            id="node2",
            node_type=ScriptNodeType.ACTION,
            name="Move",
            position=(300, 100),
            inputs={"exec": "flow", "direction": "vector2"}
        )
        graph.add_node(move_action)

        graph.connect("node1", "exec", "node2", "exec")

        assert len(graph.nodes) == 2
        assert "node2" in on_start.connections.get("exec", (None, None))
        print("    PASSED: Visual scripting working")

        # Test 5: Editor State
        print("[5] Testing Editor State...")
        state = EditorState()
        state.current_tool = EditorTool.MOVE
        assert state.current_tool == EditorTool.MOVE
        state.select_entity("entity-123")
        assert "entity-123" in state.selected_entities
        state.select_entity("entity-456", add_to_selection=True)
        assert len(state.selected_entities) == 2
        state.deselect_all()
        assert len(state.selected_entities) == 0
        print("    PASSED: Editor state working")

        print("\n" + "-"*70)
        print("EDITOR: ALL TESTS PASSED!")
        print("-"*70)
        return True

    except Exception as e:
        print(f"EDITOR TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_text_to_game(description: str):
    """Generate game from text description"""
    print("\n" + "="*70)
    print("                TEXT-TO-GAME GENERATION")
    print("="*70 + "\n")

    try:
        from ai.ai_generator import TextToGameGenerator

        generator = TextToGameGenerator()
        print(f"Input: {description}\n")
        print("Generating game...")

        game_data = generator.generate_game(description)

        print(generator.preview_game(game_data))

        # Save generated code
        output_file = "generated_game.py"
        with open(output_file, 'w') as f:
            f.write(game_data['code'])
        print(f"\nGenerated code saved to: {output_file}")

        # Save level data
        level_file = "generated_level.json"
        with open(level_file, 'w') as f:
            json.dump({
                'level': game_data['level'],
                'enemies': game_data['enemies'],
                'collectibles': game_data['collectibles'],
                'story': game_data['story']
            }, f, indent=2)
        print(f"Level data saved to: {level_file}")

        return True

    except Exception as e:
        print(f"TEXT-TO-GAME FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_demo():
    """Run full game engine demo"""
    print("\n" + "="*70)
    print("                GAME ENGINE FULL DEMO")
    print("="*70 + "\n")

    # Demo 1: Core Engine
    print("[DEMO 1] Core Engine Capabilities")
    print("-" * 40)
    try:
        from core.engine import (
            GameEngine, Scene, create_player_entity, create_physics_entity,
            PhysicsSystem, Vector2
        )

        engine = GameEngine()
        scene = engine.scene_manager.create_scene("Demo")
        engine.scene_manager.load_scene("Demo")

        # Create entities
        player = create_player_entity("Hero", 100, 100)
        scene.add_entity(player)

        for i in range(5):
            enemy = create_physics_entity(f"Enemy_{i}", 200 + i*50, 100 + i*30)
            enemy.add_tag("enemy")
            scene.add_entity(enemy)

        engine.start()

        print("    Simulating 60 frames...")
        for frame in range(60):
            engine.update(1/60)

        stats = engine.get_stats()
        print(f"    Final stats: {stats['entity_count']} entities, {stats['frame_count']} frames")
        engine.stop()
        print("    Core engine demo complete!\n")

    except Exception as e:
        print(f"    Demo error: {e}\n")

    # Demo 2: AI Generator
    print("[DEMO 2] AI Text-to-Game")
    print("-" * 40)
    try:
        from ai.ai_generator import TextToGameGenerator

        generator = TextToGameGenerator()

        descriptions = [
            "A simple platformer with jumping",
            "Top-down zombie shooter game",
            "Fantasy RPG adventure with magic"
        ]

        for desc in descriptions:
            print(f"    Input: '{desc}'")
            game = generator.generate_game(desc)
            print(f"    Output: {game['description'].title} ({game['description'].genre.name})")
            print()

        print("    AI generator demo complete!\n")

    except Exception as e:
        print(f"    Demo error: {e}\n")

    # Demo 3: Level Generation
    print("[DEMO 3] Procedural Level Generation")
    print("-" * 40)
    try:
        from ai.ai_generator import ProceduralGenerator

        gen = ProceduralGenerator()

        for difficulty in ['easy', 'medium', 'hard']:
            level = gen.generate_platformer_level(30, 8, difficulty)
            print(f"    {difficulty.upper()} level ({len(level[0])}x{len(level)}):")
            for row in level[:5]:
                line = ''.join(['#' if t == 1 else '=' if t == 2 else '^' if t == 3 else ' ' for t in row[:30]])
                print(f"      {line}")
            print()

        print("    Level generation demo complete!\n")

    except Exception as e:
        print(f"    Demo error: {e}\n")

    print("="*70)
    print("                DEMO COMPLETED!")
    print("="*70 + "\n")


def launch_editor():
    """Launch the visual editor"""
    print("\n" + "="*70)
    print("                LAUNCHING VISUAL EDITOR")
    print("="*70 + "\n")

    try:
        from ui.editor import main as editor_main
        editor_main()
    except Exception as e:
        print(f"Editor launch failed: {e}")
        print("Falling back to console editor...")
        from ui.editor import ConsoleEditor
        editor = ConsoleEditor()
        editor.run()


def main():
    """Main entry point"""
    print_banner()

    if len(sys.argv) < 2:
        # Run all tests
        print("Running all game engine tests...\n")
        results = {
            'Core Engine': test_core_engine(),
            'AI Generator': test_ai_generator(),
            'Editor': test_editor()
        }

        print("\n" + "="*70)
        print("                    FINAL RESULTS")
        print("="*70)
        for name, passed in results.items():
            status = "PASSED" if passed else "FAILED"
            print(f"  {name:20s}: {status}")
        print("="*70)

        all_passed = all(results.values())
        print(f"\nOverall: {'ALL TESTS PASSED!' if all_passed else 'SOME TESTS FAILED'}\n")

    else:
        cmd = sys.argv[1].lower()
        if cmd == 'core':
            test_core_engine()
        elif cmd == 'ai':
            test_ai_generator()
        elif cmd == 'editor':
            launch_editor()
        elif cmd == 'demo':
            run_demo()
        elif cmd == 'text2game':
            if len(sys.argv) > 2:
                description = ' '.join(sys.argv[2:])
                run_text_to_game(description)
            else:
                print("Usage: python run_engine.py text2game \"Your game description here\"")
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python run_engine.py [core|ai|editor|demo|text2game]")


if __name__ == "__main__":
    main()
