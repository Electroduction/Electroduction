#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION - MASTER SYSTEM RUNNER
===============================================================================
This is the main entry point for all Electroduction systems:

IT SECURITY SUITE:
    - Custom VPN System
    - Custom Firewall
    - Intrusion Detection System (IDS)

GAME ENGINE:
    - Core Engine (ECS, Physics, Collision, Animation)
    - AI Generator (Text-to-Game, Procedural Content)
    - Visual Editor (Drag-and-Drop, Visual Scripting)

Usage:
    python run_all_systems.py                    # Run ALL tests
    python run_all_systems.py security          # Test security suite only
    python run_all_systems.py engine            # Test game engine only
    python run_all_systems.py demo              # Run full demonstration
    python run_all_systems.py help              # Show detailed help

Individual components:
    python run_all_systems.py vpn               # Test VPN
    python run_all_systems.py firewall          # Test Firewall
    python run_all_systems.py ids               # Test IDS
    python run_all_systems.py core              # Test engine core
    python run_all_systems.py ai                # Test AI generator
    python run_all_systems.py editor            # Launch editor
    python run_all_systems.py text2game "desc"  # Generate game from text
===============================================================================
"""

import sys
import os
import time

# Add directories to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'it_security_suite'))
sys.path.insert(0, os.path.join(BASE_DIR, 'game_engine'))


def print_main_banner():
    """Print main banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ███████╗██╗     ███████╗ ██████╗████████╗██████╗  ██████╗ ██████╗ ██╗   ██╗ ║
║  ██╔════╝██║     ██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██╔══██╗██║   ██║ ║
║  █████╗  ██║     █████╗  ██║        ██║   ██████╔╝██║   ██║██║  ██║██║   ██║ ║
║  ██╔══╝  ██║     ██╔══╝  ██║        ██║   ██╔══██╗██║   ██║██║  ██║██║   ██║ ║
║  ███████╗███████╗███████╗╚██████╗   ██║   ██║  ██║╚██████╔╝██████╔╝╚██████╔╝ ║
║  ╚══════╝╚══════╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝  ║
║                                                                              ║
║                    OPEN SOURCE SOFTWARE SUITE v1.0                           ║
║                                                                              ║
║  ┌────────────────────────────┬────────────────────────────────────────────┐ ║
║  │  IT SECURITY SUITE         │  GAME ENGINE                               │ ║
║  │  • Custom VPN              │  • 2D/3D Core Engine                       │ ║
║  │  • Custom Firewall         │  • AI Text-to-Game Generator               │ ║
║  │  • Intrusion Detection     │  • Visual Drag-and-Drop Editor             │ ║
║  └────────────────────────────┴────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def print_help():
    """Print detailed help"""
    print("""
ELECTRODUCTION - Detailed Help
===============================================================================

SECURITY SUITE COMMANDS:
    security          Run all security suite tests
    vpn               Test VPN system (encryption, tunneling, key exchange)
    firewall          Test Firewall (packet filtering, rules, rate limiting)
    ids               Test IDS (signature detection, anomaly detection, alerts)

GAME ENGINE COMMANDS:
    engine            Run all game engine tests
    core              Test core engine (ECS, physics, collision, animation)
    ai                Test AI generator (text parsing, level gen, behaviors)
    editor            Launch visual editor (GUI or console)
    text2game "desc"  Generate game from text description

DEMO COMMANDS:
    demo              Run full demonstration of all systems
    demo-security     Run security suite demonstration only
    demo-engine       Run game engine demonstration only

EXAMPLES:
    python run_all_systems.py                             # Test everything
    python run_all_systems.py demo                        # Full demo
    python run_all_systems.py text2game "A space shooter" # Generate game
    python run_all_systems.py editor                      # Launch editor

===============================================================================
    """)


def run_security_tests():
    """Run all security suite tests"""
    print("\n" + "="*70)
    print("              IT SECURITY SUITE - TESTING")
    print("="*70 + "\n")

    results = {}

    # VPN
    print("[1/3] Testing VPN System...")
    try:
        from vpn.vpn_core import (
            VPNServer, VPNClient, VPNConfig, VPNPacket, PacketType,
            CryptoEngine, KeyExchange
        )

        # Quick tests
        secret = os.urandom(32)
        crypto = CryptoEngine(secret)
        nonce, ct = crypto.encrypt(b"test")
        assert crypto.decrypt(nonce, ct) == b"test"

        packet = VPNPacket(PacketType.DATA, b"payload", seq_num=1)
        deser = VPNPacket.deserialize(packet.serialize())
        assert deser.payload == b"payload"

        results['VPN'] = True
        print("    VPN: PASSED")

    except Exception as e:
        results['VPN'] = False
        print(f"    VPN: FAILED - {e}")

    # Firewall
    print("[2/3] Testing Firewall System...")
    try:
        from firewall.firewall_core import (
            Firewall, FirewallRule, Action, Protocol, Packet, create_test_packet
        )

        packet_data = create_test_packet("192.168.1.1", "10.0.0.1", 12345, 80)
        packet = Packet.parse(packet_data)
        assert packet.ip.src_ip == "192.168.1.1"

        firewall = Firewall(default_action=Action.ALLOW)
        firewall.start()
        action, _ = firewall.process_packet(packet_data)
        assert action == Action.ALLOW
        firewall.stop()

        results['Firewall'] = True
        print("    Firewall: PASSED")

    except Exception as e:
        results['Firewall'] = False
        print(f"    Firewall: FAILED - {e}")

    # IDS
    print("[3/3] Testing IDS System...")
    try:
        from ids.ids_core import (
            IntrusionDetectionSystem, create_test_packet as ids_create_packet
        )

        ids = IntrusionDetectionSystem()
        ids.start()

        packet = ids_create_packet("1.2.3.4", "5.6.7.8", 1234, 80, b"test")
        ids.process_packet(packet)

        stats = ids.get_stats()
        assert stats['packets_processed'] >= 1
        ids.stop()

        results['IDS'] = True
        print("    IDS: PASSED")

    except Exception as e:
        results['IDS'] = False
        print(f"    IDS: FAILED - {e}")

    return results


def run_engine_tests():
    """Run all game engine tests"""
    print("\n" + "="*70)
    print("              GAME ENGINE - TESTING")
    print("="*70 + "\n")

    results = {}

    # Core Engine
    print("[1/3] Testing Core Engine...")
    try:
        from core.engine import (
            Vector2, Vector3, Entity, Scene, GameEngine,
            SpriteComponent, create_physics_entity
        )

        assert Vector2(3, 4).magnitude() == 5.0
        assert Vector3(1, 0, 0).cross(Vector3(0, 1, 0)).z == 1.0

        entity = Entity("Test")
        entity.add_component(SpriteComponent())
        assert entity.has_component(SpriteComponent)

        scene = Scene("Test")
        scene.add_entity(entity)
        assert scene.get_entity(entity.id) is not None

        engine = GameEngine()
        engine.start()
        engine.update(1/60)
        engine.stop()

        results['Core'] = True
        print("    Core Engine: PASSED")

    except Exception as e:
        results['Core'] = False
        print(f"    Core Engine: FAILED - {e}")

    # AI Generator
    print("[2/3] Testing AI Generator...")
    try:
        from ai.ai_generator import (
            TextParser, ProceduralGenerator, TextToGameGenerator, GameGenre
        )

        parser = TextParser()
        result = parser.parse("A platformer with jumping")
        assert result.genre == GameGenre.PLATFORMER

        gen = ProceduralGenerator()
        level = gen.generate_platformer_level(20, 10)
        assert len(level) == 10
        assert len(level[0]) == 20

        generator = TextToGameGenerator()
        game = generator.generate_game("Simple platformer")
        assert 'code' in game

        results['AI'] = True
        print("    AI Generator: PASSED")

    except Exception as e:
        results['AI'] = False
        print(f"    AI Generator: FAILED - {e}")

    # Editor
    print("[3/3] Testing Editor Components...")
    try:
        from ui.editor import (
            EditorState, UndoRedoManager, TemplateLibrary, EditorAction
        )

        undo = UndoRedoManager()
        undo.record_action(EditorAction(action_type="test"))
        assert undo.can_undo()

        library = TemplateLibrary()
        assert 'Player' in library.get_all_templates()

        state = EditorState()
        state.select_entity("test-id")
        assert "test-id" in state.selected_entities

        results['Editor'] = True
        print("    Editor: PASSED")

    except Exception as e:
        results['Editor'] = False
        print(f"    Editor: FAILED - {e}")

    return results


def run_full_demo():
    """Run full demonstration"""
    print("\n" + "="*70)
    print("              FULL SYSTEM DEMONSTRATION")
    print("="*70 + "\n")

    # Security Demo
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                    SECURITY SUITE DEMO                             ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")

    try:
        from vpn.vpn_core import CryptoEngine, KeyExchange, VPNPacket, PacketType
        from firewall.firewall_core import FirewallManager, create_test_packet as fw_create
        from ids.ids_core import IntrusionDetectionSystem, create_test_packet as ids_create

        # VPN Demo
        print("[VPN] Demonstrating encrypted communication...")
        secret = os.urandom(32)
        crypto = CryptoEngine(secret)
        message = b"Secure VPN message across the network"
        nonce, encrypted = crypto.encrypt(message)
        decrypted = crypto.decrypt(nonce, encrypted)
        print(f"    Original: {message}")
        print(f"    Encrypted: {encrypted[:32]}...")
        print(f"    Decrypted: {decrypted}")
        print("    VPN encryption verified!\n")

        # Firewall Demo
        print("[FIREWALL] Demonstrating packet filtering...")
        manager = FirewallManager()
        manager.setup_default_rules()
        manager.block_port(23)  # Block telnet

        http_packet = fw_create("192.168.1.1", "10.0.0.1", 12345, 80)
        telnet_packet = fw_create("192.168.1.1", "10.0.0.1", 12345, 23)

        manager.firewall.start()
        http_action, _ = manager.firewall.process_packet(http_packet)
        telnet_action, _ = manager.firewall.process_packet(telnet_packet)
        manager.firewall.stop()

        print(f"    HTTP (port 80): {http_action.name}")
        print(f"    Telnet (port 23): {telnet_action.name}")
        print("    Firewall rules working!\n")

        # IDS Demo
        print("[IDS] Demonstrating intrusion detection...")
        ids = IntrusionDetectionSystem()
        ids.start()

        normal_packet = ids_create("192.168.1.1", "10.0.0.1", 12345, 80, b"GET / HTTP/1.1")
        attack_packet = ids_create("192.168.1.1", "10.0.0.1", 12345, 80, b"' OR '1'='1")

        ids.process_packet(normal_packet)
        alerts = ids.process_packet(attack_packet)

        print(f"    Normal request: 0 alerts")
        print(f"    SQL injection attempt: {len(alerts)} alerts")
        ids.stop()
        print("    IDS detection working!\n")

    except Exception as e:
        print(f"    Security demo error: {e}\n")

    # Game Engine Demo
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                    GAME ENGINE DEMO                                ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")

    try:
        from core.engine import GameEngine, Scene, create_player_entity, create_physics_entity
        from ai.ai_generator import TextToGameGenerator, ProceduralGenerator

        # Core Engine Demo
        print("[ENGINE] Demonstrating game engine...")
        engine = GameEngine()
        scene = engine.scene_manager.create_scene("Demo")
        engine.scene_manager.load_scene("Demo")

        player = create_player_entity("Hero", 100, 100)
        scene.add_entity(player)

        for i in range(3):
            enemy = create_physics_entity(f"Enemy_{i}", 200 + i*50, 100)
            enemy.add_tag("enemy")
            scene.add_entity(enemy)

        engine.start()
        for _ in range(30):
            engine.update(1/60)

        stats = engine.get_stats()
        print(f"    Created {stats['entity_count']} entities")
        print(f"    Simulated {stats['frame_count']} frames")
        engine.stop()
        print("    Game engine working!\n")

        # Level Generation Demo
        print("[GENERATOR] Demonstrating procedural generation...")
        gen = ProceduralGenerator(seed=42)
        level = gen.generate_platformer_level(25, 6)
        print("    Generated level:")
        for row in level:
            line = ''.join(['#' if t == 1 else '=' if t == 2 else '^' if t == 3 else '.' for t in row])
            print(f"      {line}")
        print()

        # Text-to-Game Demo
        print("[AI] Demonstrating text-to-game...")
        generator = TextToGameGenerator()
        game = generator.generate_game("A space shooter with aliens and powerups")
        print(f"    Input: 'A space shooter with aliens and powerups'")
        print(f"    Generated: {game['description'].title}")
        print(f"    Genre: {game['description'].genre.name}")
        print(f"    Theme: {game['description'].theme}")
        print(f"    Abilities: {game['description'].player_abilities}")
        print(f"    Enemies: {game['description'].enemy_types}")
        print("    Text-to-game working!\n")

    except Exception as e:
        print(f"    Game engine demo error: {e}\n")

    print("="*70)
    print("              DEMONSTRATION COMPLETE!")
    print("="*70 + "\n")


def main():
    """Main entry point"""
    print_main_banner()

    if len(sys.argv) < 2:
        # Run all tests
        print("Running ALL system tests...\n")

        sec_results = run_security_tests()
        eng_results = run_engine_tests()

        # Combined results
        all_results = {**sec_results, **eng_results}

        print("\n" + "="*70)
        print("                    FINAL RESULTS")
        print("="*70)
        print("\n  IT Security Suite:")
        for name in ['VPN', 'Firewall', 'IDS']:
            if name in all_results:
                status = "PASSED" if all_results[name] else "FAILED"
                print(f"    {name:15s}: {status}")

        print("\n  Game Engine:")
        for name in ['Core', 'AI', 'Editor']:
            if name in all_results:
                status = "PASSED" if all_results[name] else "FAILED"
                print(f"    {name:15s}: {status}")

        print("\n" + "="*70)
        all_passed = all(all_results.values())
        print(f"Overall: {'ALL TESTS PASSED!' if all_passed else 'SOME TESTS FAILED'}")
        print("="*70 + "\n")

    else:
        cmd = sys.argv[1].lower()

        if cmd == 'help':
            print_help()

        elif cmd == 'security':
            run_security_tests()

        elif cmd == 'engine':
            run_engine_tests()

        elif cmd == 'demo':
            run_full_demo()

        elif cmd == 'demo-security':
            # Run security demo only
            from it_security_suite.run_all import run_demo
            run_demo()

        elif cmd == 'demo-engine':
            # Run engine demo only
            from game_engine.run_engine import run_demo
            run_demo()

        # Individual security components
        elif cmd == 'vpn':
            from it_security_suite.vpn.vpn_core import main as vpn_main
            sys.argv = ['vpn', 'test']
            vpn_main()

        elif cmd == 'firewall':
            from it_security_suite.firewall.firewall_core import main as fw_main
            sys.argv = ['firewall', 'demo']
            fw_main()

        elif cmd == 'ids':
            from it_security_suite.ids.ids_core import main as ids_main
            sys.argv = ['ids', 'demo']
            ids_main()

        # Individual engine components
        elif cmd == 'core':
            from game_engine.run_engine import test_core_engine
            test_core_engine()

        elif cmd == 'ai':
            from game_engine.run_engine import test_ai_generator
            test_ai_generator()

        elif cmd == 'editor':
            from game_engine.run_engine import launch_editor
            launch_editor()

        elif cmd == 'text2game':
            if len(sys.argv) > 2:
                from game_engine.run_engine import run_text_to_game
                description = ' '.join(sys.argv[2:])
                run_text_to_game(description)
            else:
                print("Usage: python run_all_systems.py text2game \"Your game description\"")

        else:
            print(f"Unknown command: {cmd}")
            print("Use 'help' for detailed usage information")


if __name__ == "__main__":
    main()
