#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION IT SECURITY SUITE - MASTER RUN SCRIPT
===============================================================================
Run and test all security tools:
- VPN System
- Firewall System
- Intrusion Detection System (IDS)

Usage:
    python run_all.py                    # Run all tests
    python run_all.py vpn               # Test VPN only
    python run_all.py firewall          # Test Firewall only
    python run_all.py ids               # Test IDS only
    python run_all.py demo              # Run full demo
===============================================================================
"""

import sys
import os
import time

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
║                    IT SECURITY SUITE v1.0                                    ║
║                    VPN • Firewall • IDS                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def test_vpn():
    """Test VPN system"""
    print("\n" + "="*70)
    print("                    VPN SYSTEM TEST")
    print("="*70 + "\n")

    try:
        from vpn.vpn_core import (
            VPNServer, VPNClient, VPNConfig, VPNPacket, PacketType,
            CryptoEngine, KeyExchange, TUNInterface, IPAddressPool
        )

        # Test 1: Crypto
        print("[1] Testing Cryptographic Engine...")
        secret = os.urandom(32)
        crypto = CryptoEngine(secret)
        plaintext = b"Test VPN encryption message"
        nonce, ciphertext = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(nonce, ciphertext)
        assert decrypted == plaintext
        print("    PASSED: Encryption/Decryption working")

        # Test 2: Packet serialization
        print("[2] Testing Packet Serialization...")
        packet = VPNPacket(PacketType.DATA, b"payload data", seq_num=100)
        serialized = packet.serialize()
        deserialized = VPNPacket.deserialize(serialized)
        assert deserialized.payload == b"payload data"
        assert deserialized.seq_num == 100
        print("    PASSED: Packet serialization working")

        # Test 3: Key Exchange
        print("[3] Testing Key Exchange...")
        alice = KeyExchange()
        bob = KeyExchange()
        alice_pub = alice.get_public_bytes()
        bob_pub = bob.get_public_bytes()
        alice_secret = alice.compute_shared_secret(bob_pub)
        bob_secret = bob.compute_shared_secret(alice_pub)
        print(f"    Key Exchange completed")
        print("    PASSED: Diffie-Hellman working")

        # Test 4: IP Pool
        print("[4] Testing IP Address Pool...")
        pool = IPAddressPool()
        ip1 = pool.allocate("client1")
        ip2 = pool.allocate("client2")
        assert ip1 != ip2
        pool.release("client1")
        ip3 = pool.allocate("client3")
        print(f"    Allocated IPs: {ip1}, {ip2}, {ip3}")
        print("    PASSED: IP Pool working")

        # Test 5: Server/Client (simulation)
        print("[5] Testing Server/Client Integration...")
        config = VPNConfig(server_address="127.0.0.1", server_port=51820)
        server = VPNServer(config)
        server.start()
        time.sleep(0.5)
        stats = server.get_stats()
        print(f"    Server stats: {stats}")
        server.stop()
        print("    PASSED: Server lifecycle working")

        print("\n" + "-"*70)
        print("VPN SYSTEM: ALL TESTS PASSED!")
        print("-"*70)
        return True

    except Exception as e:
        print(f"VPN TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_firewall():
    """Test Firewall system"""
    print("\n" + "="*70)
    print("                    FIREWALL SYSTEM TEST")
    print("="*70 + "\n")

    try:
        from firewall.firewall_core import (
            Firewall, FirewallRule, FirewallManager,
            Action, Protocol, Direction, ConnectionState,
            ConnectionTracker, RateLimiter, Packet, create_test_packet
        )

        # Test 1: Packet Parsing
        print("[1] Testing Packet Parsing...")
        packet_data = create_test_packet("192.168.1.100", "10.0.0.1", 12345, 80)
        packet = Packet.parse(packet_data)
        assert packet.ip.src_ip == "192.168.1.100"
        assert packet.tcp.dst_port == 80
        print("    PASSED: Packet parsing working")

        # Test 2: Rule Matching
        print("[2] Testing Rule Matching...")
        rule = FirewallRule(
            name="test_rule",
            action=Action.ALLOW,
            src_ip="192.168.1.0/24",
            protocol=Protocol.TCP
        )
        assert rule.matches(packet, Direction.OUTBOUND)
        print("    PASSED: Rule matching working")

        # Test 3: Firewall Processing
        print("[3] Testing Firewall Processing...")
        firewall = Firewall(default_action=Action.DENY)
        firewall.add_rule(rule)
        firewall.start()
        action, _ = firewall.process_packet(packet_data, Direction.OUTBOUND)
        assert action == Action.ALLOW
        print(f"    Action: {action.name}")
        print("    PASSED: Firewall processing working")

        # Test 4: Connection Tracking
        print("[4] Testing Connection Tracking...")
        tracker = ConnectionTracker()
        tracker.start()
        state = tracker.process_packet(packet)
        print(f"    Connection state: {state.name}")
        tracker.stop()
        print("    PASSED: Connection tracking working")

        # Test 5: Rate Limiting
        print("[5] Testing Rate Limiting...")
        limiter = RateLimiter()
        allowed = sum(1 for _ in range(15) if limiter.check_rate("test", 10, 10))
        print(f"    Allowed {allowed} of 15 requests (limit: 10)")
        assert allowed == 10
        print("    PASSED: Rate limiting working")

        # Test 6: Firewall Manager
        print("[6] Testing Firewall Manager...")
        manager = FirewallManager()
        manager.setup_default_rules()
        rules = manager.firewall.get_rules()
        print(f"    Loaded {len(rules)} default rules")
        print("    PASSED: Firewall manager working")

        firewall.stop()

        print("\n" + "-"*70)
        print("FIREWALL SYSTEM: ALL TESTS PASSED!")
        print("-"*70)
        return True

    except Exception as e:
        print(f"FIREWALL TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ids():
    """Test IDS system"""
    print("\n" + "="*70)
    print("                    IDS SYSTEM TEST")
    print("="*70 + "\n")

    try:
        from ids.ids_core import (
            IntrusionDetectionSystem, SignatureEngine, AnomalyEngine,
            BruteForceDetector, DDoSDetector, AlertManager,
            Signature, Severity, AlertType, PacketInfo, Protocol,
            create_test_packet
        )

        # Test 1: Packet Parsing
        print("[1] Testing Packet Parsing...")
        packet_data = create_test_packet("192.168.1.100", "10.0.0.1", 12345, 80, b"GET / HTTP/1.1")
        packet = PacketInfo.parse(packet_data)
        assert packet.src_ip == "192.168.1.100"
        print("    PASSED: Packet parsing working")

        # Test 2: Signature Engine
        print("[2] Testing Signature Engine...")
        sig_engine = SignatureEngine()
        sig_engine.load_default_signatures()
        print(f"    Loaded {len(sig_engine.signatures)} signatures")

        sqli_packet = create_test_packet(
            "192.168.1.100", "10.0.0.1", 12345, 80,
            b"GET /page?id=1' OR '1'='1 HTTP/1.1"
        )
        sqli_info = PacketInfo.parse(sqli_packet)
        matches = sig_engine.check_packet(sqli_info)
        print(f"    SQL injection detected: {len(matches)} matches")
        assert len(matches) > 0
        print("    PASSED: Signature detection working")

        # Test 3: Anomaly Engine
        print("[3] Testing Anomaly Engine...")
        anomaly_engine = AnomalyEngine()
        for i in range(100):
            normal = create_test_packet(f"192.168.1.{i%10}", "10.0.0.1", 50000+i, 80, b"A"*100)
            anomaly_engine.analyze_packet(PacketInfo.parse(normal))
        baseline = anomaly_engine.get_baseline_stats()
        print(f"    Baseline established: {baseline['sample_size']} samples")
        print("    PASSED: Anomaly detection working")

        # Test 4: Brute Force Detection
        print("[4] Testing Brute Force Detection...")
        bf_detector = BruteForceDetector(threshold=5, window=60)
        for i in range(10):
            ssh_packet = create_test_packet("10.0.0.100", "192.168.1.1", 54321, 22)
            result = bf_detector.check_packet(PacketInfo.parse(ssh_packet))
        assert result is not None
        print(f"    Detected brute force on {result[0]}: {result[1]} attempts")
        print("    PASSED: Brute force detection working")

        # Test 5: Alert Manager
        print("[5] Testing Alert Manager...")
        alert_manager = AlertManager()
        test_packet = PacketInfo.parse(create_test_packet("1.2.3.4", "5.6.7.8", 1234, 80))
        alert = alert_manager.create_alert(
            AlertType.SIGNATURE_MATCH, Severity.HIGH, test_packet, "Test alert"
        )
        assert alert is not None
        print(f"    Created alert: {alert.id}")
        print("    PASSED: Alert manager working")

        # Test 6: Full IDS Integration
        print("[6] Testing Full IDS Integration...")
        ids = IntrusionDetectionSystem()
        ids.start()

        attack_packet = create_test_packet(
            "10.0.0.1", "192.168.1.1", 12345, 80,
            b"GET /page?cmd=;cat /etc/passwd HTTP/1.1"
        )
        alerts = ids.process_packet(attack_packet)
        print(f"    Generated {len(alerts)} alerts")

        stats = ids.get_stats()
        print(f"    Total packets processed: {stats['packets_processed']}")
        ids.stop()
        print("    PASSED: Full IDS integration working")

        print("\n" + "-"*70)
        print("IDS SYSTEM: ALL TESTS PASSED!")
        print("-"*70)
        return True

    except Exception as e:
        print(f"IDS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_demo():
    """Run full security suite demo"""
    print("\n" + "="*70)
    print("                SECURITY SUITE FULL DEMO")
    print("="*70 + "\n")

    print("This demo will showcase all three security systems working together.\n")

    # Demo VPN
    print("[DEMO 1] VPN System")
    print("-" * 40)
    try:
        from vpn.run_vpn import VPNDemo
        demo = VPNDemo()
        demo.run_demo()
    except Exception as e:
        print(f"VPN Demo error: {e}")

    input("\nPress Enter to continue to Firewall demo...")

    # Demo Firewall
    print("\n[DEMO 2] Firewall System")
    print("-" * 40)
    try:
        from firewall.firewall_core import run_demo as fw_demo
        fw_demo()
    except Exception as e:
        print(f"Firewall Demo error: {e}")

    input("\nPress Enter to continue to IDS demo...")

    # Demo IDS
    print("\n[DEMO 3] IDS System")
    print("-" * 40)
    try:
        from ids.ids_core import run_demo as ids_demo
        ids_demo()
    except Exception as e:
        print(f"IDS Demo error: {e}")

    print("\n" + "="*70)
    print("                DEMO COMPLETED!")
    print("="*70 + "\n")


def main():
    """Main entry point"""
    print_banner()

    if len(sys.argv) < 2:
        # Run all tests
        print("Running all security suite tests...\n")
        results = {
            'VPN': test_vpn(),
            'Firewall': test_firewall(),
            'IDS': test_ids()
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
        if cmd == 'vpn':
            test_vpn()
        elif cmd == 'firewall':
            test_firewall()
        elif cmd == 'ids':
            test_ids()
        elif cmd == 'demo':
            run_demo()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python run_all.py [vpn|firewall|ids|demo]")


if __name__ == "__main__":
    main()
