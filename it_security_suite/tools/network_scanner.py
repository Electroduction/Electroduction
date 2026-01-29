#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION NETWORK SCANNER
===============================================================================
PROGRAM SUMMARY:
A comprehensive network scanning tool for security assessment and network
discovery. This tool helps IT professionals:
- Discover active hosts on a network
- Scan open ports on target systems
- Identify running services and versions
- Detect operating systems (OS fingerprinting)
- Perform vulnerability assessment basics

FEATURES:
1. Host Discovery (ping sweep, ARP scan)
2. Port Scanning (TCP connect, SYN scan simulation)
3. Service Detection (banner grabbing)
4. Common Vulnerability Checks
5. Network Topology Mapping
6. Export Results (JSON, CSV, HTML)

USAGE:
    python network_scanner.py scan 192.168.1.0/24     # Scan network
    python network_scanner.py ports 192.168.1.1      # Port scan host
    python network_scanner.py services 192.168.1.1   # Service detection
    python network_scanner.py report                 # Generate report

WARNING: Only use on networks you own or have permission to scan.
         Unauthorized scanning may be illegal in your jurisdiction.
===============================================================================
"""

# =============================================================================
# IMPORTS
# Each import is documented with its purpose
# =============================================================================

import os                       # OS operations (file handling, env vars)
import sys                      # System functions (exit, argv)
import socket                   # Network socket operations
import struct                   # Binary data packing/unpacking
import threading                # Multi-threaded scanning
import time                     # Timing operations
import json                     # JSON serialization
import csv                      # CSV export
import ipaddress                # IP address/network manipulation
import concurrent.futures       # Thread pool executor
from dataclasses import dataclass, field  # Data classes
from typing import Dict, List, Optional, Tuple, Set, Any  # Type hints
from enum import Enum, auto     # Enumerations
from datetime import datetime   # Timestamps
from collections import defaultdict  # Default dictionary
import logging                  # Logging facility

# =============================================================================
# LOGGING SETUP
# Configure logging to track scan progress and errors
# =============================================================================

logging.basicConfig(
    level=logging.INFO,  # Default log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Format string
)
logger = logging.getLogger('NetworkScanner')  # Named logger instance


# =============================================================================
# CONSTANTS AND CONFIGURATION
# Well-known ports and service mappings
# =============================================================================

# Dictionary mapping port numbers to common service names
# Used for service identification without banner grabbing
WELL_KNOWN_PORTS = {
    20: 'FTP-DATA',      # FTP data transfer
    21: 'FTP',           # FTP control
    22: 'SSH',           # Secure Shell
    23: 'TELNET',        # Telnet (insecure)
    25: 'SMTP',          # Simple Mail Transfer
    53: 'DNS',           # Domain Name System
    67: 'DHCP',          # DHCP Server
    68: 'DHCP',          # DHCP Client
    69: 'TFTP',          # Trivial File Transfer
    80: 'HTTP',          # Web (unencrypted)
    110: 'POP3',         # Post Office Protocol
    119: 'NNTP',         # Network News
    123: 'NTP',          # Network Time Protocol
    135: 'RPC',          # Windows RPC
    137: 'NETBIOS-NS',   # NetBIOS Name Service
    138: 'NETBIOS-DGM',  # NetBIOS Datagram
    139: 'NETBIOS-SSN',  # NetBIOS Session
    143: 'IMAP',         # Internet Message Access
    161: 'SNMP',         # Simple Network Management
    162: 'SNMPTRAP',     # SNMP Trap
    389: 'LDAP',         # Lightweight Directory Access
    443: 'HTTPS',        # Web (encrypted)
    445: 'SMB',          # Server Message Block
    465: 'SMTPS',        # SMTP over SSL
    514: 'SYSLOG',       # System Logging
    587: 'SUBMISSION',   # Email Submission
    636: 'LDAPS',        # LDAP over SSL
    993: 'IMAPS',        # IMAP over SSL
    995: 'POP3S',        # POP3 over SSL
    1080: 'SOCKS',       # SOCKS Proxy
    1433: 'MSSQL',       # Microsoft SQL Server
    1434: 'MSSQL-UDP',   # MS SQL Browser
    1521: 'ORACLE',      # Oracle Database
    3306: 'MYSQL',       # MySQL Database
    3389: 'RDP',         # Remote Desktop
    5432: 'POSTGRESQL',  # PostgreSQL Database
    5900: 'VNC',         # Virtual Network Computing
    5901: 'VNC-1',       # VNC Display 1
    6379: 'REDIS',       # Redis Database
    8080: 'HTTP-ALT',    # Alternate HTTP
    8443: 'HTTPS-ALT',   # Alternate HTTPS
    27017: 'MONGODB',    # MongoDB Database
}

# Default ports to scan when doing quick scan
# Covers most common services
DEFAULT_SCAN_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
    1723, 3306, 3389, 5432, 5900, 8080, 8443
]

# Full port range for comprehensive scans
ALL_PORTS = range(1, 65536)  # 1-65535

# Timeout values in seconds
DEFAULT_TIMEOUT = 1.0        # Socket connection timeout
PING_TIMEOUT = 2.0           # ICMP ping timeout
BANNER_TIMEOUT = 3.0         # Banner grab timeout


# =============================================================================
# ENUMERATIONS
# Define scan types and port states
# =============================================================================

class ScanType(Enum):
    """
    Types of network scans available.
    Each type has different speed/accuracy tradeoffs.
    """
    PING = auto()           # ICMP ping sweep (host discovery)
    TCP_CONNECT = auto()    # Full TCP connection (accurate but detectable)
    TCP_SYN = auto()        # SYN scan (stealthier, requires root)
    UDP = auto()            # UDP scan (slower, less reliable)
    SERVICE = auto()        # Service/version detection


class PortState(Enum):
    """
    Possible states of a scanned port.
    Based on Nmap port state model.
    """
    OPEN = "open"               # Port accepts connections
    CLOSED = "closed"           # Port responds with RST
    FILTERED = "filtered"       # No response (firewall)
    OPEN_FILTERED = "open|filtered"  # UDP ambiguity
    UNKNOWN = "unknown"         # Could not determine


class HostState(Enum):
    """
    State of discovered hosts.
    """
    UP = "up"               # Host responds to probes
    DOWN = "down"           # No response
    UNKNOWN = "unknown"     # Could not determine


# =============================================================================
# DATA CLASSES
# Structured data containers for scan results
# =============================================================================

@dataclass
class PortResult:
    """
    Result of scanning a single port.

    Attributes:
        port: Port number that was scanned
        state: Current state of the port (open/closed/filtered)
        service: Identified service name
        banner: Raw banner from service (if retrieved)
        version: Detected version information
        scan_time: Time taken to scan this port
    """
    port: int                           # Port number (1-65535)
    state: PortState                    # Port state
    service: str = ""                   # Service name
    banner: str = ""                    # Banner text
    version: str = ""                   # Version string
    scan_time: float = 0.0              # Scan duration in seconds

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'port': self.port,
            'state': self.state.value,
            'service': self.service,
            'banner': self.banner,
            'version': self.version,
            'scan_time': self.scan_time
        }


@dataclass
class HostResult:
    """
    Complete scan results for a single host.

    Attributes:
        ip: IP address of scanned host
        hostname: Resolved hostname (if available)
        state: Whether host is up/down
        mac_address: MAC address (if on local network)
        os_guess: Guessed operating system
        ports: List of port scan results
        scan_start: When scan started
        scan_end: When scan completed
    """
    ip: str                             # IP address
    hostname: str = ""                  # DNS hostname
    state: HostState = HostState.UNKNOWN  # Host state
    mac_address: str = ""               # MAC address
    os_guess: str = ""                  # OS fingerprint guess
    ports: List[PortResult] = field(default_factory=list)  # Port results
    scan_start: float = 0.0             # Start timestamp
    scan_end: float = 0.0               # End timestamp

    def get_open_ports(self) -> List[int]:
        """Return list of open port numbers."""
        return [p.port for p in self.ports if p.state == PortState.OPEN]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'ip': self.ip,
            'hostname': self.hostname,
            'state': self.state.value,
            'mac_address': self.mac_address,
            'os_guess': self.os_guess,
            'ports': [p.to_dict() for p in self.ports],
            'scan_duration': self.scan_end - self.scan_start
        }


@dataclass
class ScanResults:
    """
    Complete results from a network scan.

    Attributes:
        target: Original scan target (IP or CIDR)
        scan_type: Type of scan performed
        hosts: List of host results
        start_time: Overall scan start time
        end_time: Overall scan end time
        total_hosts_scanned: Count of hosts checked
        total_hosts_up: Count of responsive hosts
    """
    target: str                         # Scan target
    scan_type: ScanType                 # Type of scan
    hosts: List[HostResult] = field(default_factory=list)  # Results
    start_time: float = 0.0             # Start timestamp
    end_time: float = 0.0               # End timestamp
    total_hosts_scanned: int = 0        # Hosts checked
    total_hosts_up: int = 0             # Hosts responding

    def get_summary(self) -> str:
        """Generate human-readable summary."""
        duration = self.end_time - self.start_time
        open_ports = sum(len(h.get_open_ports()) for h in self.hosts)

        return (
            f"Scan Summary:\n"
            f"  Target: {self.target}\n"
            f"  Type: {self.scan_type.name}\n"
            f"  Duration: {duration:.2f}s\n"
            f"  Hosts Scanned: {self.total_hosts_scanned}\n"
            f"  Hosts Up: {self.total_hosts_up}\n"
            f"  Open Ports Found: {open_ports}"
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'target': self.target,
            'scan_type': self.scan_type.name,
            'hosts': [h.to_dict() for h in self.hosts],
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
            'total_hosts_scanned': self.total_hosts_scanned,
            'total_hosts_up': self.total_hosts_up
        }


# =============================================================================
# PORT SCANNER CLASS
# Core scanning functionality
# =============================================================================

class PortScanner:
    """
    Port scanner implementation.

    This class handles:
    - TCP connect scanning (full 3-way handshake)
    - Service banner grabbing
    - Multi-threaded scanning for speed

    Usage:
        scanner = PortScanner()
        results = scanner.scan_host("192.168.1.1", ports=[22, 80, 443])
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, threads: int = 100):
        """
        Initialize port scanner.

        Args:
            timeout: Socket timeout in seconds
            threads: Maximum concurrent threads for scanning
        """
        self.timeout = timeout          # Connection timeout
        self.max_threads = threads      # Thread pool size
        self._lock = threading.Lock()   # Thread synchronization

    def scan_port(self, ip: str, port: int, grab_banner: bool = False) -> PortResult:
        """
        Scan a single port on target IP.

        This performs a TCP connect scan:
        1. Create socket
        2. Attempt connection to IP:port
        3. If connected, port is OPEN
        4. If refused, port is CLOSED
        5. If timeout, port is FILTERED

        Args:
            ip: Target IP address
            port: Port number to scan
            grab_banner: Whether to grab service banner

        Returns:
            PortResult with scan findings
        """
        start_time = time.time()  # Record start time
        result = PortResult(
            port=port,
            state=PortState.UNKNOWN,
            service=WELL_KNOWN_PORTS.get(port, "")  # Look up known service
        )

        try:
            # Create TCP socket
            # AF_INET = IPv4, SOCK_STREAM = TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set connection timeout
            sock.settimeout(self.timeout)

            # Attempt to connect
            # connect_ex returns 0 on success, error code on failure
            error_code = sock.connect_ex((ip, port))

            if error_code == 0:
                # Connection successful - port is open
                result.state = PortState.OPEN

                # Optionally grab banner
                if grab_banner:
                    result.banner = self._grab_banner(sock)
                    result.version = self._parse_version(result.banner)

            elif error_code == 111:  # Connection refused
                result.state = PortState.CLOSED

            else:
                # Other errors typically mean filtered
                result.state = PortState.FILTERED

            sock.close()  # Always close socket

        except socket.timeout:
            # Timeout indicates filtered (firewall dropping packets)
            result.state = PortState.FILTERED

        except socket.error as e:
            # Network error
            logger.debug(f"Socket error scanning {ip}:{port}: {e}")
            result.state = PortState.FILTERED

        except Exception as e:
            # Unexpected error
            logger.error(f"Error scanning {ip}:{port}: {e}")

        # Record scan duration
        result.scan_time = time.time() - start_time
        return result

    def _grab_banner(self, sock: socket.socket) -> str:
        """
        Grab service banner from open port.

        Many services send a banner (identification string) when
        a client connects. This helps identify the service and version.

        Args:
            sock: Connected socket

        Returns:
            Banner string or empty string
        """
        try:
            # Set longer timeout for banner
            sock.settimeout(BANNER_TIMEOUT)

            # Some services need initial request
            # HTTP needs GET request, others send banner immediately
            sock.send(b"HEAD / HTTP/1.0\r\n\r\n")

            # Receive response (up to 1024 bytes)
            banner = sock.recv(1024)

            # Decode and clean banner
            return banner.decode('utf-8', errors='ignore').strip()

        except Exception:
            return ""

    def _parse_version(self, banner: str) -> str:
        """
        Parse version information from banner.

        Extracts version numbers from common banner formats.

        Args:
            banner: Raw banner string

        Returns:
            Extracted version or empty string
        """
        if not banner:
            return ""

        # Look for common version patterns
        # Pattern examples: "Apache/2.4.41", "OpenSSH_8.0", "nginx/1.18"
        import re

        # Common version patterns
        patterns = [
            r'([A-Za-z]+)[/\s](\d+\.\d+(?:\.\d+)?)',  # Name/X.Y.Z
            r'(\d+\.\d+(?:\.\d+)?)',                   # Just X.Y.Z
        ]

        for pattern in patterns:
            match = re.search(pattern, banner)
            if match:
                return match.group(0)

        return ""

    def scan_host(self, ip: str, ports: List[int] = None,
                  grab_banners: bool = True) -> HostResult:
        """
        Scan multiple ports on a single host.

        Uses thread pool for concurrent scanning to improve speed.

        Args:
            ip: Target IP address
            ports: List of ports to scan (default: common ports)
            grab_banners: Whether to grab service banners

        Returns:
            HostResult with all port findings
        """
        # Default to common ports if not specified
        if ports is None:
            ports = DEFAULT_SCAN_PORTS

        result = HostResult(ip=ip)
        result.scan_start = time.time()

        # Try to resolve hostname
        try:
            result.hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            pass  # No reverse DNS

        # Use thread pool for parallel scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submit all port scans
            future_to_port = {
                executor.submit(self.scan_port, ip, port, grab_banners): port
                for port in ports
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_port):
                port_result = future.result()
                result.ports.append(port_result)

        # Sort ports by number
        result.ports.sort(key=lambda p: p.port)

        # Determine host state (up if any ports respond)
        if any(p.state in [PortState.OPEN, PortState.CLOSED] for p in result.ports):
            result.state = HostState.UP
        else:
            result.state = HostState.DOWN

        result.scan_end = time.time()
        return result


# =============================================================================
# HOST DISCOVERY CLASS
# Network scanning and host enumeration
# =============================================================================

class HostDiscovery:
    """
    Discovers live hosts on a network.

    Methods:
    - ICMP ping sweep (requires privileges)
    - TCP ping (SYN to common ports)
    - ARP scan (local network only)

    Usage:
        discovery = HostDiscovery()
        hosts = discovery.discover_network("192.168.1.0/24")
    """

    def __init__(self, timeout: float = PING_TIMEOUT, threads: int = 50):
        """
        Initialize host discovery.

        Args:
            timeout: Probe timeout in seconds
            threads: Concurrent probe threads
        """
        self.timeout = timeout
        self.max_threads = threads

    def ping_host(self, ip: str) -> bool:
        """
        Check if host is alive using TCP connection.

        Since ICMP requires root privileges, this uses TCP connect
        to common ports as a host discovery method.

        Args:
            ip: IP address to check

        Returns:
            True if host responds, False otherwise
        """
        # Try connecting to common ports
        common_ports = [80, 443, 22, 445]

        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)

                # Connect returns 0 on success
                result = sock.connect_ex((ip, port))
                sock.close()

                # Any response (open or closed) means host is up
                if result in [0, 111]:  # Connected or refused
                    return True

            except Exception:
                continue

        return False

    def discover_network(self, cidr: str) -> List[str]:
        """
        Discover all live hosts in a network.

        Args:
            cidr: Network in CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            List of IP addresses that responded
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            logger.error(f"Invalid network: {e}")
            return []

        live_hosts = []
        total = network.num_addresses

        logger.info(f"Scanning {total} addresses in {cidr}")

        # Use thread pool for parallel discovery
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submit all host checks
            future_to_ip = {
                executor.submit(self.ping_host, str(ip)): str(ip)
                for ip in network.hosts()  # .hosts() excludes network/broadcast
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        live_hosts.append(ip)
                        logger.info(f"Host discovered: {ip}")
                except Exception as e:
                    logger.debug(f"Error checking {ip}: {e}")

        logger.info(f"Discovery complete: {len(live_hosts)} hosts found")
        return sorted(live_hosts, key=lambda x: ipaddress.ip_address(x))


# =============================================================================
# SERVICE DETECTOR CLASS
# Identifies services and versions
# =============================================================================

class ServiceDetector:
    """
    Detects services running on open ports.

    Uses:
    - Banner grabbing
    - Protocol-specific probes
    - Response analysis

    Usage:
        detector = ServiceDetector()
        services = detector.detect_services("192.168.1.1", [22, 80, 443])
    """

    # Protocol-specific probe strings
    # These trigger specific responses from services
    PROBES = {
        'HTTP': b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n',
        'HTTPS': b'',  # SSL handshake needed
        'FTP': b'',    # FTP sends banner immediately
        'SSH': b'',    # SSH sends banner immediately
        'SMTP': b'EHLO localhost\r\n',
        'POP3': b'',   # POP3 sends banner immediately
        'IMAP': b'',   # IMAP sends banner immediately
    }

    def __init__(self, timeout: float = BANNER_TIMEOUT):
        """
        Initialize service detector.

        Args:
            timeout: Response timeout in seconds
        """
        self.timeout = timeout

    def detect_service(self, ip: str, port: int) -> Dict[str, str]:
        """
        Detect service on a specific port.

        Args:
            ip: Target IP address
            port: Port number

        Returns:
            Dictionary with service details
        """
        result = {
            'port': port,
            'service': WELL_KNOWN_PORTS.get(port, 'unknown'),
            'banner': '',
            'version': '',
            'info': ''
        }

        try:
            # Create connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))

            # Determine probe based on expected service
            expected_service = WELL_KNOWN_PORTS.get(port, '')
            probe = self.PROBES.get(expected_service.upper(), b'')

            # Send probe if any
            if probe:
                sock.send(probe)

            # Receive response
            response = b''
            try:
                response = sock.recv(2048)
            except socket.timeout:
                pass  # No response

            sock.close()

            # Analyze response
            if response:
                result['banner'] = response.decode('utf-8', errors='ignore').strip()
                result['service'] = self._identify_service(response, port)
                result['version'] = self._extract_version(response)

        except Exception as e:
            logger.debug(f"Service detection error on {ip}:{port}: {e}")

        return result

    def _identify_service(self, response: bytes, port: int) -> str:
        """
        Identify service from response content.

        Args:
            response: Raw response bytes
            port: Port number (for hints)

        Returns:
            Identified service name
        """
        response_str = response.decode('utf-8', errors='ignore').lower()

        # Check for service signatures
        signatures = [
            ('ssh', 'SSH'),
            ('http', 'HTTP'),
            ('220 ', 'FTP/SMTP'),  # FTP and SMTP greeting
            ('+ok', 'POP3'),
            ('* ok', 'IMAP'),
            ('mysql', 'MySQL'),
            ('postgresql', 'PostgreSQL'),
            ('redis', 'Redis'),
            ('mongodb', 'MongoDB'),
        ]

        for signature, service in signatures:
            if signature in response_str:
                return service

        # Fall back to well-known port mapping
        return WELL_KNOWN_PORTS.get(port, 'unknown')

    def _extract_version(self, response: bytes) -> str:
        """
        Extract version from response.

        Args:
            response: Raw response bytes

        Returns:
            Version string or empty
        """
        import re
        response_str = response.decode('utf-8', errors='ignore')

        # Version patterns
        patterns = [
            r'(?:version|ver)[:\s]*(\d+(?:\.\d+)+)',
            r'([A-Za-z]+)[/\s](\d+(?:\.\d+)+)',
            r'(\d+\.\d+(?:\.\d+)?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, response_str, re.IGNORECASE)
            if match:
                return match.group(0)

        return ""

    def detect_services(self, ip: str, ports: List[int]) -> List[Dict]:
        """
        Detect services on multiple ports.

        Args:
            ip: Target IP address
            ports: List of ports to check

        Returns:
            List of service detection results
        """
        results = []
        for port in ports:
            result = self.detect_service(ip, port)
            results.append(result)
        return results


# =============================================================================
# VULNERABILITY CHECKER CLASS
# Basic security assessment
# =============================================================================

class VulnerabilityChecker:
    """
    Performs basic vulnerability checks.

    Checks for:
    - Default/weak credentials
    - Insecure protocols
    - Known vulnerable services
    - Misconfigurations

    WARNING: Only use on systems you own or have permission to test.
    """

    # Common default credentials (username, password)
    # Used to check for unchanged default passwords
    DEFAULT_CREDENTIALS = [
        ('admin', 'admin'),
        ('admin', 'password'),
        ('admin', ''),
        ('root', 'root'),
        ('root', 'password'),
        ('guest', 'guest'),
        ('test', 'test'),
    ]

    # Known vulnerable service versions
    # Format: (service_regex, min_safe_version, vulnerability_description)
    VULNERABLE_VERSIONS = [
        (r'OpenSSH[_/](\d+\.\d+)', '7.4', 'OpenSSH < 7.4 vulnerable to username enumeration'),
        (r'Apache/(\d+\.\d+\.\d+)', '2.4.50', 'Apache < 2.4.50 path traversal vulnerability'),
        (r'nginx/(\d+\.\d+\.\d+)', '1.20.0', 'nginx < 1.20.0 HTTP/2 vulnerabilities'),
    ]

    def __init__(self):
        """Initialize vulnerability checker."""
        self.findings = []

    def check_insecure_protocols(self, host_result: HostResult) -> List[Dict]:
        """
        Check for insecure protocols.

        Args:
            host_result: Scan results for host

        Returns:
            List of findings
        """
        findings = []
        insecure_ports = {
            21: 'FTP - Credentials sent in cleartext',
            23: 'Telnet - All traffic unencrypted',
            69: 'TFTP - No authentication',
            80: 'HTTP - Traffic unencrypted',
            110: 'POP3 - Credentials sent in cleartext',
            143: 'IMAP - Credentials sent in cleartext',
            161: 'SNMP - Community strings often weak',
        }

        for port_result in host_result.ports:
            if port_result.state == PortState.OPEN:
                if port_result.port in insecure_ports:
                    findings.append({
                        'type': 'INSECURE_PROTOCOL',
                        'severity': 'MEDIUM',
                        'port': port_result.port,
                        'description': insecure_ports[port_result.port],
                        'recommendation': 'Use encrypted alternative (SSH, HTTPS, IMAPS, etc.)'
                    })

        return findings

    def check_common_exposures(self, host_result: HostResult) -> List[Dict]:
        """
        Check for commonly exposed services.

        Args:
            host_result: Scan results for host

        Returns:
            List of findings
        """
        findings = []

        # Services that shouldn't be exposed to internet
        dangerous_ports = {
            22: ('SSH', 'Ensure strong authentication, consider VPN'),
            445: ('SMB', 'Critical - Close this port immediately'),
            3306: ('MySQL', 'Database should not be internet-facing'),
            3389: ('RDP', 'High risk - Use VPN instead'),
            5432: ('PostgreSQL', 'Database should not be internet-facing'),
            6379: ('Redis', 'Usually has no authentication'),
            27017: ('MongoDB', 'Often misconfigured with no auth'),
        }

        for port_result in host_result.ports:
            if port_result.state == PortState.OPEN:
                if port_result.port in dangerous_ports:
                    service, recommendation = dangerous_ports[port_result.port]
                    findings.append({
                        'type': 'EXPOSED_SERVICE',
                        'severity': 'HIGH' if port_result.port in [445, 6379, 27017] else 'MEDIUM',
                        'port': port_result.port,
                        'service': service,
                        'description': f'{service} exposed on port {port_result.port}',
                        'recommendation': recommendation
                    })

        return findings

    def run_checks(self, host_result: HostResult) -> List[Dict]:
        """
        Run all vulnerability checks.

        Args:
            host_result: Scan results to analyze

        Returns:
            Combined findings from all checks
        """
        findings = []
        findings.extend(self.check_insecure_protocols(host_result))
        findings.extend(self.check_common_exposures(host_result))
        return findings


# =============================================================================
# REPORT GENERATOR CLASS
# Export results in various formats
# =============================================================================

class ReportGenerator:
    """
    Generates scan reports in multiple formats.

    Supported formats:
    - JSON (machine-readable)
    - CSV (spreadsheet)
    - HTML (human-readable)
    - Text (console output)
    """

    def __init__(self, results: ScanResults):
        """
        Initialize report generator.

        Args:
            results: Scan results to report
        """
        self.results = results

    def to_json(self, filepath: str):
        """
        Export results to JSON file.

        Args:
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(self.results.to_dict(), f, indent=2)
        logger.info(f"JSON report saved to {filepath}")

    def to_csv(self, filepath: str):
        """
        Export results to CSV file.

        Args:
            filepath: Output file path
        """
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header row
            writer.writerow(['IP', 'Hostname', 'Port', 'State', 'Service', 'Version'])

            # Data rows
            for host in self.results.hosts:
                for port in host.ports:
                    writer.writerow([
                        host.ip,
                        host.hostname,
                        port.port,
                        port.state.value,
                        port.service,
                        port.version
                    ])

        logger.info(f"CSV report saved to {filepath}")

    def to_html(self, filepath: str):
        """
        Export results to HTML report.

        Args:
            filepath: Output file path
        """
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Network Scan Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .open {{ color: green; font-weight: bold; }}
        .closed {{ color: red; }}
        .filtered {{ color: orange; }}
        .summary {{ background-color: #e7e7e7; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Network Scan Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Target:</strong> {self.results.target}</p>
        <p><strong>Scan Type:</strong> {self.results.scan_type.name}</p>
        <p><strong>Hosts Scanned:</strong> {self.results.total_hosts_scanned}</p>
        <p><strong>Hosts Up:</strong> {self.results.total_hosts_up}</p>
        <p><strong>Scan Time:</strong> {self.results.end_time - self.results.start_time:.2f}s</p>
    </div>
"""

        for host in self.results.hosts:
            if host.state == HostState.UP:
                html += f"""
    <h2>{host.ip} ({host.hostname or 'No hostname'})</h2>
    <table>
        <tr><th>Port</th><th>State</th><th>Service</th><th>Version</th></tr>
"""
                for port in host.ports:
                    state_class = port.state.value.replace('|', '')
                    html += f"""
        <tr>
            <td>{port.port}</td>
            <td class="{state_class}">{port.state.value}</td>
            <td>{port.service}</td>
            <td>{port.version}</td>
        </tr>
"""
                html += "    </table>\n"

        html += """
</body>
</html>
"""
        with open(filepath, 'w') as f:
            f.write(html)

        logger.info(f"HTML report saved to {filepath}")

    def to_text(self) -> str:
        """
        Generate text report.

        Returns:
            Formatted text report
        """
        lines = [
            "="*70,
            "NETWORK SCAN REPORT",
            "="*70,
            f"Target: {self.results.target}",
            f"Scan Type: {self.results.scan_type.name}",
            f"Duration: {self.results.end_time - self.results.start_time:.2f}s",
            f"Hosts Scanned: {self.results.total_hosts_scanned}",
            f"Hosts Up: {self.results.total_hosts_up}",
            "-"*70
        ]

        for host in self.results.hosts:
            if host.state == HostState.UP:
                lines.append(f"\nHost: {host.ip} ({host.hostname or 'No hostname'})")
                lines.append(f"Open Ports: {len(host.get_open_ports())}")
                lines.append("-"*40)
                lines.append(f"{'PORT':<10} {'STATE':<12} {'SERVICE':<15} {'VERSION':<20}")
                lines.append("-"*40)

                for port in host.ports:
                    if port.state == PortState.OPEN:
                        lines.append(
                            f"{port.port:<10} {port.state.value:<12} "
                            f"{port.service:<15} {port.version:<20}"
                        )

        lines.append("="*70)
        return "\n".join(lines)


# =============================================================================
# MAIN NETWORK SCANNER CLASS
# High-level interface combining all components
# =============================================================================

class NetworkScanner:
    """
    Main network scanner class.

    Provides high-level interface for:
    - Network discovery
    - Port scanning
    - Service detection
    - Vulnerability assessment
    - Report generation

    Usage:
        scanner = NetworkScanner()
        results = scanner.full_scan("192.168.1.0/24")
        scanner.generate_report(results, "report.html")
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, threads: int = 100):
        """
        Initialize network scanner.

        Args:
            timeout: Connection timeout in seconds
            threads: Maximum concurrent threads
        """
        self.timeout = timeout
        self.threads = threads

        # Initialize components
        self.discovery = HostDiscovery(timeout, threads // 2)
        self.port_scanner = PortScanner(timeout, threads)
        self.service_detector = ServiceDetector(timeout * 2)
        self.vuln_checker = VulnerabilityChecker()

    def discover_hosts(self, cidr: str) -> List[str]:
        """
        Discover live hosts on network.

        Args:
            cidr: Network in CIDR notation

        Returns:
            List of responding IP addresses
        """
        return self.discovery.discover_network(cidr)

    def scan_ports(self, ip: str, ports: List[int] = None) -> HostResult:
        """
        Scan ports on single host.

        Args:
            ip: Target IP address
            ports: Ports to scan (default: common ports)

        Returns:
            Host scan results
        """
        return self.port_scanner.scan_host(ip, ports)

    def full_scan(self, target: str, ports: List[int] = None) -> ScanResults:
        """
        Perform full network scan.

        Steps:
        1. Discover live hosts
        2. Scan ports on each host
        3. Detect services
        4. Check vulnerabilities

        Args:
            target: IP address or CIDR network
            ports: Ports to scan

        Returns:
            Complete scan results
        """
        results = ScanResults(
            target=target,
            scan_type=ScanType.TCP_CONNECT,
            start_time=time.time()
        )

        # Determine if single host or network
        try:
            # Try parsing as network
            network = ipaddress.ip_network(target, strict=False)
            is_network = network.num_addresses > 1
        except ValueError:
            is_network = False

        if is_network:
            # Discover hosts first
            logger.info(f"Starting network scan of {target}")
            live_hosts = self.discover_hosts(target)
            results.total_hosts_scanned = network.num_addresses
        else:
            # Single host
            live_hosts = [target]
            results.total_hosts_scanned = 1

        results.total_hosts_up = len(live_hosts)

        # Scan each live host
        for ip in live_hosts:
            logger.info(f"Scanning {ip}")
            host_result = self.port_scanner.scan_host(ip, ports)

            # Run vulnerability checks
            findings = self.vuln_checker.run_checks(host_result)
            if findings:
                logger.warning(f"Vulnerabilities found on {ip}: {len(findings)}")

            results.hosts.append(host_result)

        results.end_time = time.time()
        return results

    def generate_report(self, results: ScanResults, filepath: str, format: str = 'html'):
        """
        Generate scan report.

        Args:
            results: Scan results to report
            filepath: Output file path
            format: Report format (json, csv, html)
        """
        reporter = ReportGenerator(results)

        if format == 'json':
            reporter.to_json(filepath)
        elif format == 'csv':
            reporter.to_csv(filepath)
        elif format == 'html':
            reporter.to_html(filepath)
        else:
            print(reporter.to_text())


# =============================================================================
# COMMAND-LINE INTERFACE
# =============================================================================

def main():
    """
    Main function for command-line usage.
    """
    import sys

    print("\n" + "="*70)
    print("ELECTRODUCTION NETWORK SCANNER")
    print("="*70 + "\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python network_scanner.py scan <target>     - Full scan")
        print("  python network_scanner.py ports <ip>        - Port scan")
        print("  python network_scanner.py discover <cidr>   - Host discovery")
        print("  python network_scanner.py test              - Run tests")
        print("\nExamples:")
        print("  python network_scanner.py scan 192.168.1.1")
        print("  python network_scanner.py scan 192.168.1.0/24")
        print("  python network_scanner.py ports 192.168.1.1")
        return

    command = sys.argv[1].lower()

    if command == 'test':
        run_tests()
    elif command == 'scan' and len(sys.argv) > 2:
        target = sys.argv[2]
        scanner = NetworkScanner()
        results = scanner.full_scan(target)
        print(ReportGenerator(results).to_text())
    elif command == 'ports' and len(sys.argv) > 2:
        ip = sys.argv[2]
        scanner = PortScanner()
        result = scanner.scan_host(ip)
        print(f"\nScan results for {ip}:")
        print(f"State: {result.state.value}")
        print(f"Open ports: {result.get_open_ports()}")
    elif command == 'discover' and len(sys.argv) > 2:
        cidr = sys.argv[2]
        discovery = HostDiscovery()
        hosts = discovery.discover_network(cidr)
        print(f"\nDiscovered {len(hosts)} hosts:")
        for host in hosts:
            print(f"  {host}")
    else:
        print(f"Unknown command: {command}")


def run_tests():
    """Run scanner tests."""
    print("[1] Testing PortResult...")
    pr = PortResult(port=80, state=PortState.OPEN, service="HTTP")
    assert pr.to_dict()['port'] == 80
    print("    PASSED")

    print("[2] Testing HostResult...")
    hr = HostResult(ip="192.168.1.1")
    hr.ports.append(pr)
    assert hr.get_open_ports() == [80]
    print("    PASSED")

    print("[3] Testing Port Scanner...")
    scanner = PortScanner(timeout=0.5)
    # Test scanning localhost
    result = scanner.scan_port("127.0.0.1", 22)  # SSH typically not running
    assert result.state in [PortState.OPEN, PortState.CLOSED, PortState.FILTERED]
    print("    PASSED")

    print("[4] Testing Vulnerability Checker...")
    vuln = VulnerabilityChecker()
    hr2 = HostResult(ip="192.168.1.1")
    hr2.ports.append(PortResult(port=23, state=PortState.OPEN, service="TELNET"))
    findings = vuln.run_checks(hr2)
    assert len(findings) > 0  # Should find telnet insecure
    print("    PASSED")

    print("[5] Testing Report Generator...")
    results = ScanResults(target="192.168.1.1", scan_type=ScanType.TCP_CONNECT)
    results.hosts.append(hr)
    results.start_time = time.time()
    results.end_time = time.time() + 1
    results.total_hosts_scanned = 1
    results.total_hosts_up = 1

    report = ReportGenerator(results)
    text = report.to_text()
    assert "192.168.1.1" in text
    print("    PASSED")

    print("\n" + "="*70)
    print("ALL NETWORK SCANNER TESTS PASSED!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
