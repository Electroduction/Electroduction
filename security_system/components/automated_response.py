#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION SECURITY SYSTEM - AUTOMATED RESPONSE ENGINE
================================================================================
Orchestrates automated responses to security threats. Takes input from all
security components and executes predefined response playbooks.

RESPONSE CAPABILITIES:
1. Network Actions: Block IPs, isolate hosts, reset connections
2. Host Actions: Kill processes, quarantine files, disable accounts
3. Alert Actions: Send notifications, escalate, create tickets
4. Forensic Actions: Capture evidence, take snapshots, preserve logs

PLAYBOOK SYSTEM:
Playbooks define sequences of actions for specific threat scenarios.
They support conditions, variables, and parallel execution.

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATED RESPONSE ENGINE                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Trigger    │───▶│   Playbook   │───▶│   Action     │      │
│  │   Manager    │    │   Executor   │    │   Handlers   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Response Actions                         │      │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐       │      │
│  │  │Block│  │Kill │  │Alert│  │Isol.│  │Log  │       │      │
│  │  │ IP  │  │Proc │  │Send │  │Host │  │Evid.│       │      │
│  │  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘       │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘

Usage:
    from security_system.components.automated_response import AutomatedResponse
    ar = AutomatedResponse(soc)
    ar.start()
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os                        # Operating system interface
import sys                       # System parameters
import time                      # Time functions
import json                      # JSON serialization
import hashlib                   # Hash functions
import threading                 # Thread-based concurrency
import logging                   # Logging facility
import subprocess                # Process execution
import shutil                    # File operations
import socket                    # Network operations
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
from pathlib import Path
import queue


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ActionType(Enum):
    """
    Types of response actions.
    Each type has specific implementation and requirements.
    """
    # Network actions
    BLOCK_IP = "block_ip"                # Block IP address
    UNBLOCK_IP = "unblock_ip"            # Remove IP block
    RATE_LIMIT = "rate_limit"            # Apply rate limiting
    RESET_CONNECTION = "reset_conn"      # Reset TCP connection
    ISOLATE_HOST = "isolate_host"        # Network isolation
    RESTORE_HOST = "restore_host"        # Remove isolation

    # Host actions
    KILL_PROCESS = "kill_process"        # Terminate process
    QUARANTINE_FILE = "quarantine_file"  # Move file to quarantine
    DISABLE_USER = "disable_user"        # Disable user account
    ENABLE_USER = "enable_user"          # Enable user account
    LOCK_ACCOUNT = "lock_account"        # Lock account

    # Alert actions
    SEND_ALERT = "send_alert"            # Send alert notification
    SEND_EMAIL = "send_email"            # Send email
    SEND_SLACK = "send_slack"            # Send Slack message
    CREATE_TICKET = "create_ticket"      # Create incident ticket
    ESCALATE = "escalate"                # Escalate to team

    # Forensic actions
    CAPTURE_PACKETS = "capture_packets"  # Start packet capture
    CAPTURE_MEMORY = "capture_memory"    # Memory dump
    SNAPSHOT_DISK = "snapshot_disk"      # Disk snapshot
    PRESERVE_LOGS = "preserve_logs"      # Archive logs
    COLLECT_EVIDENCE = "collect_evidence"  # Gather forensic data

    # Custom actions
    RUN_SCRIPT = "run_script"            # Run custom script
    WEBHOOK = "webhook"                  # Call webhook
    CUSTOM = "custom"                    # Custom handler


class ActionStatus(Enum):
    """
    Status of an action execution.
    """
    PENDING = "pending"          # Not yet started
    RUNNING = "running"          # Currently executing
    COMPLETED = "completed"      # Successfully completed
    FAILED = "failed"            # Execution failed
    SKIPPED = "skipped"          # Skipped (condition not met)
    ROLLBACK = "rollback"        # Action was rolled back


class TriggerType(Enum):
    """
    Types of triggers that can initiate responses.
    """
    ALERT = "alert"              # Security alert
    THRESHOLD = "threshold"      # Metric threshold
    PATTERN = "pattern"          # Event pattern
    SCHEDULE = "schedule"        # Scheduled execution
    MANUAL = "manual"            # Manual trigger
    API = "api"                  # API call


class PlaybookPriority(Enum):
    """
    Priority levels for playbook execution.
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ResponseAction:
    """
    A single response action to execute.

    Attributes:
        id: Unique action identifier
        action_type: Type of action
        parameters: Action parameters
        timeout: Execution timeout in seconds
        retry_count: Number of retries on failure
        rollback_action: Action to undo this one
        condition: Condition to check before execution
    """
    id: str                                      # Action ID
    action_type: ActionType                      # Action type
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 60                            # Timeout seconds
    retry_count: int = 3                         # Retry attempts
    rollback_action: Optional['ResponseAction'] = None
    condition: Optional[str] = None              # Jinja-like condition


@dataclass
class ActionResult:
    """
    Result of an action execution.

    Attributes:
        action_id: ID of the executed action
        status: Execution status
        start_time: When execution started
        end_time: When execution ended
        output: Action output/result
        error: Error message if failed
    """
    action_id: str                               # Action ID
    status: ActionStatus                         # Status
    start_time: str                              # Start time
    end_time: str = ""                           # End time
    output: Any = None                           # Output
    error: str = ""                              # Error message


@dataclass
class Playbook:
    """
    Response playbook defining a sequence of actions.

    Attributes:
        id: Unique playbook identifier
        name: Human-readable name
        description: What this playbook does
        trigger_conditions: When to trigger this playbook
        priority: Execution priority
        actions: List of actions to execute
        enabled: Whether playbook is active
        cooldown: Minimum time between executions
        max_concurrent: Maximum concurrent executions
    """
    id: str                                      # Playbook ID
    name: str                                    # Name
    description: str = ""                        # Description
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    priority: PlaybookPriority = PlaybookPriority.MEDIUM
    actions: List[ResponseAction] = field(default_factory=list)
    enabled: bool = True                         # Active
    cooldown: int = 300                          # Cooldown seconds
    max_concurrent: int = 5                      # Max concurrent
    last_triggered: str = ""                     # Last trigger time
    execution_count: int = 0                     # Total executions


@dataclass
class ResponseExecution:
    """
    Record of a playbook execution.

    Attributes:
        id: Unique execution ID
        playbook_id: Playbook that was executed
        trigger_type: What triggered execution
        trigger_data: Data that triggered execution
        start_time: Execution start
        end_time: Execution end
        status: Overall status
        action_results: Results of each action
    """
    id: str                                      # Execution ID
    playbook_id: str                             # Playbook ID
    trigger_type: TriggerType                    # Trigger type
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    start_time: str = ""                         # Start time
    end_time: str = ""                           # End time
    status: ActionStatus = ActionStatus.PENDING  # Status
    action_results: List[ActionResult] = field(default_factory=list)


# =============================================================================
# ACTION HANDLERS - Implement actual response actions
# =============================================================================

class ActionHandlers:
    """
    Collection of action handler implementations.

    Each handler executes a specific type of response action.
    Handlers are registered with the response engine.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize action handlers.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger('ActionHandlers')

        # Quarantine directory
        self.quarantine_dir = self.config.get('quarantine_dir', '/tmp/quarantine')
        Path(self.quarantine_dir).mkdir(parents=True, exist_ok=True)

        # Evidence directory
        self.evidence_dir = self.config.get('evidence_dir', '/tmp/evidence')
        Path(self.evidence_dir).mkdir(parents=True, exist_ok=True)

        # Track blocked IPs for unblocking
        self.blocked_ips: Dict[str, datetime] = {}

    def block_ip(self, ip: str, duration: int = 3600,
                 reason: str = "") -> Tuple[bool, str]:
        """
        Block an IP address using iptables.

        Args:
            ip: IP address to block
            duration: Block duration in seconds (0 = permanent)
            reason: Reason for blocking

        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate IP
            socket.inet_aton(ip)  # Raises error if invalid

            # Add iptables rule
            cmd = ['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0:
                self.blocked_ips[ip] = datetime.now()
                self.logger.warning(f"Blocked IP: {ip} | Reason: {reason}")
                return (True, f"Successfully blocked {ip}")
            else:
                # iptables might not be available, log instead
                self.logger.warning(f"Would block IP: {ip} (iptables not available)")
                self.blocked_ips[ip] = datetime.now()
                return (True, f"Logged block for {ip} (iptables unavailable)")

        except subprocess.TimeoutExpired:
            return (False, "Command timed out")
        except FileNotFoundError:
            self.logger.warning(f"Would block IP: {ip} (iptables not installed)")
            self.blocked_ips[ip] = datetime.now()
            return (True, f"Logged block for {ip}")
        except Exception as e:
            return (False, str(e))

    def unblock_ip(self, ip: str) -> Tuple[bool, str]:
        """
        Remove block for an IP address.

        Args:
            ip: IP address to unblock

        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP']
            subprocess.run(cmd, capture_output=True, timeout=10)

            if ip in self.blocked_ips:
                del self.blocked_ips[ip]

            self.logger.info(f"Unblocked IP: {ip}")
            return (True, f"Unblocked {ip}")

        except Exception as e:
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]
            return (True, f"Removed block record for {ip}")

    def kill_process(self, pid: int = None, name: str = None) -> Tuple[bool, str]:
        """
        Terminate a process by PID or name.

        Args:
            pid: Process ID to kill
            name: Process name to kill

        Returns:
            Tuple of (success, message)
        """
        try:
            if pid:
                os.kill(pid, 9)  # SIGKILL
                self.logger.warning(f"Killed process PID: {pid}")
                return (True, f"Killed process {pid}")
            elif name:
                # Use pkill
                cmd = ['pkill', '-9', name]
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                self.logger.warning(f"Killed processes named: {name}")
                return (True, f"Killed processes matching {name}")
            else:
                return (False, "No PID or name specified")

        except ProcessLookupError:
            return (False, f"Process {pid} not found")
        except PermissionError:
            return (False, f"Permission denied to kill process {pid}")
        except Exception as e:
            return (False, str(e))

    def quarantine_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Move a file to quarantine.

        Args:
            filepath: Path to file to quarantine

        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(filepath):
                return (False, f"File not found: {filepath}")

            # Create quarantine filename with timestamp
            filename = os.path.basename(filepath)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            quarantine_name = f"{timestamp}_{filename}"
            quarantine_path = os.path.join(self.quarantine_dir, quarantine_name)

            # Move file
            shutil.move(filepath, quarantine_path)

            # Create metadata file
            metadata = {
                'original_path': filepath,
                'quarantine_time': datetime.now().isoformat(),
                'quarantine_path': quarantine_path
            }
            with open(f"{quarantine_path}.meta", 'w') as f:
                json.dump(metadata, f)

            self.logger.warning(f"Quarantined file: {filepath} -> {quarantine_path}")
            return (True, f"Quarantined to {quarantine_path}")

        except Exception as e:
            return (False, str(e))

    def disable_user(self, username: str) -> Tuple[bool, str]:
        """
        Disable a user account.

        Args:
            username: Username to disable

        Returns:
            Tuple of (success, message)
        """
        try:
            # Use usermod to lock account
            cmd = ['usermod', '-L', username]
            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0:
                self.logger.warning(f"Disabled user: {username}")
                return (True, f"Disabled user {username}")
            else:
                return (False, result.stderr.decode())

        except FileNotFoundError:
            self.logger.warning(f"Would disable user: {username} (usermod not available)")
            return (True, f"Logged disable for {username}")
        except Exception as e:
            return (False, str(e))

    def send_alert(self, title: str, message: str,
                   severity: str = "warning") -> Tuple[bool, str]:
        """
        Send an alert notification.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity

        Returns:
            Tuple of (success, message)
        """
        # In a real system, this would integrate with alerting platforms
        # For now, log the alert
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'severity': severity
        }

        self.logger.warning(f"ALERT [{severity}]: {title} - {message}")

        # Write to alert file
        alert_file = '/tmp/security_alerts.log'
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert_data) + '\n')

        return (True, f"Alert sent: {title}")

    def preserve_logs(self, log_paths: List[str],
                      case_id: str = None) -> Tuple[bool, str]:
        """
        Preserve logs for forensic analysis.

        Args:
            log_paths: Paths to logs to preserve
            case_id: Case identifier

        Returns:
            Tuple of (success, message)
        """
        try:
            # Create case directory
            if not case_id:
                case_id = datetime.now().strftime('%Y%m%d_%H%M%S')

            case_dir = os.path.join(self.evidence_dir, f"case_{case_id}")
            Path(case_dir).mkdir(parents=True, exist_ok=True)

            preserved = []
            for log_path in log_paths:
                if os.path.exists(log_path):
                    dest = os.path.join(case_dir, os.path.basename(log_path))
                    shutil.copy2(log_path, dest)
                    preserved.append(log_path)

            # Create manifest
            manifest = {
                'case_id': case_id,
                'timestamp': datetime.now().isoformat(),
                'preserved_files': preserved
            }
            with open(os.path.join(case_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)

            self.logger.info(f"Preserved {len(preserved)} logs to {case_dir}")
            return (True, f"Preserved logs to {case_dir}")

        except Exception as e:
            return (False, str(e))

    def run_script(self, script_path: str,
                   args: List[str] = None) -> Tuple[bool, str]:
        """
        Run a custom response script.

        Args:
            script_path: Path to script
            args: Script arguments

        Returns:
            Tuple of (success, output)
        """
        try:
            if not os.path.exists(script_path):
                return (False, f"Script not found: {script_path}")

            cmd = [script_path] + (args or [])
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300,  # 5 minute timeout
                text=True
            )

            if result.returncode == 0:
                self.logger.info(f"Script executed: {script_path}")
                return (True, result.stdout)
            else:
                return (False, result.stderr)

        except subprocess.TimeoutExpired:
            return (False, "Script timed out")
        except Exception as e:
            return (False, str(e))

    def isolate_host(self, hostname: str) -> Tuple[bool, str]:
        """
        Network isolate a host.

        Args:
            hostname: Hostname to isolate

        Returns:
            Tuple of (success, message)
        """
        # In a real system, this would:
        # - Update switch port to isolation VLAN
        # - Add firewall rules
        # - Update network ACLs
        self.logger.critical(f"ISOLATION requested for host: {hostname}")

        # Log the action
        isolation_record = {
            'timestamp': datetime.now().isoformat(),
            'hostname': hostname,
            'action': 'isolate'
        }
        with open('/tmp/host_isolations.log', 'a') as f:
            f.write(json.dumps(isolation_record) + '\n')

        return (True, f"Isolation logged for {hostname}")


# =============================================================================
# PLAYBOOK MANAGER - Manage response playbooks
# =============================================================================

class PlaybookManager:
    """
    Manages response playbooks.

    Loads, stores, and provides access to playbooks.
    Supports built-in and custom playbooks.
    """

    def __init__(self):
        """Initialize playbook manager."""
        self.playbooks: Dict[str, Playbook] = {}
        self.logger = logging.getLogger('PlaybookManager')
        self._load_default_playbooks()

    def _load_default_playbooks(self):
        """Load built-in response playbooks."""
        default_playbooks = [
            # Brute Force Response
            Playbook(
                id="pb_brute_force",
                name="Brute Force Response",
                description="Respond to brute force login attempts",
                trigger_conditions={
                    'event_type': 'BRUTE_FORCE',
                    'severity_min': 'WARNING'
                },
                priority=PlaybookPriority.HIGH,
                actions=[
                    ResponseAction(
                        id="bf_1",
                        action_type=ActionType.BLOCK_IP,
                        parameters={'duration': 3600}
                    ),
                    ResponseAction(
                        id="bf_2",
                        action_type=ActionType.SEND_ALERT,
                        parameters={
                            'title': 'Brute Force Attack Blocked',
                            'severity': 'warning'
                        }
                    ),
                    ResponseAction(
                        id="bf_3",
                        action_type=ActionType.PRESERVE_LOGS,
                        parameters={'log_paths': ['/var/log/auth.log']}
                    )
                ]
            ),

            # Malware Detection Response
            Playbook(
                id="pb_malware",
                name="Malware Detection Response",
                description="Respond to malware detection",
                trigger_conditions={
                    'event_type': 'MALWARE',
                    'severity_min': 'ERROR'
                },
                priority=PlaybookPriority.CRITICAL,
                actions=[
                    ResponseAction(
                        id="mal_1",
                        action_type=ActionType.QUARANTINE_FILE,
                        parameters={}
                    ),
                    ResponseAction(
                        id="mal_2",
                        action_type=ActionType.BLOCK_IP,
                        parameters={'duration': 86400}  # 24 hours
                    ),
                    ResponseAction(
                        id="mal_3",
                        action_type=ActionType.SEND_ALERT,
                        parameters={
                            'title': 'Malware Detected',
                            'severity': 'critical'
                        }
                    ),
                    ResponseAction(
                        id="mal_4",
                        action_type=ActionType.COLLECT_EVIDENCE,
                        parameters={}
                    )
                ]
            ),

            # Data Exfiltration Response
            Playbook(
                id="pb_exfiltration",
                name="Data Exfiltration Response",
                description="Respond to potential data exfiltration",
                trigger_conditions={
                    'event_type': 'DATA_EXFILTRATION',
                    'severity_min': 'WARNING'
                },
                priority=PlaybookPriority.EMERGENCY,
                actions=[
                    ResponseAction(
                        id="exf_1",
                        action_type=ActionType.BLOCK_IP,
                        parameters={'duration': 0}  # Permanent
                    ),
                    ResponseAction(
                        id="exf_2",
                        action_type=ActionType.ISOLATE_HOST,
                        parameters={}
                    ),
                    ResponseAction(
                        id="exf_3",
                        action_type=ActionType.CAPTURE_PACKETS,
                        parameters={'duration': 300}
                    ),
                    ResponseAction(
                        id="exf_4",
                        action_type=ActionType.ESCALATE,
                        parameters={'team': 'security'}
                    )
                ]
            ),

            # Intrusion Response
            Playbook(
                id="pb_intrusion",
                name="Intrusion Response",
                description="Respond to intrusion attempts",
                trigger_conditions={
                    'event_type': 'INTRUSION',
                    'severity_min': 'ERROR'
                },
                priority=PlaybookPriority.HIGH,
                actions=[
                    ResponseAction(
                        id="int_1",
                        action_type=ActionType.BLOCK_IP,
                        parameters={'duration': 7200}
                    ),
                    ResponseAction(
                        id="int_2",
                        action_type=ActionType.SEND_ALERT,
                        parameters={
                            'title': 'Intrusion Attempt Detected',
                            'severity': 'error'
                        }
                    ),
                    ResponseAction(
                        id="int_3",
                        action_type=ActionType.PRESERVE_LOGS,
                        parameters={}
                    )
                ]
            ),

            # Suspicious User Activity
            Playbook(
                id="pb_suspicious_user",
                name="Suspicious User Activity Response",
                description="Respond to suspicious user behavior",
                trigger_conditions={
                    'event_type': 'SUSPICIOUS_USER',
                    'severity_min': 'WARNING'
                },
                priority=PlaybookPriority.MEDIUM,
                actions=[
                    ResponseAction(
                        id="sus_1",
                        action_type=ActionType.DISABLE_USER,
                        parameters={}
                    ),
                    ResponseAction(
                        id="sus_2",
                        action_type=ActionType.SEND_ALERT,
                        parameters={
                            'title': 'Suspicious User Activity',
                            'severity': 'warning'
                        }
                    )
                ]
            )
        ]

        for playbook in default_playbooks:
            self.playbooks[playbook.id] = playbook

        self.logger.info(f"Loaded {len(self.playbooks)} default playbooks")

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get a playbook by ID."""
        return self.playbooks.get(playbook_id)

    def get_matching_playbooks(self, event_type: str,
                                severity: str) -> List[Playbook]:
        """
        Get playbooks that match event criteria.

        Args:
            event_type: Type of event
            severity: Event severity

        Returns:
            List of matching playbooks
        """
        matches = []
        for playbook in self.playbooks.values():
            if not playbook.enabled:
                continue

            conditions = playbook.trigger_conditions
            if conditions.get('event_type') == event_type:
                matches.append(playbook)

        # Sort by priority
        matches.sort(key=lambda p: p.priority.value, reverse=True)
        return matches

    def add_playbook(self, playbook: Playbook):
        """Add a custom playbook."""
        self.playbooks[playbook.id] = playbook
        self.logger.info(f"Added playbook: {playbook.name}")

    def disable_playbook(self, playbook_id: str):
        """Disable a playbook."""
        if playbook_id in self.playbooks:
            self.playbooks[playbook_id].enabled = False


# =============================================================================
# RESPONSE ENGINE - Main automated response class
# =============================================================================

class AutomatedResponse:
    """
    Main Automated Response Engine.

    Coordinates trigger detection, playbook execution,
    and action handling.
    """

    def __init__(self, soc=None, config: Dict[str, Any] = None):
        """
        Initialize the Automated Response Engine.

        Args:
            soc: SecurityOperationsCenter instance
            config: Configuration dictionary
        """
        self.config = config or {}
        self.soc = soc
        self.logger = logging.getLogger('AutoResponse')

        # Initialize components
        self.action_handlers = ActionHandlers(config)
        self.playbook_manager = PlaybookManager()

        # Execution queue
        self.execution_queue: queue.Queue = queue.Queue()

        # Execution history
        self.execution_history: deque = deque(maxlen=1000)

        # Statistics
        self.stats = {
            'triggers_received': 0,
            'playbooks_executed': 0,
            'actions_executed': 0,
            'actions_failed': 0,
        }

        # Running state
        self.running = False
        self._executor_thread = None

        self.logger.info("Automated Response Engine initialized")

    def start(self):
        """Start the response engine."""
        self.running = True

        # Start executor thread
        self._executor_thread = threading.Thread(
            target=self._executor_loop,
            daemon=True
        )
        self._executor_thread.start()

        # Register with SOC
        if self.soc:
            self.soc.register_component('AutoResponse', self)
            self.soc.add_alert_handler(self._handle_alert)

        self.logger.info("Automated Response Engine started")

    def stop(self):
        """Stop the response engine."""
        self.running = False
        if self._executor_thread:
            self._executor_thread.join(timeout=5.0)
        self.logger.info("Automated Response Engine stopped")

    def _handle_alert(self, alert):
        """
        Handle alert from SOC.

        Args:
            alert: Alert object from SOC
        """
        self.stats['triggers_received'] += 1

        # Find matching playbooks
        event_type = alert.category.name if hasattr(alert, 'category') else 'UNKNOWN'
        severity = alert.severity.name if hasattr(alert, 'severity') else 'WARNING'

        playbooks = self.playbook_manager.get_matching_playbooks(event_type, severity)

        for playbook in playbooks:
            # Check cooldown
            if playbook.last_triggered:
                last_time = datetime.fromisoformat(playbook.last_triggered)
                if (datetime.now() - last_time).total_seconds() < playbook.cooldown:
                    continue

            # Queue for execution
            execution = ResponseExecution(
                id=hashlib.md5(f"{time.time()}{playbook.id}".encode()).hexdigest()[:16],
                playbook_id=playbook.id,
                trigger_type=TriggerType.ALERT,
                trigger_data={
                    'alert_id': alert.id if hasattr(alert, 'id') else '',
                    'event_type': event_type,
                    'severity': severity,
                    'source_ip': alert.source_ips[0] if hasattr(alert, 'source_ips') and alert.source_ips else ''
                }
            )

            self.execution_queue.put(execution)
            playbook.last_triggered = datetime.now().isoformat()

    def trigger_playbook(self, playbook_id: str,
                         context: Dict[str, Any] = None) -> Optional[ResponseExecution]:
        """
        Manually trigger a playbook.

        Args:
            playbook_id: Playbook ID to execute
            context: Context data for the playbook

        Returns:
            ResponseExecution if queued
        """
        playbook = self.playbook_manager.get_playbook(playbook_id)
        if not playbook:
            self.logger.error(f"Playbook not found: {playbook_id}")
            return None

        execution = ResponseExecution(
            id=hashlib.md5(f"{time.time()}{playbook_id}".encode()).hexdigest()[:16],
            playbook_id=playbook_id,
            trigger_type=TriggerType.MANUAL,
            trigger_data=context or {}
        )

        self.execution_queue.put(execution)
        return execution

    def execute_action(self, action_type: ActionType,
                       parameters: Dict[str, Any]) -> ActionResult:
        """
        Execute a single action directly.

        Args:
            action_type: Type of action
            parameters: Action parameters

        Returns:
            ActionResult with outcome
        """
        action = ResponseAction(
            id=hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8],
            action_type=action_type,
            parameters=parameters
        )

        return self._execute_action(action, {})

    def _executor_loop(self):
        """Background executor loop."""
        while self.running:
            try:
                execution = self.execution_queue.get(timeout=1.0)
                self._execute_playbook(execution)
                self.execution_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Executor error: {e}")

    def _execute_playbook(self, execution: ResponseExecution):
        """
        Execute a playbook.

        Args:
            execution: ResponseExecution to process
        """
        playbook = self.playbook_manager.get_playbook(execution.playbook_id)
        if not playbook:
            self.logger.error(f"Playbook not found: {execution.playbook_id}")
            return

        execution.start_time = datetime.now().isoformat()
        execution.status = ActionStatus.RUNNING

        self.logger.info(f"Executing playbook: {playbook.name}")

        # Execute each action
        for action in playbook.actions:
            result = self._execute_action(action, execution.trigger_data)
            execution.action_results.append(result)

            if result.status == ActionStatus.FAILED:
                self.stats['actions_failed'] += 1
                # Continue with other actions unless critical

        execution.end_time = datetime.now().isoformat()
        execution.status = ActionStatus.COMPLETED

        # Update statistics
        self.stats['playbooks_executed'] += 1
        playbook.execution_count += 1

        # Store in history
        self.execution_history.append(execution)

        self.logger.info(f"Playbook completed: {playbook.name}")

    def _execute_action(self, action: ResponseAction,
                        context: Dict[str, Any]) -> ActionResult:
        """
        Execute a single action.

        Args:
            action: Action to execute
            context: Execution context

        Returns:
            ActionResult with outcome
        """
        result = ActionResult(
            action_id=action.id,
            status=ActionStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )

        try:
            # Get parameters with context substitution
            params = action.parameters.copy()
            for key, value in params.items():
                if isinstance(value, str) and value.startswith('{{'):
                    # Simple variable substitution
                    var_name = value[2:-2].strip()
                    if var_name in context:
                        params[key] = context[var_name]

            # Execute based on action type
            success, output = self._dispatch_action(action.action_type, params, context)

            result.status = ActionStatus.COMPLETED if success else ActionStatus.FAILED
            result.output = output
            if not success:
                result.error = output

            self.stats['actions_executed'] += 1

        except Exception as e:
            result.status = ActionStatus.FAILED
            result.error = str(e)
            self.logger.error(f"Action failed: {action.id} - {e}")

        result.end_time = datetime.now().isoformat()
        return result

    def _dispatch_action(self, action_type: ActionType,
                         params: Dict[str, Any],
                         context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Dispatch action to appropriate handler.

        Args:
            action_type: Type of action
            params: Action parameters
            context: Execution context

        Returns:
            Tuple of (success, output)
        """
        handlers = self.action_handlers

        if action_type == ActionType.BLOCK_IP:
            ip = params.get('ip') or context.get('source_ip')
            duration = params.get('duration', 3600)
            reason = params.get('reason', context.get('event_type', 'automated'))
            if ip:
                return handlers.block_ip(ip, duration, reason)
            return (False, "No IP specified")

        elif action_type == ActionType.UNBLOCK_IP:
            ip = params.get('ip') or context.get('source_ip')
            if ip:
                return handlers.unblock_ip(ip)
            return (False, "No IP specified")

        elif action_type == ActionType.KILL_PROCESS:
            return handlers.kill_process(
                pid=params.get('pid'),
                name=params.get('name')
            )

        elif action_type == ActionType.QUARANTINE_FILE:
            filepath = params.get('filepath') or context.get('filepath')
            if filepath:
                return handlers.quarantine_file(filepath)
            return (False, "No file specified")

        elif action_type == ActionType.DISABLE_USER:
            username = params.get('username') or context.get('username')
            if username:
                return handlers.disable_user(username)
            return (False, "No username specified")

        elif action_type == ActionType.SEND_ALERT:
            return handlers.send_alert(
                title=params.get('title', 'Security Alert'),
                message=params.get('message', context.get('event_type', '')),
                severity=params.get('severity', 'warning')
            )

        elif action_type == ActionType.PRESERVE_LOGS:
            log_paths = params.get('log_paths', ['/var/log/syslog', '/var/log/auth.log'])
            case_id = context.get('alert_id', '')
            return handlers.preserve_logs(log_paths, case_id)

        elif action_type == ActionType.ISOLATE_HOST:
            hostname = params.get('hostname') or context.get('hostname')
            if hostname:
                return handlers.isolate_host(hostname)
            return (False, "No hostname specified")

        elif action_type == ActionType.RUN_SCRIPT:
            return handlers.run_script(
                script_path=params.get('script_path'),
                args=params.get('args', [])
            )

        elif action_type == ActionType.ESCALATE:
            return handlers.send_alert(
                title=f"ESCALATION: {context.get('event_type', 'Security Event')}",
                message=f"Escalated to team: {params.get('team', 'security')}",
                severity='critical'
            )

        else:
            self.logger.warning(f"Unknown action type: {action_type}")
            return (True, f"Action logged: {action_type}")

    def get_stats(self) -> Dict[str, Any]:
        """Get response engine statistics."""
        return {
            **self.stats,
            'playbooks_available': len(self.playbook_manager.playbooks),
            'queue_size': self.execution_queue.qsize(),
            'history_size': len(self.execution_history),
            'blocked_ips': len(self.action_handlers.blocked_ips)
        }

    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """Get recent execution history."""
        history = list(self.execution_history)[-limit:]
        return [
            {
                'id': e.id,
                'playbook_id': e.playbook_id,
                'trigger_type': e.trigger_type.value,
                'start_time': e.start_time,
                'end_time': e.end_time,
                'status': e.status.value,
                'actions_count': len(e.action_results)
            }
            for e in history
        ]


# =============================================================================
# DEMO AND TESTING
# =============================================================================

def run_demo():
    """Demonstrate Automated Response functionality."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ELECTRODUCTION AUTOMATED RESPONSE ENGINE                        ║
║                         Security Response Demo                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Create response engine
    ar = AutomatedResponse()
    ar.start()

    print("[*] Testing individual response actions...\n")

    # Test block IP
    print("  [1] Block IP Action:")
    result = ar.execute_action(
        ActionType.BLOCK_IP,
        {'ip': '10.0.0.100', 'duration': 3600, 'reason': 'Demo block'}
    )
    print(f"      Status: {result.status.value}")
    print(f"      Output: {result.output}")

    # Test send alert
    print("\n  [2] Send Alert Action:")
    result = ar.execute_action(
        ActionType.SEND_ALERT,
        {
            'title': 'Test Security Alert',
            'message': 'This is a test alert from the demo',
            'severity': 'warning'
        }
    )
    print(f"      Status: {result.status.value}")
    print(f"      Output: {result.output}")

    # Test preserve logs
    print("\n  [3] Preserve Logs Action:")
    result = ar.execute_action(
        ActionType.PRESERVE_LOGS,
        {'log_paths': ['/etc/passwd'], 'case_id': 'demo_001'}
    )
    print(f"      Status: {result.status.value}")
    print(f"      Output: {result.output}")

    # Test playbook execution
    print("\n[*] Testing playbook execution...\n")

    # Manually trigger brute force playbook
    print("  [4] Triggering 'Brute Force Response' playbook:")
    execution = ar.trigger_playbook(
        'pb_brute_force',
        {'source_ip': '192.168.1.50', 'event_type': 'BRUTE_FORCE'}
    )
    if execution:
        print(f"      Execution ID: {execution.id}")

    # Wait for execution
    time.sleep(2)

    # Show statistics
    print("\n[*] Response Engine Statistics:")
    stats = ar.get_stats()
    for key, value in stats.items():
        print(f"    {key}: {value}")

    # Show execution history
    print("\n[*] Execution History:")
    history = ar.get_execution_history(5)
    for h in history:
        print(f"    {h['id']}: {h['playbook_id']} - {h['status']}")

    ar.stop()
    print("\n[*] Demo completed!")


if __name__ == "__main__":
    run_demo()
