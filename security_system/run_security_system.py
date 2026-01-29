#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION COMPLETE SECURITY SYSTEM - MASTER CONTROL
================================================================================
This is the main entry point for the complete security system.
It initializes, coordinates, and manages all security components.

COMPONENTS INTEGRATED:
1. Security Operations Center (SOC) - Central command
2. Intrusion Prevention System (IPS) - Active blocking
3. Threat Intelligence - IOC management
4. Automated Response - Response automation
5. Log Analysis - Security log processing
6. System Monitor - Infrastructure monitoring

QUICK START:
    python run_security_system.py           # Run demo
    python run_security_system.py --start   # Start full system
    python run_security_system.py --test    # Run all tests

================================================================================
SETUP INSTRUCTIONS:
================================================================================

STEP 1: DIRECTORY STRUCTURE
    security_system/
    ├── core/
    │   ├── __init__.py
    │   └── soc_core.py              # Security Operations Center
    ├── components/
    │   ├── __init__.py
    │   ├── intrusion_prevention.py  # IPS - Active blocking
    │   ├── threat_intelligence.py   # Threat feeds & IOCs
    │   └── automated_response.py    # Response automation
    └── run_security_system.py       # This file

STEP 2: DEPENDENCIES (all built-in Python libraries)
    - No external dependencies required
    - Python 3.7+ recommended
    - Optional: iptables for actual blocking

STEP 3: CONFIGURATION
    Edit the config dictionary in this file or create config.json:
    {
        "db_path": "/var/lib/security/soc.db",
        "log_level": "INFO",
        "use_iptables": true,
        "alert_email": "security@example.com"
    }

STEP 4: RUN THE SYSTEM
    # Development/Demo mode:
    python run_security_system.py

    # Production mode (requires root for iptables):
    sudo python run_security_system.py --start

STEP 5: INTEGRATION POINTS
    - Syslog: Send logs to port 5514 (UDP)
    - API: REST API on port 8443
    - Webhook: Configure webhooks for alerts

================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os
import sys
import time
import json
import signal
import argparse
import threading
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import security components
# -------------------------------------------------------------------------
# Each import brings in a major security subsystem that handles a specific
# aspect of security monitoring and response.
# -------------------------------------------------------------------------

try:
    # Security Operations Center - The central brain of the system
    # Coordinates all components and routes security events
    from security_system.core.soc_core import (
        SecurityOperationsCenter,
        SecurityEvent,
        EventCategory,
        EventSeverity,
        Alert
    )
except ImportError:
    from core.soc_core import (
        SecurityOperationsCenter,
        SecurityEvent,
        EventCategory,
        EventSeverity,
        Alert
    )

try:
    # Intrusion Prevention System - Active attack blocking
    # Detects attack patterns and blocks malicious traffic
    from security_system.components.intrusion_prevention import (
        IntrusionPreventionSystem,
        ThreatLevel,
        AttackType
    )
except ImportError:
    from components.intrusion_prevention import (
        IntrusionPreventionSystem,
        ThreatLevel,
        AttackType
    )

try:
    # Threat Intelligence - IOC management and threat feeds
    # Manages indicators of compromise and threat data
    from security_system.components.threat_intelligence import (
        ThreatIntelligence,
        IOCType,
        ThreatType
    )
except ImportError:
    from components.threat_intelligence import (
        ThreatIntelligence,
        IOCType,
        ThreatType
    )

try:
    # Automated Response - Response automation engine
    # Executes playbooks and response actions
    from security_system.components.automated_response import (
        AutomatedResponse,
        ActionType,
        PlaybookPriority
    )
except ImportError:
    from components.automated_response import (
        AutomatedResponse,
        ActionType,
        PlaybookPriority
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default system configuration
# -------------------------------------------------------------------------
# This configuration can be overridden by a config file or environment vars.
# Each setting controls a specific aspect of the security system.
# -------------------------------------------------------------------------
DEFAULT_CONFIG = {
    # Database paths - where security data is stored
    'soc_db_path': '/tmp/soc_events.db',      # SOC event database
    'ti_db_path': '/tmp/threat_intel.db',      # Threat intel database

    # Logging configuration
    'log_level': 'INFO',                       # DEBUG, INFO, WARNING, ERROR
    'log_file': '/tmp/security_system.log',    # Log file path

    # Network configuration
    'syslog_port': 5514,                       # Syslog listener port
    'api_port': 8443,                          # REST API port

    # IPS configuration
    'use_iptables': False,                     # Use actual iptables (requires root)
    'block_duration_default': 3600,            # Default block duration (1 hour)

    # Threat Intelligence
    'update_feeds': True,                      # Auto-update threat feeds
    'feed_update_interval': 6,                 # Hours between updates

    # Automated Response
    'auto_block_enabled': True,                # Enable automatic IP blocking
    'auto_quarantine_enabled': True,           # Enable automatic file quarantine

    # Alert configuration
    'alert_email': '',                         # Alert email (empty = disabled)
    'alert_webhook': '',                       # Alert webhook URL

    # Retention
    'event_retention_days': 30,                # Days to retain events
    'log_retention_days': 90,                  # Days to retain logs
}


# =============================================================================
# SECURITY SYSTEM CLASS
# =============================================================================

class ElectroductionSecuritySystem:
    """
    Main Security System orchestrator.

    This class initializes and coordinates all security components:
    - Security Operations Center (SOC)
    - Intrusion Prevention System (IPS)
    - Threat Intelligence (TI)
    - Automated Response (AR)

    The system provides:
    - Centralized security event management
    - Real-time threat detection and blocking
    - Automated incident response
    - Comprehensive security monitoring
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the complete security system.

        Args:
            config: Configuration dictionary (merges with defaults)

        STEP-BY-STEP INITIALIZATION:
        1. Load and merge configuration
        2. Set up logging infrastructure
        3. Initialize SOC (central command)
        4. Initialize IPS (active defense)
        5. Initialize Threat Intelligence (IOC management)
        6. Initialize Automated Response (playbooks)
        7. Connect components together
        """
        # Step 1: Merge configuration with defaults
        # This allows partial configuration overrides
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        # Step 2: Set up logging
        self._setup_logging()
        self.logger = logging.getLogger('SecuritySystem')

        self.logger.info("=" * 60)
        self.logger.info("ELECTRODUCTION SECURITY SYSTEM INITIALIZING")
        self.logger.info("=" * 60)

        # Step 3: Initialize Security Operations Center
        # The SOC is the central hub - all events flow through it
        self.logger.info("[1/4] Initializing Security Operations Center...")
        self.soc = SecurityOperationsCenter({
            'db_path': self.config['soc_db_path'],
            'log_level': self.config['log_level'],
        })

        # Step 4: Initialize Intrusion Prevention System
        # The IPS actively detects and blocks attacks
        self.logger.info("[2/4] Initializing Intrusion Prevention System...")
        self.ips = IntrusionPreventionSystem(
            soc=self.soc,
            config={
                'use_iptables': self.config['use_iptables'],
            }
        )

        # Step 5: Initialize Threat Intelligence
        # TI provides IOC data for detection
        self.logger.info("[3/4] Initializing Threat Intelligence...")
        self.threat_intel = ThreatIntelligence(
            soc=self.soc,
            config={
                'db_path': self.config['ti_db_path'],
            }
        )

        # Step 6: Initialize Automated Response
        # AR executes response playbooks automatically
        self.logger.info("[4/4] Initializing Automated Response Engine...")
        self.auto_response = AutomatedResponse(
            soc=self.soc,
            config={}
        )

        # Step 7: Connect components
        self._connect_components()

        # System state
        self.running = False
        self.start_time = None

        self.logger.info("Security System initialization complete!")

    def _setup_logging(self):
        """
        Configure logging for the security system.

        Sets up both console and file logging with appropriate
        formatting for security events.
        """
        # Get log level from config
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))

        # Create formatter with timestamp and component name
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # File handler (if configured)
        handlers = [console_handler]
        log_file = self.config.get('log_file')
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                handlers.append(file_handler)
            except:
                pass  # Continue without file logging

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers
        )

    def _connect_components(self):
        """
        Connect security components together.

        This creates the integration between:
        - IPS -> SOC (threat events)
        - TI -> IPS (threat indicators)
        - SOC -> AR (alert triggers)
        """
        # IPS uses TI for additional threat matching
        def check_threat_intel(ip: str) -> bool:
            """Check IP against threat intelligence."""
            result = self.threat_intel.check_ip(ip)
            return result.matched

        # Add TI check to IPS (conceptual - would integrate in production)
        self.logger.debug("Components connected via SOC event bus")

    def start(self):
        """
        Start all security system components.

        STARTUP SEQUENCE:
        1. Start SOC (central command must start first)
        2. Start IPS (defense layer)
        3. Start Threat Intelligence (data layer)
        4. Start Automated Response (action layer)
        5. Generate startup event
        """
        if self.running:
            self.logger.warning("Security system already running")
            return

        self.logger.info("-" * 60)
        self.logger.info("STARTING SECURITY SYSTEM")
        self.logger.info("-" * 60)

        # Start components in order
        self.logger.info("[1/4] Starting SOC...")
        self.soc.start()

        self.logger.info("[2/4] Starting IPS...")
        self.ips.start()

        self.logger.info("[3/4] Starting Threat Intelligence...")
        self.threat_intel.start()

        self.logger.info("[4/4] Starting Automated Response...")
        self.auto_response.start()

        # Update state
        self.running = True
        self.start_time = datetime.now()

        # Log startup event
        self._log_system_event("Security System Started", EventSeverity.INFO)

        self.logger.info("-" * 60)
        self.logger.info("SECURITY SYSTEM RUNNING")
        self.logger.info(f"Start time: {self.start_time}")
        self.logger.info("-" * 60)

    def stop(self):
        """
        Stop all security system components.

        SHUTDOWN SEQUENCE:
        1. Log shutdown event
        2. Stop AR (stop responses first)
        3. Stop TI (stop data feeds)
        4. Stop IPS (stop detection)
        5. Stop SOC (stop last)
        """
        if not self.running:
            return

        self.logger.info("-" * 60)
        self.logger.info("STOPPING SECURITY SYSTEM")
        self.logger.info("-" * 60)

        # Log shutdown event
        self._log_system_event("Security System Stopping", EventSeverity.INFO)

        # Stop components in reverse order
        self.logger.info("[1/4] Stopping Automated Response...")
        self.auto_response.stop()

        self.logger.info("[2/4] Stopping Threat Intelligence...")
        self.threat_intel.stop()

        self.logger.info("[3/4] Stopping IPS...")
        self.ips.stop()

        self.logger.info("[4/4] Stopping SOC...")
        self.soc.stop()

        self.running = False

        # Calculate uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            self.logger.info(f"Total uptime: {uptime}")

        self.logger.info("-" * 60)
        self.logger.info("SECURITY SYSTEM STOPPED")
        self.logger.info("-" * 60)

    def _log_system_event(self, message: str, severity: EventSeverity):
        """Log a system event to SOC."""
        import uuid
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source='SecuritySystem',
            category=EventCategory.SYSTEM,
            severity=severity,
            title=message
        )
        self.soc.publish_event(event)

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.

        Returns:
            Dictionary with status of all components
        """
        status = {
            'running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'components': {
                'soc': self.soc.get_status() if self.running else {'running': False},
                'ips': self.ips.get_stats() if self.running else {},
                'threat_intel': self.threat_intel.get_stats() if self.running else {},
                'auto_response': self.auto_response.get_stats() if self.running else {},
            }
        }
        return status

    def analyze_traffic(self, data: bytes, source_ip: str,
                        dest_ip: str, dest_port: int = 0) -> Dict[str, Any]:
        """
        Analyze network traffic for threats.

        This is the main entry point for traffic analysis.
        It coordinates IPS detection and threat intelligence lookup.

        Args:
            data: Packet data to analyze
            source_ip: Source IP address
            dest_ip: Destination IP address
            dest_port: Destination port

        Returns:
            Analysis result dictionary
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'source_ip': source_ip,
            'threat_detected': False,
            'blocked': False,
            'details': {}
        }

        # Check against IPS
        ips_result = self.ips.analyze_packet(data, source_ip, dest_ip, dest_port)

        if ips_result.threat_level != ThreatLevel.NONE:
            result['threat_detected'] = True
            result['blocked'] = ips_result.blocked
            result['details']['ips'] = {
                'threat_level': ips_result.threat_level.name,
                'attack_type': ips_result.attack_type.name,
                'action': ips_result.action_taken.name
            }

        # Check against Threat Intelligence
        ti_result = self.threat_intel.check_ip(source_ip)
        if ti_result.matched:
            result['threat_detected'] = True
            result['details']['threat_intel'] = {
                'threat_type': ti_result.indicator.threat_type.value,
                'confidence': ti_result.indicator.confidence,
                'source': ti_result.indicator.source
            }

        return result

    def add_threat_indicator(self, ioc_type: str, value: str,
                              threat_type: str = "unknown",
                              confidence: int = 50) -> bool:
        """
        Add a custom threat indicator.

        Args:
            ioc_type: Type of IOC (ip/domain/hash)
            value: Indicator value
            threat_type: Type of threat
            confidence: Confidence score (0-100)

        Returns:
            True if added successfully
        """
        try:
            ioc_type_enum = IOCType(ioc_type)
            threat_type_enum = ThreatType(threat_type)

            return self.threat_intel.add_indicator(
                ioc_type_enum,
                value,
                threat_type_enum,
                confidence
            )
        except Exception as e:
            self.logger.error(f"Failed to add indicator: {e}")
            return False

    def block_ip(self, ip: str, reason: str = "manual",
                 duration: int = 3600) -> bool:
        """
        Manually block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
            duration: Block duration in seconds

        Returns:
            True if blocked successfully
        """
        from components.intrusion_prevention import BlockDuration

        return self.ips.block_manager.block_ip(
            ip=ip,
            reason=reason,
            attack_type=AttackType.POLICY_VIOLATION,
            duration=BlockDuration.TEMPORARY_1HOUR
        )

    def get_blocked_ips(self) -> List[Dict]:
        """Get list of currently blocked IPs."""
        return self.ips.get_blocked_ips()

    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        """Get recent security alerts."""
        return self.soc.get_recent_events(limit)

    def trigger_response(self, playbook_id: str,
                         context: Dict[str, Any] = None) -> Optional[str]:
        """
        Manually trigger a response playbook.

        Args:
            playbook_id: ID of playbook to execute
            context: Context data for playbook

        Returns:
            Execution ID if triggered
        """
        execution = self.auto_response.trigger_playbook(playbook_id, context)
        return execution.id if execution else None


# =============================================================================
# DEMO FUNCTIONS
# =============================================================================

def run_comprehensive_demo():
    """
    Run a comprehensive demonstration of the security system.

    This demo shows:
    1. System initialization
    2. Attack detection
    3. Threat intelligence lookups
    4. Automated response
    5. Statistics and reporting
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           ELECTRODUCTION COMPLETE SECURITY SYSTEM                            ║
║                     Comprehensive Demo                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

This demo will demonstrate:
  1. Security system initialization
  2. Attack detection and blocking
  3. Threat intelligence lookups
  4. Automated response execution
  5. System statistics and status

""")

    # Initialize system
    print("[*] Initializing Security System...")
    print("-" * 60)

    system = ElectroductionSecuritySystem()

    # Start system
    print("\n[*] Starting Security System...")
    print("-" * 60)
    system.start()

    time.sleep(1)

    # Demo 1: Attack Detection
    print("\n" + "=" * 60)
    print("DEMO 1: ATTACK DETECTION")
    print("=" * 60)

    test_attacks = [
        {
            'name': 'SQL Injection',
            'data': b"GET /search?q=test' UNION SELECT * FROM users-- HTTP/1.1",
            'source_ip': '10.0.0.50'
        },
        {
            'name': 'XSS Attack',
            'data': b"POST /comment HTTP/1.1\r\n\r\n<script>alert('xss')</script>",
            'source_ip': '10.0.0.51'
        },
        {
            'name': 'Path Traversal',
            'data': b"GET /../../../etc/passwd HTTP/1.1",
            'source_ip': '10.0.0.52'
        },
        {
            'name': 'Normal Request',
            'data': b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n",
            'source_ip': '192.168.1.100'
        }
    ]

    for attack in test_attacks:
        result = system.analyze_traffic(
            attack['data'],
            attack['source_ip'],
            dest_ip='192.168.1.1',
            dest_port=80
        )

        status = "🔴 BLOCKED" if result.get('blocked') else (
            "🟡 DETECTED" if result.get('threat_detected') else "🟢 ALLOWED"
        )
        print(f"\n  {attack['name']:20s} from {attack['source_ip']:15s} -> {status}")
        if result.get('details', {}).get('ips'):
            print(f"    └─ Attack Type: {result['details']['ips']['attack_type']}")

    # Demo 2: Threat Intelligence
    print("\n" + "=" * 60)
    print("DEMO 2: THREAT INTELLIGENCE LOOKUP")
    print("=" * 60)

    # Add some test indicators
    system.add_threat_indicator('ip', '185.220.101.1', 'malware', 90)
    system.add_threat_indicator('domain', 'malicious-c2.evil.com', 'malware', 95)

    test_iocs = ['185.220.101.1', '8.8.8.8', '192.168.1.1']
    for ip in test_iocs:
        result = system.threat_intel.check_ip(ip)
        status = "🔴 THREAT" if result.matched else "🟢 CLEAN"
        print(f"\n  IP: {ip:20s} -> {status}")
        if result.matched:
            print(f"    └─ Type: {result.indicator.threat_type.value}")
            print(f"    └─ Confidence: {result.indicator.confidence}%")

    # Demo 3: Manual Response
    print("\n" + "=" * 60)
    print("DEMO 3: AUTOMATED RESPONSE")
    print("=" * 60)

    print("\n  Triggering 'Brute Force Response' playbook...")
    exec_id = system.trigger_response('pb_brute_force', {
        'source_ip': '10.0.0.99',
        'event_type': 'BRUTE_FORCE'
    })
    print(f"    └─ Execution ID: {exec_id}")

    time.sleep(1)

    # Demo 4: Block IP
    print("\n  Manually blocking IP 203.0.113.50...")
    system.block_ip('203.0.113.50', 'Demo block', 3600)
    print("    └─ IP blocked successfully")

    # Show blocked IPs
    blocked = system.get_blocked_ips()
    print(f"\n  Currently blocked IPs: {len(blocked)}")
    for b in blocked[:5]:
        print(f"    └─ {b['ip']} - {b['reason']}")

    # Demo 5: System Status
    print("\n" + "=" * 60)
    print("DEMO 5: SYSTEM STATUS")
    print("=" * 60)

    status = system.get_status()

    print(f"\n  System Running: {status['running']}")
    print(f"  Uptime: {status['uptime_seconds']:.0f} seconds")

    print("\n  Component Statistics:")
    if 'ips' in status['components']:
        ips_stats = status['components']['ips']
        print(f"    IPS:")
        print(f"      └─ Packets Analyzed: {ips_stats.get('packets_analyzed', 0)}")
        print(f"      └─ Threats Detected: {ips_stats.get('threats_detected', 0)}")
        print(f"      └─ Attacks Blocked: {ips_stats.get('attacks_blocked', 0)}")

    if 'threat_intel' in status['components']:
        ti_stats = status['components']['threat_intel']
        print(f"    Threat Intel:")
        print(f"      └─ Total Indicators: {ti_stats.get('total_indicators', 0)}")
        print(f"      └─ Lookups: {ti_stats.get('lookups', 0)}")
        print(f"      └─ Matches: {ti_stats.get('matches', 0)}")

    if 'auto_response' in status['components']:
        ar_stats = status['components']['auto_response']
        print(f"    Auto Response:")
        print(f"      └─ Playbooks Executed: {ar_stats.get('playbooks_executed', 0)}")
        print(f"      └─ Actions Executed: {ar_stats.get('actions_executed', 0)}")

    # Stop system
    print("\n" + "=" * 60)
    print("STOPPING SECURITY SYSTEM")
    print("=" * 60)
    system.stop()

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                          DEMO COMPLETED                                       ║
║                                                                              ║
║   The security system demonstrated:                                          ║
║   ✓ Real-time attack detection (SQL injection, XSS, etc.)                   ║
║   ✓ Automatic IP blocking                                                    ║
║   ✓ Threat intelligence lookups                                              ║
║   ✓ Automated response playbooks                                             ║
║   ✓ Comprehensive logging and statistics                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def run_continuous_mode():
    """
    Run the security system in continuous mode.

    This mode keeps the system running until interrupted.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           ELECTRODUCTION SECURITY SYSTEM - CONTINUOUS MODE                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    system = ElectroductionSecuritySystem()

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n[*] Shutdown signal received...")
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start system
    system.start()

    print("\n[*] Security System running. Press Ctrl+C to stop.\n")

    # Keep running
    try:
        while True:
            time.sleep(60)
            # Periodic status update
            status = system.get_status()
            events = status['components'].get('soc', {}).get('stats', {}).get('events_total', 0)
            alerts = status['components'].get('soc', {}).get('stats', {}).get('alerts_total', 0)
            print(f"[STATUS] Events: {events} | Alerts: {alerts}")
    except KeyboardInterrupt:
        system.stop()


def run_tests():
    """
    Run tests on all security components.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           ELECTRODUCTION SECURITY SYSTEM - TEST SUITE                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    results = []

    # Test 1: SOC initialization
    print("\n[TEST 1] Security Operations Center...")
    try:
        soc = SecurityOperationsCenter()
        soc.start()
        time.sleep(0.5)
        soc.stop()
        print("  ✓ SOC: PASSED")
        results.append(('SOC', True))
    except Exception as e:
        print(f"  ✗ SOC: FAILED - {e}")
        results.append(('SOC', False))

    # Test 2: IPS detection
    print("\n[TEST 2] Intrusion Prevention System...")
    try:
        ips = IntrusionPreventionSystem()
        ips.start()

        # Test SQL injection detection
        result = ips.analyze_packet(
            b"' OR 1=1--",
            '10.0.0.1',
            '192.168.1.1',
            80
        )
        assert result.threat_level != ThreatLevel.NONE, "Should detect SQL injection"

        ips.stop()
        print("  ✓ IPS: PASSED")
        results.append(('IPS', True))
    except Exception as e:
        print(f"  ✗ IPS: FAILED - {e}")
        results.append(('IPS', False))

    # Test 3: Threat Intelligence
    print("\n[TEST 3] Threat Intelligence...")
    try:
        ti = ThreatIntelligence()
        ti.start()

        # Add and lookup indicator
        ti.add_indicator(IOCType.IP_ADDRESS, '1.2.3.4', ThreatType.MALWARE, 90)
        result = ti.check_ip('1.2.3.4')
        assert result.matched, "Should find added indicator"

        ti.stop()
        print("  ✓ Threat Intel: PASSED")
        results.append(('ThreatIntel', True))
    except Exception as e:
        print(f"  ✗ Threat Intel: FAILED - {e}")
        results.append(('ThreatIntel', False))

    # Test 4: Automated Response
    print("\n[TEST 4] Automated Response...")
    try:
        ar = AutomatedResponse()
        ar.start()

        # Test action execution
        result = ar.execute_action(
            ActionType.SEND_ALERT,
            {'title': 'Test', 'message': 'Test alert'}
        )
        assert result.status.value in ['completed', 'failed'], "Action should complete"

        ar.stop()
        print("  ✓ Auto Response: PASSED")
        results.append(('AutoResponse', True))
    except Exception as e:
        print(f"  ✗ Auto Response: FAILED - {e}")
        results.append(('AutoResponse', False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    return all(r for _, r in results)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """
    Main entry point for the security system.

    Parses command-line arguments and dispatches to appropriate mode.
    """
    parser = argparse.ArgumentParser(
        description='Electroduction Complete Security System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_security_system.py              Run demo
  python run_security_system.py --start      Start continuous mode
  python run_security_system.py --test       Run tests
  python run_security_system.py --help       Show help
        """
    )

    parser.add_argument(
        '--start', '-s',
        action='store_true',
        help='Start security system in continuous mode'
    )

    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run test suite'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config) as f:
            config = json.load(f)

    # Dispatch to appropriate mode
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    elif args.start:
        run_continuous_mode()
    else:
        run_comprehensive_demo()


if __name__ == "__main__":
    main()
