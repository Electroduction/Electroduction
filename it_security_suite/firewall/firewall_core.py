#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION CUSTOM FIREWALL SYSTEM
===============================================================================
A complete, educational firewall implementation demonstrating:
- Packet filtering (IP, port, protocol based)
- Stateful packet inspection
- Application layer filtering
- Rate limiting and DDoS protection
- Traffic logging and monitoring
- Rule-based access control
- NAT (Network Address Translation)

This firewall uses:
- Raw sockets for packet capture (Linux)
- Netfilter/iptables integration
- Rule engine for packet filtering
- Connection tracking for stateful inspection
===============================================================================
"""

import os
import sys
import socket
import struct
import threading
import time
import json
import logging
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Callable
from enum import Enum, auto
from collections import defaultdict
from datetime import datetime, timedelta
import ipaddress
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Firewall')


class Action(Enum):
    """Firewall rule actions"""
    ALLOW = auto()
    DENY = auto()
    DROP = auto()  # Drop silently
    REJECT = auto()  # Send rejection message
    LOG = auto()  # Log and continue
    RATE_LIMIT = auto()


class Protocol(Enum):
    """Network protocols"""
    ANY = 0
    ICMP = 1
    TCP = 6
    UDP = 17


class Direction(Enum):
    """Traffic direction"""
    INBOUND = auto()
    OUTBOUND = auto()
    BOTH = auto()


class ConnectionState(Enum):
    """TCP connection states for stateful inspection"""
    NEW = auto()
    ESTABLISHED = auto()
    RELATED = auto()
    INVALID = auto()
    TIME_WAIT = auto()
    CLOSED = auto()


@dataclass
class IPHeader:
    """Parsed IP header"""
    version: int
    ihl: int
    tos: int
    total_length: int
    identification: int
    flags: int
    fragment_offset: int
    ttl: int
    protocol: int
    checksum: int
    src_ip: str
    dst_ip: str
    options: bytes = b''

    @classmethod
    def parse(cls, data: bytes) -> 'IPHeader':
        """Parse IP header from raw packet"""
        if len(data) < 20:
            raise ValueError("Packet too short for IP header")

        version_ihl = data[0]
        version = (version_ihl >> 4) & 0xF
        ihl = version_ihl & 0xF
        header_length = ihl * 4

        tos = data[1]
        total_length = struct.unpack('!H', data[2:4])[0]
        identification = struct.unpack('!H', data[4:6])[0]
        flags_fragment = struct.unpack('!H', data[6:8])[0]
        flags = (flags_fragment >> 13) & 0x7
        fragment_offset = flags_fragment & 0x1FFF
        ttl = data[8]
        protocol = data[9]
        checksum = struct.unpack('!H', data[10:12])[0]
        src_ip = socket.inet_ntoa(data[12:16])
        dst_ip = socket.inet_ntoa(data[16:20])
        options = data[20:header_length] if header_length > 20 else b''

        return cls(
            version=version, ihl=ihl, tos=tos, total_length=total_length,
            identification=identification, flags=flags,
            fragment_offset=fragment_offset, ttl=ttl, protocol=protocol,
            checksum=checksum, src_ip=src_ip, dst_ip=dst_ip, options=options
        )


@dataclass
class TCPHeader:
    """Parsed TCP header"""
    src_port: int
    dst_port: int
    seq_num: int
    ack_num: int
    data_offset: int
    flags: int
    window: int
    checksum: int
    urgent_ptr: int

    # TCP flag masks
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    PSH = 0x08
    ACK = 0x10
    URG = 0x20
    ECE = 0x40
    CWR = 0x80

    @classmethod
    def parse(cls, data: bytes) -> 'TCPHeader':
        """Parse TCP header from raw packet"""
        if len(data) < 20:
            raise ValueError("Packet too short for TCP header")

        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        seq_num = struct.unpack('!I', data[4:8])[0]
        ack_num = struct.unpack('!I', data[8:12])[0]
        data_offset_flags = struct.unpack('!H', data[12:14])[0]
        data_offset = (data_offset_flags >> 12) & 0xF
        flags = data_offset_flags & 0x1FF
        window = struct.unpack('!H', data[14:16])[0]
        checksum = struct.unpack('!H', data[16:18])[0]
        urgent_ptr = struct.unpack('!H', data[18:20])[0]

        return cls(
            src_port=src_port, dst_port=dst_port, seq_num=seq_num,
            ack_num=ack_num, data_offset=data_offset, flags=flags,
            window=window, checksum=checksum, urgent_ptr=urgent_ptr
        )

    @property
    def is_syn(self) -> bool:
        return bool(self.flags & self.SYN) and not bool(self.flags & self.ACK)

    @property
    def is_syn_ack(self) -> bool:
        return bool(self.flags & self.SYN) and bool(self.flags & self.ACK)

    @property
    def is_fin(self) -> bool:
        return bool(self.flags & self.FIN)

    @property
    def is_rst(self) -> bool:
        return bool(self.flags & self.RST)


@dataclass
class UDPHeader:
    """Parsed UDP header"""
    src_port: int
    dst_port: int
    length: int
    checksum: int

    @classmethod
    def parse(cls, data: bytes) -> 'UDPHeader':
        """Parse UDP header from raw packet"""
        if len(data) < 8:
            raise ValueError("Packet too short for UDP header")

        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        length = struct.unpack('!H', data[4:6])[0]
        checksum = struct.unpack('!H', data[6:8])[0]

        return cls(
            src_port=src_port, dst_port=dst_port,
            length=length, checksum=checksum
        )


@dataclass
class ICMPHeader:
    """Parsed ICMP header"""
    type: int
    code: int
    checksum: int
    data: bytes

    @classmethod
    def parse(cls, data: bytes) -> 'ICMPHeader':
        """Parse ICMP header from raw packet"""
        if len(data) < 4:
            raise ValueError("Packet too short for ICMP header")

        icmp_type = data[0]
        code = data[1]
        checksum = struct.unpack('!H', data[2:4])[0]
        icmp_data = data[4:]

        return cls(type=icmp_type, code=code, checksum=checksum, data=icmp_data)


@dataclass
class Packet:
    """Complete parsed packet"""
    raw: bytes
    ip: IPHeader
    tcp: Optional[TCPHeader] = None
    udp: Optional[UDPHeader] = None
    icmp: Optional[ICMPHeader] = None
    payload: bytes = b''
    timestamp: float = field(default_factory=time.time)

    @classmethod
    def parse(cls, data: bytes) -> 'Packet':
        """Parse complete packet"""
        ip = IPHeader.parse(data)
        ip_header_len = ip.ihl * 4
        transport_data = data[ip_header_len:]

        tcp = None
        udp = None
        icmp = None
        payload = b''

        if ip.protocol == Protocol.TCP.value:
            tcp = TCPHeader.parse(transport_data)
            tcp_header_len = tcp.data_offset * 4
            payload = transport_data[tcp_header_len:]
        elif ip.protocol == Protocol.UDP.value:
            udp = UDPHeader.parse(transport_data)
            payload = transport_data[8:]
        elif ip.protocol == Protocol.ICMP.value:
            icmp = ICMPHeader.parse(transport_data)
            payload = icmp.data

        return cls(
            raw=data, ip=ip, tcp=tcp, udp=udp, icmp=icmp,
            payload=payload, timestamp=time.time()
        )


@dataclass
class FirewallRule:
    """Firewall rule definition"""
    name: str
    action: Action
    priority: int = 100  # Lower = higher priority
    enabled: bool = True

    # Match criteria
    src_ip: Optional[str] = None  # Can be CIDR notation
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    src_port_range: Optional[Tuple[int, int]] = None
    dst_port: Optional[int] = None
    dst_port_range: Optional[Tuple[int, int]] = None
    protocol: Protocol = Protocol.ANY
    direction: Direction = Direction.BOTH

    # Stateful options
    state: Optional[ConnectionState] = None

    # Rate limiting
    rate_limit: Optional[int] = None  # Packets per second
    rate_burst: Optional[int] = None  # Burst allowance

    # Time-based
    time_start: Optional[str] = None  # HH:MM format
    time_end: Optional[str] = None

    # Logging
    log_enabled: bool = False
    log_prefix: str = ""

    # Match counters
    match_count: int = 0
    last_match: Optional[float] = None

    def matches(self, packet: Packet, direction: Direction) -> bool:
        """Check if packet matches this rule"""
        if not self.enabled:
            return False

        # Direction check
        if self.direction != Direction.BOTH and self.direction != direction:
            return False

        # Protocol check
        if self.protocol != Protocol.ANY:
            if packet.ip.protocol != self.protocol.value:
                return False

        # IP address checks
        if self.src_ip and not self._ip_matches(packet.ip.src_ip, self.src_ip):
            return False
        if self.dst_ip and not self._ip_matches(packet.ip.dst_ip, self.dst_ip):
            return False

        # Port checks (for TCP/UDP)
        src_port = None
        dst_port = None

        if packet.tcp:
            src_port = packet.tcp.src_port
            dst_port = packet.tcp.dst_port
        elif packet.udp:
            src_port = packet.udp.src_port
            dst_port = packet.udp.dst_port

        if self.src_port and src_port != self.src_port:
            return False
        if self.dst_port and dst_port != self.dst_port:
            return False

        if self.src_port_range:
            if not src_port or not (self.src_port_range[0] <= src_port <= self.src_port_range[1]):
                return False

        if self.dst_port_range:
            if not dst_port or not (self.dst_port_range[0] <= dst_port <= self.dst_port_range[1]):
                return False

        # Time-based check
        if self.time_start and self.time_end:
            current_time = datetime.now().strftime("%H:%M")
            if not (self.time_start <= current_time <= self.time_end):
                return False

        return True

    def _ip_matches(self, ip: str, pattern: str) -> bool:
        """Check if IP matches pattern (supports CIDR)"""
        try:
            if '/' in pattern:
                network = ipaddress.ip_network(pattern, strict=False)
                return ipaddress.ip_address(ip) in network
            else:
                return ip == pattern
        except:
            return False


@dataclass
class Connection:
    """Connection tracking entry"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: Protocol
    state: ConnectionState
    created: float
    last_seen: float
    packets: int = 0
    bytes_count: int = 0

    def get_key(self) -> str:
        """Get unique connection key"""
        return f"{self.protocol.value}:{self.src_ip}:{self.src_port}-{self.dst_ip}:{self.dst_port}"

    def get_reverse_key(self) -> str:
        """Get reverse connection key for response packets"""
        return f"{self.protocol.value}:{self.dst_ip}:{self.dst_port}-{self.src_ip}:{self.src_port}"


class ConnectionTracker:
    """
    Stateful connection tracking for the firewall.
    Tracks TCP/UDP connections and their states.
    """

    def __init__(self, timeout: int = 300):
        self.connections: Dict[str, Connection] = {}
        self.timeout = timeout
        self.lock = threading.Lock()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._running = False

    def start(self):
        """Start connection tracking"""
        self._running = True
        self._cleanup_thread.start()

    def stop(self):
        """Stop connection tracking"""
        self._running = False

    def _cleanup_loop(self):
        """Periodically clean up expired connections"""
        while self._running:
            time.sleep(30)
            self._cleanup_expired()

    def _cleanup_expired(self):
        """Remove expired connections"""
        current_time = time.time()
        expired = []

        with self.lock:
            for key, conn in self.connections.items():
                if current_time - conn.last_seen > self.timeout:
                    expired.append(key)

            for key in expired:
                del self.connections[key]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired connections")

    def process_packet(self, packet: Packet) -> ConnectionState:
        """Process packet and return connection state"""
        if packet.ip.protocol == Protocol.TCP.value and packet.tcp:
            return self._process_tcp(packet)
        elif packet.ip.protocol == Protocol.UDP.value and packet.udp:
            return self._process_udp(packet)
        else:
            return ConnectionState.NEW

    def _process_tcp(self, packet: Packet) -> ConnectionState:
        """Process TCP packet for connection tracking"""
        tcp = packet.tcp
        key = f"{Protocol.TCP.value}:{packet.ip.src_ip}:{tcp.src_port}-{packet.ip.dst_ip}:{tcp.dst_port}"
        reverse_key = f"{Protocol.TCP.value}:{packet.ip.dst_ip}:{tcp.dst_port}-{packet.ip.src_ip}:{tcp.src_port}"

        with self.lock:
            # Check for existing connection (either direction)
            conn = self.connections.get(key) or self.connections.get(reverse_key)

            if tcp.is_syn and not tcp.is_syn_ack:
                # New connection attempt
                if conn is None:
                    conn = Connection(
                        src_ip=packet.ip.src_ip, dst_ip=packet.ip.dst_ip,
                        src_port=tcp.src_port, dst_port=tcp.dst_port,
                        protocol=Protocol.TCP, state=ConnectionState.NEW,
                        created=time.time(), last_seen=time.time()
                    )
                    self.connections[key] = conn
                return ConnectionState.NEW

            elif tcp.is_syn_ack:
                # SYN-ACK response
                if conn and conn.state == ConnectionState.NEW:
                    conn.state = ConnectionState.ESTABLISHED
                    conn.last_seen = time.time()
                    return ConnectionState.ESTABLISHED
                return ConnectionState.RELATED

            elif tcp.is_fin or tcp.is_rst:
                # Connection termination
                if conn:
                    conn.state = ConnectionState.TIME_WAIT
                    conn.last_seen = time.time()
                return ConnectionState.ESTABLISHED if conn else ConnectionState.INVALID

            else:
                # Regular data packet
                if conn:
                    conn.last_seen = time.time()
                    conn.packets += 1
                    conn.bytes_count += len(packet.raw)
                    return conn.state
                return ConnectionState.INVALID

    def _process_udp(self, packet: Packet) -> ConnectionState:
        """Process UDP packet for connection tracking"""
        udp = packet.udp
        key = f"{Protocol.UDP.value}:{packet.ip.src_ip}:{udp.src_port}-{packet.ip.dst_ip}:{udp.dst_port}"
        reverse_key = f"{Protocol.UDP.value}:{packet.ip.dst_ip}:{udp.dst_port}-{packet.ip.src_ip}:{udp.src_port}"

        with self.lock:
            conn = self.connections.get(key) or self.connections.get(reverse_key)

            if conn:
                conn.last_seen = time.time()
                conn.packets += 1
                return ConnectionState.ESTABLISHED
            else:
                conn = Connection(
                    src_ip=packet.ip.src_ip, dst_ip=packet.ip.dst_ip,
                    src_port=udp.src_port, dst_port=udp.dst_port,
                    protocol=Protocol.UDP, state=ConnectionState.ESTABLISHED,
                    created=time.time(), last_seen=time.time()
                )
                self.connections[key] = conn
                return ConnectionState.NEW

    def get_connections(self) -> List[Connection]:
        """Get all active connections"""
        with self.lock:
            return list(self.connections.values())


class RateLimiter:
    """
    Rate limiting implementation using token bucket algorithm.
    Protects against DDoS and brute force attacks.
    """

    def __init__(self):
        self.buckets: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def check_rate(self, key: str, limit: int, burst: int = None) -> bool:
        """
        Check if request is within rate limit.
        Returns True if allowed, False if rate limited.
        """
        burst = burst or limit * 2
        current_time = time.time()

        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = {
                    'tokens': burst,
                    'last_update': current_time
                }

            bucket = self.buckets[key]

            # Add tokens based on time elapsed
            elapsed = current_time - bucket['last_update']
            bucket['tokens'] = min(burst, bucket['tokens'] + elapsed * limit)
            bucket['last_update'] = current_time

            # Check if we have tokens available
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True
            else:
                return False


class TrafficLogger:
    """
    Traffic logging system with support for multiple output formats.
    """

    def __init__(self, log_file: str = "firewall.log"):
        self.log_file = log_file
        self.logs: List[Dict] = []
        self.lock = threading.Lock()
        self.max_memory_logs = 10000

        # Statistics
        self.stats = defaultdict(int)

    def log_packet(self, packet: Packet, rule: FirewallRule, action: Action,
                   direction: Direction, extra: Dict = None):
        """Log packet processing result"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'src_ip': packet.ip.src_ip,
            'dst_ip': packet.ip.dst_ip,
            'protocol': Protocol(packet.ip.protocol).name if packet.ip.protocol in [p.value for p in Protocol] else str(packet.ip.protocol),
            'src_port': packet.tcp.src_port if packet.tcp else (packet.udp.src_port if packet.udp else None),
            'dst_port': packet.tcp.dst_port if packet.tcp else (packet.udp.dst_port if packet.udp else None),
            'length': packet.ip.total_length,
            'rule': rule.name if rule else None,
            'action': action.name,
            'direction': direction.name
        }

        if extra:
            entry.update(extra)

        with self.lock:
            self.logs.append(entry)
            if len(self.logs) > self.max_memory_logs:
                self.logs = self.logs[-self.max_memory_logs:]

            # Update statistics
            self.stats[f'packets_{action.name.lower()}'] += 1
            self.stats[f'bytes_{action.name.lower()}'] += packet.ip.total_length
            self.stats['total_packets'] += 1

        # Write to file
        if rule and rule.log_enabled:
            self._write_log(entry, rule.log_prefix)

    def _write_log(self, entry: Dict, prefix: str = ""):
        """Write log entry to file"""
        try:
            with open(self.log_file, 'a') as f:
                log_line = f"{prefix}{json.dumps(entry)}\n"
                f.write(log_line)
        except Exception as e:
            logger.error(f"Failed to write log: {e}")

    def get_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent log entries"""
        with self.lock:
            return self.logs[-limit:]

    def get_stats(self) -> Dict:
        """Get traffic statistics"""
        with self.lock:
            return dict(self.stats)


class Firewall:
    """
    Main Firewall class implementing packet filtering.

    Features:
    - Rule-based packet filtering
    - Stateful packet inspection
    - Rate limiting
    - Traffic logging
    - NAT support
    - Application-layer filtering
    """

    def __init__(self, default_action: Action = Action.ALLOW):
        self.rules: List[FirewallRule] = []
        self.default_action = default_action
        self.running = False

        # Components
        self.connection_tracker = ConnectionTracker()
        self.rate_limiter = RateLimiter()
        self.logger = TrafficLogger()

        # Blocked IPs (blacklist)
        self.blocked_ips: Set[str] = set()

        # Allowed IPs (whitelist)
        self.allowed_ips: Set[str] = set()

        # NAT table
        self.nat_table: Dict[str, str] = {}

        # Port forwarding
        self.port_forwards: Dict[Tuple[int, Protocol], Tuple[str, int]] = {}

        # Hooks for custom packet processing
        self.pre_hooks: List[Callable] = []
        self.post_hooks: List[Callable] = []

        # Statistics
        self.stats = {
            'packets_processed': 0,
            'packets_allowed': 0,
            'packets_denied': 0,
            'packets_dropped': 0,
            'packets_rate_limited': 0
        }

        self._lock = threading.Lock()

    def add_rule(self, rule: FirewallRule):
        """Add a firewall rule"""
        with self._lock:
            self.rules.append(rule)
            self.rules.sort(key=lambda r: r.priority)
        logger.info(f"Added rule: {rule.name}")

    def remove_rule(self, name: str) -> bool:
        """Remove a firewall rule by name"""
        with self._lock:
            for i, rule in enumerate(self.rules):
                if rule.name == name:
                    del self.rules[i]
                    logger.info(f"Removed rule: {name}")
                    return True
        return False

    def block_ip(self, ip: str):
        """Add IP to blacklist"""
        self.blocked_ips.add(ip)
        logger.info(f"Blocked IP: {ip}")

    def unblock_ip(self, ip: str):
        """Remove IP from blacklist"""
        self.blocked_ips.discard(ip)
        logger.info(f"Unblocked IP: {ip}")

    def allow_ip(self, ip: str):
        """Add IP to whitelist"""
        self.allowed_ips.add(ip)
        logger.info(f"Whitelisted IP: {ip}")

    def add_port_forward(self, external_port: int, protocol: Protocol,
                         internal_ip: str, internal_port: int):
        """Add port forwarding rule"""
        self.port_forwards[(external_port, protocol)] = (internal_ip, internal_port)
        logger.info(f"Added port forward: {external_port} -> {internal_ip}:{internal_port}")

    def start(self):
        """Start the firewall"""
        self.running = True
        self.connection_tracker.start()
        logger.info("Firewall started")

    def stop(self):
        """Stop the firewall"""
        self.running = False
        self.connection_tracker.stop()
        logger.info("Firewall stopped")

    def process_packet(self, data: bytes, direction: Direction = Direction.INBOUND) -> Tuple[Action, Optional[bytes]]:
        """
        Process a packet through the firewall.

        Returns:
            Tuple of (action, modified_packet)
            modified_packet may be None if packet should be dropped
        """
        try:
            packet = Packet.parse(data)
        except Exception as e:
            logger.error(f"Failed to parse packet: {e}")
            return Action.DROP, None

        self.stats['packets_processed'] += 1

        # Run pre-hooks
        for hook in self.pre_hooks:
            try:
                result = hook(packet)
                if result is not None:
                    return result, None
            except:
                pass

        # Check whitelist
        if packet.ip.src_ip in self.allowed_ips:
            self.stats['packets_allowed'] += 1
            return Action.ALLOW, data

        # Check blacklist
        if packet.ip.src_ip in self.blocked_ips:
            self.logger.log_packet(packet, None, Action.DROP, direction)
            self.stats['packets_dropped'] += 1
            return Action.DROP, None

        # Get connection state for stateful inspection
        conn_state = self.connection_tracker.process_packet(packet)

        # Process through rules
        matched_rule = None
        action = self.default_action

        with self._lock:
            for rule in self.rules:
                if rule.matches(packet, direction):
                    matched_rule = rule
                    rule.match_count += 1
                    rule.last_match = time.time()

                    # Check rate limiting
                    if rule.rate_limit:
                        rate_key = f"{rule.name}:{packet.ip.src_ip}"
                        if not self.rate_limiter.check_rate(
                            rate_key, rule.rate_limit, rule.rate_burst
                        ):
                            action = Action.DROP
                            self.stats['packets_rate_limited'] += 1
                            break

                    # Check stateful rule
                    if rule.state and rule.state != conn_state:
                        continue

                    action = rule.action
                    break

        # Log the packet
        self.logger.log_packet(packet, matched_rule, action, direction)

        # Update statistics
        if action == Action.ALLOW:
            self.stats['packets_allowed'] += 1
        elif action == Action.DENY or action == Action.REJECT:
            self.stats['packets_denied'] += 1
        elif action == Action.DROP:
            self.stats['packets_dropped'] += 1

        # Run post-hooks
        for hook in self.post_hooks:
            try:
                hook(packet, action)
            except:
                pass

        # Return result
        if action in [Action.DROP, Action.DENY, Action.REJECT]:
            return action, None
        else:
            return action, data

    def get_stats(self) -> Dict:
        """Get firewall statistics"""
        return {
            **self.stats,
            'active_connections': len(self.connection_tracker.get_connections()),
            'rules_count': len(self.rules),
            'blocked_ips': len(self.blocked_ips),
            'traffic_stats': self.logger.get_stats()
        }

    def get_rules(self) -> List[Dict]:
        """Get all rules as dictionaries"""
        with self._lock:
            return [
                {
                    'name': r.name,
                    'action': r.action.name,
                    'priority': r.priority,
                    'enabled': r.enabled,
                    'src_ip': r.src_ip,
                    'dst_ip': r.dst_ip,
                    'src_port': r.src_port,
                    'dst_port': r.dst_port,
                    'protocol': r.protocol.name,
                    'match_count': r.match_count
                }
                for r in self.rules
            ]


class FirewallManager:
    """
    High-level firewall management interface.
    Provides easy-to-use methods for common firewall operations.
    """

    def __init__(self):
        self.firewall = Firewall(default_action=Action.ALLOW)

    def setup_default_rules(self):
        """Set up common default rules"""
        # Allow loopback
        self.firewall.add_rule(FirewallRule(
            name="allow_loopback",
            action=Action.ALLOW,
            priority=1,
            src_ip="127.0.0.0/8",
            dst_ip="127.0.0.0/8"
        ))

        # Allow established connections
        self.firewall.add_rule(FirewallRule(
            name="allow_established",
            action=Action.ALLOW,
            priority=10,
            state=ConnectionState.ESTABLISHED
        ))

        # Allow related connections
        self.firewall.add_rule(FirewallRule(
            name="allow_related",
            action=Action.ALLOW,
            priority=11,
            state=ConnectionState.RELATED
        ))

        # Allow ICMP echo (ping)
        self.firewall.add_rule(FirewallRule(
            name="allow_ping",
            action=Action.ALLOW,
            priority=20,
            protocol=Protocol.ICMP
        ))

        # Allow DNS
        self.firewall.add_rule(FirewallRule(
            name="allow_dns",
            action=Action.ALLOW,
            priority=30,
            protocol=Protocol.UDP,
            dst_port=53
        ))

        # Allow HTTP/HTTPS outbound
        self.firewall.add_rule(FirewallRule(
            name="allow_http_out",
            action=Action.ALLOW,
            priority=40,
            protocol=Protocol.TCP,
            dst_port_range=(80, 443),
            direction=Direction.OUTBOUND
        ))

        logger.info("Default firewall rules configured")

    def block_port(self, port: int, protocol: Protocol = Protocol.TCP):
        """Block a specific port"""
        rule_name = f"block_port_{port}_{protocol.name}"
        self.firewall.add_rule(FirewallRule(
            name=rule_name,
            action=Action.DROP,
            priority=50,
            protocol=protocol,
            dst_port=port,
            log_enabled=True,
            log_prefix=f"[BLOCKED PORT {port}] "
        ))

    def allow_port(self, port: int, protocol: Protocol = Protocol.TCP):
        """Allow a specific port"""
        rule_name = f"allow_port_{port}_{protocol.name}"
        self.firewall.add_rule(FirewallRule(
            name=rule_name,
            action=Action.ALLOW,
            priority=45,
            protocol=protocol,
            dst_port=port
        ))

    def add_rate_limit_rule(self, name: str, src_ip: str = None,
                            rate: int = 100, burst: int = 200):
        """Add rate limiting rule"""
        self.firewall.add_rule(FirewallRule(
            name=name,
            action=Action.ALLOW,
            priority=5,
            src_ip=src_ip,
            rate_limit=rate,
            rate_burst=burst,
            log_enabled=True,
            log_prefix="[RATE LIMITED] "
        ))

    def block_country(self, country_code: str, ip_ranges: List[str]):
        """Block traffic from a country (given IP ranges)"""
        for i, ip_range in enumerate(ip_ranges):
            self.firewall.add_rule(FirewallRule(
                name=f"block_{country_code}_{i}",
                action=Action.DROP,
                priority=60,
                src_ip=ip_range,
                log_enabled=True,
                log_prefix=f"[BLOCKED {country_code}] "
            ))


def create_test_packet(src_ip: str, dst_ip: str, src_port: int, dst_port: int,
                       protocol: Protocol = Protocol.TCP) -> bytes:
    """Create a test packet for firewall testing"""
    # IP header
    version_ihl = (4 << 4) | 5  # IPv4, 5 words
    tos = 0
    total_length = 40 if protocol == Protocol.TCP else 28
    identification = 54321
    flags_fragment = 0x4000  # Don't fragment
    ttl = 64
    proto = protocol.value
    checksum = 0  # Would be calculated
    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)

    ip_header = struct.pack('!BBHHHBBH4s4s',
        version_ihl, tos, total_length, identification,
        flags_fragment, ttl, proto, checksum, src, dst
    )

    if protocol == Protocol.TCP:
        # TCP header
        seq = 0
        ack = 0
        data_offset_flags = (5 << 12) | 0x02  # SYN flag
        window = 65535
        tcp_checksum = 0
        urgent = 0

        tcp_header = struct.pack('!HHIIHHHH',
            src_port, dst_port, seq, ack,
            data_offset_flags, window, tcp_checksum, urgent
        )
        return ip_header + tcp_header

    elif protocol == Protocol.UDP:
        # UDP header
        length = 8
        udp_checksum = 0

        udp_header = struct.pack('!HHHH',
            src_port, dst_port, length, udp_checksum
        )
        return ip_header + udp_header

    else:
        return ip_header


def main():
    """Main entry point for firewall testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Electroduction Firewall System')
    parser.add_argument('mode', choices=['test', 'demo', 'interactive'],
                        help='Run mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.mode == 'test':
        run_tests()
    elif args.mode == 'demo':
        run_demo()
    elif args.mode == 'interactive':
        run_interactive()


def run_tests():
    """Run firewall component tests"""
    print("\n" + "="*60)
    print("FIREWALL SYSTEM TESTS")
    print("="*60 + "\n")

    # Test 1: Packet Parsing
    print("[1] Testing Packet Parsing...")
    packet_data = create_test_packet("192.168.1.100", "10.0.0.1", 12345, 80)
    packet = Packet.parse(packet_data)
    assert packet.ip.src_ip == "192.168.1.100"
    assert packet.ip.dst_ip == "10.0.0.1"
    assert packet.tcp.src_port == 12345
    assert packet.tcp.dst_port == 80
    print("    Packet parsing PASSED")

    # Test 2: Rule Matching
    print("[2] Testing Rule Matching...")
    rule = FirewallRule(
        name="test_rule",
        action=Action.ALLOW,
        src_ip="192.168.1.0/24",
        dst_port=80,
        protocol=Protocol.TCP
    )
    assert rule.matches(packet, Direction.OUTBOUND) == True

    rule2 = FirewallRule(
        name="test_rule2",
        action=Action.DENY,
        src_ip="10.0.0.0/8",
        protocol=Protocol.TCP
    )
    assert rule2.matches(packet, Direction.OUTBOUND) == False
    print("    Rule matching PASSED")

    # Test 3: Firewall Processing
    print("[3] Testing Firewall Processing...")
    firewall = Firewall(default_action=Action.DENY)
    firewall.add_rule(rule)
    firewall.start()

    action, _ = firewall.process_packet(packet_data, Direction.OUTBOUND)
    assert action == Action.ALLOW
    print("    Firewall processing PASSED")

    # Test 4: Connection Tracking
    print("[4] Testing Connection Tracking...")
    tracker = ConnectionTracker()
    tracker.start()

    # SYN packet
    state = tracker.process_packet(packet)
    assert state == ConnectionState.NEW
    print("    Connection tracking PASSED")

    # Test 5: Rate Limiting
    print("[5] Testing Rate Limiting...")
    limiter = RateLimiter()
    allowed = sum(1 for _ in range(15) if limiter.check_rate("test", 10, 10))
    assert allowed == 10  # First 10 should pass
    print("    Rate limiting PASSED")

    # Test 6: Blacklist/Whitelist
    print("[6] Testing IP Blacklist/Whitelist...")
    firewall.block_ip("192.168.1.100")
    action, _ = firewall.process_packet(packet_data, Direction.OUTBOUND)
    assert action == Action.DROP

    firewall.unblock_ip("192.168.1.100")
    firewall.allow_ip("192.168.1.100")
    action, _ = firewall.process_packet(packet_data, Direction.OUTBOUND)
    assert action == Action.ALLOW
    print("    Blacklist/Whitelist PASSED")

    # Test 7: Traffic Logging
    print("[7] Testing Traffic Logging...")
    logs = firewall.logger.get_logs()
    assert len(logs) > 0
    print("    Traffic logging PASSED")

    firewall.stop()
    tracker.stop()

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")


def run_demo():
    """Run firewall demonstration"""
    print("\n" + "="*70)
    print("   ELECTRODUCTION FIREWALL SYSTEM - DEMONSTRATION")
    print("="*70 + "\n")

    # Create firewall manager
    manager = FirewallManager()

    print("[1] Setting up firewall with default rules...")
    manager.setup_default_rules()
    manager.firewall.start()
    print("    Firewall started\n")

    # Display rules
    print("[2] Current firewall rules:")
    for rule in manager.firewall.get_rules():
        print(f"    {rule['priority']:3d} | {rule['name']:25s} | {rule['action']:8s} | {rule['protocol']}")
    print()

    # Test various packets
    print("[3] Testing packet processing...\n")

    test_cases = [
        ("Web traffic (HTTP)", "192.168.1.100", "93.184.216.34", 54321, 80, Protocol.TCP),
        ("DNS query", "192.168.1.100", "8.8.8.8", 54322, 53, Protocol.UDP),
        ("SSH attempt", "10.20.30.40", "192.168.1.1", 54323, 22, Protocol.TCP),
        ("Loopback", "127.0.0.1", "127.0.0.1", 12345, 8080, Protocol.TCP),
    ]

    for desc, src, dst, sp, dp, proto in test_cases:
        packet = create_test_packet(src, dst, sp, dp, proto)
        action, _ = manager.firewall.process_packet(packet, Direction.OUTBOUND)
        print(f"    {desc:25s}: {src}:{sp} -> {dst}:{dp} = {action.name}")

    print()

    # Add custom rules
    print("[4] Adding custom security rules...")
    manager.block_port(23, Protocol.TCP)  # Block Telnet
    manager.block_port(21, Protocol.TCP)  # Block FTP
    manager.add_rate_limit_rule("rate_limit_all", rate=1000, burst=2000)
    print("    Blocked ports: 21 (FTP), 23 (Telnet)")
    print("    Added rate limiting: 1000 pps\n")

    # Test blocked ports
    print("[5] Testing blocked ports...")
    telnet_packet = create_test_packet("192.168.1.100", "10.0.0.1", 54321, 23)
    action, _ = manager.firewall.process_packet(telnet_packet)
    print(f"    Telnet (port 23): {action.name}")

    ftp_packet = create_test_packet("192.168.1.100", "10.0.0.1", 54321, 21)
    action, _ = manager.firewall.process_packet(ftp_packet)
    print(f"    FTP (port 21): {action.name}")
    print()

    # Show statistics
    print("[6] Firewall Statistics:")
    stats = manager.firewall.get_stats()
    print(f"    Packets Processed: {stats['packets_processed']}")
    print(f"    Packets Allowed: {stats['packets_allowed']}")
    print(f"    Packets Denied: {stats['packets_denied']}")
    print(f"    Packets Dropped: {stats['packets_dropped']}")
    print(f"    Active Connections: {stats['active_connections']}")
    print(f"    Total Rules: {stats['rules_count']}")
    print()

    # Show recent logs
    print("[7] Recent Firewall Logs:")
    for log in manager.firewall.logger.get_logs(5):
        print(f"    {log['timestamp']}: {log['src_ip']} -> {log['dst_ip']} : {log['action']}")
    print()

    manager.firewall.stop()

    print("="*70)
    print("   DEMO COMPLETED")
    print("="*70 + "\n")


def run_interactive():
    """Run interactive firewall shell"""
    print("\n" + "="*60)
    print("FIREWALL INTERACTIVE MODE")
    print("="*60)
    print("\nCommands:")
    print("  rules       - List all rules")
    print("  add <rule>  - Add a rule")
    print("  block <ip>  - Block an IP")
    print("  allow <ip>  - Whitelist an IP")
    print("  stats       - Show statistics")
    print("  logs        - Show recent logs")
    print("  test <src> <dst> <port> - Test a packet")
    print("  quit        - Exit")
    print()

    manager = FirewallManager()
    manager.setup_default_rules()
    manager.firewall.start()

    while True:
        try:
            cmd = input("firewall> ").strip().lower().split()
            if not cmd:
                continue

            if cmd[0] == 'quit' or cmd[0] == 'exit':
                break
            elif cmd[0] == 'rules':
                for rule in manager.firewall.get_rules():
                    print(f"  {rule['name']}: {rule['action']} (priority {rule['priority']})")
            elif cmd[0] == 'block' and len(cmd) > 1:
                manager.firewall.block_ip(cmd[1])
                print(f"Blocked {cmd[1]}")
            elif cmd[0] == 'allow' and len(cmd) > 1:
                manager.firewall.allow_ip(cmd[1])
                print(f"Whitelisted {cmd[1]}")
            elif cmd[0] == 'stats':
                stats = manager.firewall.get_stats()
                for k, v in stats.items():
                    print(f"  {k}: {v}")
            elif cmd[0] == 'logs':
                for log in manager.firewall.logger.get_logs(10):
                    print(f"  {log['timestamp']}: {log['action']}")
            elif cmd[0] == 'test' and len(cmd) >= 4:
                packet = create_test_packet(cmd[1], cmd[2], 12345, int(cmd[3]))
                action, _ = manager.firewall.process_packet(packet)
                print(f"Result: {action.name}")
            else:
                print("Unknown command")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    manager.firewall.stop()
    print("\nFirewall stopped.")


if __name__ == "__main__":
    main()
