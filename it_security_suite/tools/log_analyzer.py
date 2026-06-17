#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION IT SECURITY SUITE - LOG ANALYZER
================================================================================
A comprehensive security log analyzer that parses, analyzes, and reports on
various log formats including system logs, web server logs, firewall logs,
and authentication logs.

Features:
- Multi-format log parsing (syslog, Apache/Nginx, auth logs, JSON logs)
- Pattern matching for security events (failed logins, attacks, anomalies)
- Statistical analysis and trending
- Alert generation for suspicious activities
- Report generation (text, JSON, HTML)
- Real-time log monitoring mode
- IP reputation checking
- Geolocation lookup for suspicious IPs

Usage:
    python log_analyzer.py                    # Interactive mode
    python log_analyzer.py /var/log/auth.log  # Analyze specific log
    python log_analyzer.py --monitor          # Real-time monitoring
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os                    # Operating system interface for file operations
import sys                   # System-specific parameters and functions
import re                    # Regular expression operations for pattern matching
import json                  # JSON encoding and decoding for structured data
import time                  # Time-related functions for timestamps
import hashlib               # Secure hash algorithms for fingerprinting
import threading             # Thread-based parallelism for monitoring
import queue                 # Thread-safe queue for event passing
from datetime import datetime, timedelta  # Date/time manipulation
from typing import (         # Type hints for better code documentation
    Dict, List, Optional, Tuple, Any, Set, Callable, Pattern
)
from dataclasses import dataclass, field  # Decorator for data classes
from enum import Enum, auto  # Enumeration support for categorization
from collections import defaultdict, Counter  # Specialized containers
from pathlib import Path     # Object-oriented filesystem paths
import socket                # Network interface for IP resolution
import struct                # Binary data packing/unpacking


# =============================================================================
# ENUMERATIONS - Define categories and severity levels
# =============================================================================

class LogFormat(Enum):
    """
    Enumeration of supported log file formats.
    Each format has its own parsing rules and patterns.
    """
    SYSLOG = auto()      # Standard Unix syslog format
    APACHE = auto()      # Apache HTTP server access/error logs
    NGINX = auto()       # Nginx web server logs
    AUTH = auto()        # Authentication logs (login attempts)
    FIREWALL = auto()    # Firewall/iptables logs
    JSON = auto()        # Structured JSON log format
    WINDOWS = auto()     # Windows Event Log format
    CUSTOM = auto()      # User-defined custom format
    UNKNOWN = auto()     # Unrecognized format


class Severity(Enum):
    """
    Severity levels for security events and alerts.
    Based on common security logging standards.
    """
    DEBUG = 0       # Detailed debugging information
    INFO = 1        # General informational messages
    WARNING = 2     # Warning conditions that may need attention
    ERROR = 3       # Error conditions indicating problems
    CRITICAL = 4    # Critical conditions requiring immediate action
    ALERT = 5       # Action must be taken immediately


class EventType(Enum):
    """
    Categories of security events detected in logs.
    Used to classify and filter security incidents.
    """
    LOGIN_SUCCESS = auto()      # Successful authentication
    LOGIN_FAILURE = auto()      # Failed authentication attempt
    BRUTE_FORCE = auto()        # Multiple failed login attempts
    PORT_SCAN = auto()          # Port scanning activity detected
    SQL_INJECTION = auto()      # SQL injection attempt
    XSS_ATTACK = auto()         # Cross-site scripting attempt
    PATH_TRAVERSAL = auto()     # Directory traversal attempt
    MALWARE = auto()            # Malware signature detected
    DDOS = auto()               # Distributed denial of service
    PRIVILEGE_ESCALATION = auto()  # Privilege escalation attempt
    DATA_EXFILTRATION = auto()  # Potential data theft
    ANOMALY = auto()            # Unusual pattern detected
    SYSTEM_ERROR = auto()       # System-level error
    SERVICE_FAILURE = auto()    # Service crash or failure
    CONFIGURATION_CHANGE = auto()  # Config modification
    FILE_ACCESS = auto()        # Sensitive file access
    NETWORK_ERROR = auto()      # Network connectivity issues
    UNKNOWN = auto()            # Unclassified event


# =============================================================================
# DATA CLASSES - Structured data containers
# =============================================================================

@dataclass
class LogEntry:
    """
    Represents a single parsed log entry with all extracted fields.

    Attributes:
        timestamp: When the event occurred
        source: Origin of the log (hostname, IP, service)
        message: The actual log message content
        severity: Importance/urgency level
        raw: Original unparsed log line
        fields: Additional extracted key-value pairs
        event_type: Classified security event type
        log_format: Detected format of the source log
    """
    timestamp: datetime                          # Event timestamp
    source: str                                  # Log source identifier
    message: str                                 # Log message content
    severity: Severity = Severity.INFO           # Default to INFO level
    raw: str = ""                                # Original raw log line
    fields: Dict[str, Any] = field(default_factory=dict)  # Extra fields
    event_type: EventType = EventType.UNKNOWN    # Classified event type
    log_format: LogFormat = LogFormat.UNKNOWN    # Detected log format


@dataclass
class SecurityAlert:
    """
    Represents a security alert generated from log analysis.

    Attributes:
        id: Unique alert identifier
        timestamp: When the alert was generated
        event_type: Type of security event
        severity: Alert severity level
        source_ip: IP address involved (if applicable)
        description: Human-readable alert description
        evidence: List of log entries supporting this alert
        recommendations: Suggested remediation actions
        fingerprint: Unique hash for deduplication
    """
    id: str                                      # Unique identifier
    timestamp: datetime                          # Alert generation time
    event_type: EventType                        # Security event category
    severity: Severity                           # Alert importance
    source_ip: str = ""                          # Source IP if available
    description: str = ""                        # Alert description
    evidence: List[LogEntry] = field(default_factory=list)  # Supporting logs
    recommendations: List[str] = field(default_factory=list)  # Remediation
    fingerprint: str = ""                        # Dedup hash


@dataclass
class AnalysisReport:
    """
    Container for complete log analysis results.

    Attributes:
        start_time: Analysis start timestamp
        end_time: Analysis end timestamp
        total_entries: Number of log entries processed
        entries_by_severity: Count of entries per severity level
        entries_by_type: Count of entries per event type
        alerts: List of generated security alerts
        top_source_ips: Most frequent source IPs
        top_targets: Most targeted resources
        timeline: Events grouped by time period
        statistics: General statistical data
    """
    start_time: datetime                         # Analysis start
    end_time: datetime                           # Analysis end
    total_entries: int = 0                       # Total logs processed
    entries_by_severity: Dict[Severity, int] = field(default_factory=dict)
    entries_by_type: Dict[EventType, int] = field(default_factory=dict)
    alerts: List[SecurityAlert] = field(default_factory=list)
    top_source_ips: List[Tuple[str, int]] = field(default_factory=list)
    top_targets: List[Tuple[str, int]] = field(default_factory=list)
    timeline: Dict[str, int] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# LOG PARSER - Multi-format log parsing engine
# =============================================================================

class LogParser:
    """
    Multi-format log parser that automatically detects and parses various
    log file formats. Uses regular expressions for pattern matching.

    The parser maintains a registry of format patterns and applies them
    to extract structured data from raw log lines.
    """

    def __init__(self):
        """
        Initialize the log parser with format patterns and field extractors.
        Sets up regex patterns for each supported log format.
        """
        # Dictionary mapping log formats to their regex patterns
        # Each pattern captures key fields like timestamp, source, message
        self.patterns: Dict[LogFormat, Pattern] = {
            # Syslog format: "Mon DD HH:MM:SS hostname service[pid]: message"
            LogFormat.SYSLOG: re.compile(
                r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
                r'(?P<hostname>\S+)\s+'
                r'(?P<service>\S+?)(?:\[(?P<pid>\d+)\])?\s*:\s*'
                r'(?P<message>.*)$'
            ),

            # Apache Combined Log Format
            # IP - - [timestamp] "request" status size "referer" "user-agent"
            LogFormat.APACHE: re.compile(
                r'^(?P<ip>\S+)\s+\S+\s+\S+\s+'
                r'\[(?P<timestamp>[^\]]+)\]\s+'
                r'"(?P<request>[^"]*)"\s+'
                r'(?P<status>\d{3})\s+'
                r'(?P<size>\S+)\s*'
                r'(?:"(?P<referer>[^"]*)"\s*)?'
                r'(?:"(?P<user_agent>[^"]*)")?'
            ),

            # Nginx log format (similar to Apache but may differ)
            LogFormat.NGINX: re.compile(
                r'^(?P<ip>\S+)\s+-\s+(?P<user>\S+)\s+'
                r'\[(?P<timestamp>[^\]]+)\]\s+'
                r'"(?P<request>[^"]*)"\s+'
                r'(?P<status>\d{3})\s+'
                r'(?P<size>\d+)\s+'
                r'"(?P<referer>[^"]*)"\s+'
                r'"(?P<user_agent>[^"]*)"'
            ),

            # Auth log format: "timestamp hostname service[pid]: message"
            # Similar to syslog but used specifically for auth events
            LogFormat.AUTH: re.compile(
                r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
                r'(?P<hostname>\S+)\s+'
                r'(?P<service>sshd|sudo|login|su|passwd|useradd|groupadd)'
                r'(?:\[(?P<pid>\d+)\])?\s*:\s*'
                r'(?P<message>.*)$'
            ),

            # Firewall/iptables log format
            LogFormat.FIREWALL: re.compile(
                r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
                r'(?P<hostname>\S+)\s+kernel:\s*\[?\s*\d+\.\d+\]?\s*'
                r'(?P<prefix>\S+)?\s*'
                r'IN=(?P<in_iface>\S*)\s*OUT=(?P<out_iface>\S*)\s*'
                r'(?:MAC=(?P<mac>\S+)\s*)?'
                r'SRC=(?P<src_ip>\S+)\s+DST=(?P<dst_ip>\S+)\s+'
                r'.*?PROTO=(?P<proto>\S+)'
                r'(?:.*?SPT=(?P<src_port>\d+))?'
                r'(?:.*?DPT=(?P<dst_port>\d+))?'
            ),
        }

        # Timestamp format strings for parsing dates
        # Maps log formats to their expected timestamp patterns
        self.timestamp_formats = {
            LogFormat.SYSLOG: '%b %d %H:%M:%S',    # "Jan 15 10:30:45"
            LogFormat.APACHE: '%d/%b/%Y:%H:%M:%S %z',  # "15/Jan/2024:10:30:45 +0000"
            LogFormat.NGINX: '%d/%b/%Y:%H:%M:%S %z',
            LogFormat.AUTH: '%b %d %H:%M:%S',
            LogFormat.FIREWALL: '%b %d %H:%M:%S',
        }

        # Current year for logs that don't include year
        self.current_year = datetime.now().year

    def detect_format(self, line: str) -> LogFormat:
        """
        Automatically detect the format of a log line by testing
        against known patterns.

        Args:
            line: Raw log line to analyze

        Returns:
            LogFormat enum indicating detected format
        """
        # Try to parse as JSON first (common modern format)
        if line.strip().startswith('{'):
            try:
                json.loads(line)
                return LogFormat.JSON  # Valid JSON detected
            except json.JSONDecodeError:
                pass  # Not valid JSON, continue checking

        # Test each pattern in priority order
        # Auth logs take priority over generic syslog
        for fmt in [LogFormat.AUTH, LogFormat.FIREWALL, LogFormat.APACHE,
                    LogFormat.NGINX, LogFormat.SYSLOG]:
            if fmt in self.patterns and self.patterns[fmt].match(line):
                return fmt

        # No pattern matched
        return LogFormat.UNKNOWN

    def parse_timestamp(self, timestamp_str: str, fmt: LogFormat) -> datetime:
        """
        Parse a timestamp string into a datetime object.

        Args:
            timestamp_str: Raw timestamp string from log
            fmt: Log format to determine parsing rules

        Returns:
            datetime object representing the timestamp
        """
        try:
            # Get the format string for this log type
            format_str = self.timestamp_formats.get(fmt)

            if format_str:
                # Parse with the known format
                dt = datetime.strptime(timestamp_str, format_str)

                # Add year if not present (syslog format)
                if dt.year == 1900:  # Year wasn't in the format
                    dt = dt.replace(year=self.current_year)

                    # Handle year boundary (Dec -> Jan transition)
                    if dt > datetime.now() + timedelta(days=1):
                        dt = dt.replace(year=self.current_year - 1)

                return dt
            else:
                # Try common formats
                for try_fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S',
                               '%d/%b/%Y:%H:%M:%S', '%b %d %H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp_str, try_fmt)
                    except ValueError:
                        continue

        except Exception as e:
            pass  # Parsing failed, return current time

        return datetime.now()  # Default to current time if parsing fails

    def parse_line(self, line: str, expected_format: LogFormat = None) -> Optional[LogEntry]:
        """
        Parse a single log line into a structured LogEntry.

        Args:
            line: Raw log line to parse
            expected_format: Optional format hint (auto-detect if None)

        Returns:
            LogEntry object or None if parsing fails
        """
        line = line.strip()
        if not line:
            return None  # Skip empty lines

        # Detect format if not specified
        fmt = expected_format or self.detect_format(line)

        # Handle JSON format specially
        if fmt == LogFormat.JSON:
            return self._parse_json_log(line)

        # Try to match with detected format pattern
        if fmt in self.patterns:
            match = self.patterns[fmt].match(line)
            if match:
                return self._create_entry_from_match(match, fmt, line)

        # Fallback: create basic entry with raw line
        return LogEntry(
            timestamp=datetime.now(),
            source="unknown",
            message=line,
            raw=line,
            log_format=LogFormat.UNKNOWN
        )

    def _parse_json_log(self, line: str) -> Optional[LogEntry]:
        """
        Parse a JSON-formatted log line.

        Args:
            line: JSON string to parse

        Returns:
            LogEntry with fields extracted from JSON
        """
        try:
            data = json.loads(line)

            # Extract common fields with fallbacks
            timestamp_str = data.get('timestamp', data.get('time', data.get('@timestamp', '')))
            source = data.get('source', data.get('host', data.get('hostname', 'unknown')))
            message = data.get('message', data.get('msg', str(data)))
            level = data.get('level', data.get('severity', 'info'))

            # Map level string to Severity enum
            severity_map = {
                'debug': Severity.DEBUG,
                'info': Severity.INFO,
                'warning': Severity.WARNING, 'warn': Severity.WARNING,
                'error': Severity.ERROR, 'err': Severity.ERROR,
                'critical': Severity.CRITICAL, 'crit': Severity.CRITICAL,
                'alert': Severity.ALERT,
            }
            severity = severity_map.get(str(level).lower(), Severity.INFO)

            # Parse timestamp
            timestamp = datetime.now()
            if timestamp_str:
                try:
                    # Try ISO format
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    pass

            return LogEntry(
                timestamp=timestamp,
                source=str(source),
                message=str(message),
                severity=severity,
                raw=line,
                fields=data,  # Store all JSON fields
                log_format=LogFormat.JSON
            )

        except json.JSONDecodeError:
            return None

    def _create_entry_from_match(self, match: re.Match, fmt: LogFormat,
                                  raw_line: str) -> LogEntry:
        """
        Create a LogEntry from a regex match result.

        Args:
            match: Regex match object with named groups
            fmt: Detected log format
            raw_line: Original unparsed line

        Returns:
            Populated LogEntry object
        """
        groups = match.groupdict()

        # Parse timestamp
        timestamp = self.parse_timestamp(groups.get('timestamp', ''), fmt)

        # Determine source based on format
        if fmt in [LogFormat.APACHE, LogFormat.NGINX]:
            source = groups.get('ip', 'unknown')
            message = groups.get('request', raw_line)
        elif fmt == LogFormat.FIREWALL:
            source = groups.get('src_ip', 'unknown')
            message = f"{groups.get('proto', 'UNKNOWN')} {source}:{groups.get('src_port', '?')} -> {groups.get('dst_ip', '?')}:{groups.get('dst_port', '?')}"
        else:
            source = groups.get('hostname', groups.get('service', 'unknown'))
            message = groups.get('message', raw_line)

        return LogEntry(
            timestamp=timestamp,
            source=source,
            message=message,
            raw=raw_line,
            fields=groups,
            log_format=fmt
        )

    def parse_file(self, filepath: str, max_lines: int = None) -> List[LogEntry]:
        """
        Parse an entire log file into a list of LogEntry objects.

        Args:
            filepath: Path to the log file
            max_lines: Optional limit on number of lines to parse

        Returns:
            List of parsed LogEntry objects
        """
        entries = []
        detected_format = None

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    # Check line limit
                    if max_lines and i >= max_lines:
                        break

                    # Detect format from first valid line
                    if detected_format is None:
                        detected_format = self.detect_format(line)

                    # Parse line
                    entry = self.parse_line(line, detected_format)
                    if entry:
                        entries.append(entry)

        except FileNotFoundError:
            print(f"[ERROR] File not found: {filepath}")
        except PermissionError:
            print(f"[ERROR] Permission denied: {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to parse file: {e}")

        return entries


# =============================================================================
# SECURITY PATTERN DETECTOR - Identify security events in logs
# =============================================================================

class SecurityPatternDetector:
    """
    Detects security-relevant patterns in log entries using regex matching
    and heuristic analysis. Identifies attacks, anomalies, and suspicious
    activities.
    """

    def __init__(self):
        """
        Initialize the detector with security patterns.
        Each pattern maps to an event type and severity.
        """
        # Dictionary of security patterns: (regex, event_type, severity, description)
        self.patterns: List[Tuple[Pattern, EventType, Severity, str]] = [
            # Authentication patterns
            (
                re.compile(r'Failed password|authentication failure|failed login', re.I),
                EventType.LOGIN_FAILURE,
                Severity.WARNING,
                "Failed authentication attempt"
            ),
            (
                re.compile(r'Accepted password|session opened|successful login', re.I),
                EventType.LOGIN_SUCCESS,
                Severity.INFO,
                "Successful authentication"
            ),
            (
                re.compile(r'POSSIBLE BREAK-IN|repeated login failures|maximum attempts', re.I),
                EventType.BRUTE_FORCE,
                Severity.CRITICAL,
                "Potential brute force attack"
            ),

            # Web attack patterns
            (
                re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.I),
                EventType.SQL_INJECTION,
                Severity.ALERT,
                "Potential SQL injection attempt"
            ),
            (
                re.compile(r'(?:union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table)', re.I),
                EventType.SQL_INJECTION,
                Severity.ALERT,
                "SQL injection keywords detected"
            ),
            (
                re.compile(r'<script[^>]*>|javascript:|on\w+\s*=', re.I),
                EventType.XSS_ATTACK,
                Severity.ALERT,
                "Potential XSS attack"
            ),
            (
                re.compile(r'\.\./|\.\.\\|%2e%2e|%252e', re.I),
                EventType.PATH_TRAVERSAL,
                Severity.CRITICAL,
                "Path traversal attempt"
            ),
            (
                re.compile(r'/etc/passwd|/etc/shadow|/proc/self|/windows/system32', re.I),
                EventType.PATH_TRAVERSAL,
                Severity.CRITICAL,
                "Sensitive file access attempt"
            ),

            # Network attack patterns
            (
                re.compile(r'port\s*scan|nmap|masscan|SYN\s*flood', re.I),
                EventType.PORT_SCAN,
                Severity.WARNING,
                "Port scanning activity"
            ),
            (
                re.compile(r'DDoS|denial.of.service|flood\s*attack', re.I),
                EventType.DDOS,
                Severity.CRITICAL,
                "Potential DDoS attack"
            ),

            # Malware patterns
            (
                re.compile(r'malware|virus|trojan|ransomware|cryptolocker', re.I),
                EventType.MALWARE,
                Severity.ALERT,
                "Malware indicator detected"
            ),
            (
                re.compile(r'reverse.shell|bind.shell|meterpreter|c2.beacon', re.I),
                EventType.MALWARE,
                Severity.ALERT,
                "Command & control indicator"
            ),

            # Privilege escalation
            (
                re.compile(r'sudo.*FAILED|unauthorized.*root|privilege.*escalat', re.I),
                EventType.PRIVILEGE_ESCALATION,
                Severity.CRITICAL,
                "Privilege escalation attempt"
            ),
            (
                re.compile(r'setuid|setgid|chmod\s+[0-7]*[4-7][0-7]{2}', re.I),
                EventType.PRIVILEGE_ESCALATION,
                Severity.WARNING,
                "Permission modification detected"
            ),

            # System errors
            (
                re.compile(r'segfault|kernel\s*panic|out\s*of\s*memory|oom.killer', re.I),
                EventType.SYSTEM_ERROR,
                Severity.ERROR,
                "System error detected"
            ),
            (
                re.compile(r'service\s+\w+\s+(failed|crash|stopped)|systemd.*failed', re.I),
                EventType.SERVICE_FAILURE,
                Severity.ERROR,
                "Service failure detected"
            ),

            # Data exfiltration indicators
            (
                re.compile(r'large.download|bulk.transfer|unusual.outbound', re.I),
                EventType.DATA_EXFILTRATION,
                Severity.CRITICAL,
                "Potential data exfiltration"
            ),
        ]

        # Known malicious IP ranges (simplified - in production use threat intel feeds)
        self.suspicious_ip_patterns = [
            re.compile(r'^10\.0\.0\.'),      # Often used in attacks (internal)
            re.compile(r'^192\.168\.'),       # Internal network probing
            re.compile(r'^0\.0\.0\.0'),        # Invalid source
            re.compile(r'^255\.255\.255\.'),  # Broadcast abuse
        ]

    def classify_entry(self, entry: LogEntry) -> Tuple[EventType, Severity, str]:
        """
        Classify a log entry by matching against security patterns.

        Args:
            entry: LogEntry to classify

        Returns:
            Tuple of (EventType, Severity, description)
        """
        # Check message against all patterns
        for pattern, event_type, severity, description in self.patterns:
            if pattern.search(entry.message) or pattern.search(entry.raw):
                # Update entry with classification
                entry.event_type = event_type
                entry.severity = severity
                return (event_type, severity, description)

        # Check HTTP status codes for web logs
        if entry.log_format in [LogFormat.APACHE, LogFormat.NGINX]:
            status = entry.fields.get('status', '')
            if status.startswith('4'):  # 4xx errors
                return (EventType.ANOMALY, Severity.WARNING, f"HTTP {status} error")
            elif status.startswith('5'):  # 5xx errors
                return (EventType.SYSTEM_ERROR, Severity.ERROR, f"HTTP {status} server error")

        # Default classification
        return (EventType.UNKNOWN, Severity.INFO, "Normal log entry")

    def detect_brute_force(self, entries: List[LogEntry],
                           threshold: int = 5, window_seconds: int = 300) -> List[SecurityAlert]:
        """
        Detect brute force attacks by analyzing failed login patterns.

        Args:
            entries: List of log entries to analyze
            threshold: Number of failures to trigger alert
            window_seconds: Time window for counting failures

        Returns:
            List of SecurityAlert objects for detected attacks
        """
        alerts = []

        # Group failed logins by source IP
        failures_by_ip: Dict[str, List[LogEntry]] = defaultdict(list)

        for entry in entries:
            if entry.event_type == EventType.LOGIN_FAILURE:
                # Extract source IP from entry
                source_ip = entry.fields.get('ip', entry.source)

                # Also try to extract from message
                ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', entry.message)
                if ip_match:
                    source_ip = ip_match.group(1)

                failures_by_ip[source_ip].append(entry)

        # Analyze each IP's failure pattern
        for ip, ip_failures in failures_by_ip.items():
            # Sort by timestamp
            ip_failures.sort(key=lambda e: e.timestamp)

            # Sliding window analysis
            window_start = 0
            for i, entry in enumerate(ip_failures):
                # Move window start forward
                while (window_start < i and
                       (entry.timestamp - ip_failures[window_start].timestamp).total_seconds() > window_seconds):
                    window_start += 1

                # Count failures in window
                window_count = i - window_start + 1

                # Check threshold
                if window_count >= threshold:
                    # Generate alert
                    alert = SecurityAlert(
                        id=f"BF-{ip}-{entry.timestamp.isoformat()}",
                        timestamp=datetime.now(),
                        event_type=EventType.BRUTE_FORCE,
                        severity=Severity.CRITICAL,
                        source_ip=ip,
                        description=f"Brute force attack detected from {ip}: {window_count} failed logins in {window_seconds}s",
                        evidence=ip_failures[window_start:i+1],
                        recommendations=[
                            f"Block IP address {ip} at the firewall",
                            "Review authentication logs for compromised accounts",
                            "Consider implementing rate limiting",
                            "Enable account lockout after failed attempts"
                        ]
                    )

                    # Generate fingerprint for deduplication
                    alert.fingerprint = hashlib.md5(
                        f"{ip}-{window_count}".encode()
                    ).hexdigest()

                    alerts.append(alert)
                    break  # One alert per IP

        return alerts

    def detect_port_scan(self, entries: List[LogEntry],
                         threshold: int = 10, window_seconds: int = 60) -> List[SecurityAlert]:
        """
        Detect port scanning by analyzing connection patterns.

        Args:
            entries: List of log entries to analyze
            threshold: Number of ports to trigger alert
            window_seconds: Time window for counting

        Returns:
            List of SecurityAlert objects for detected scans
        """
        alerts = []

        # Track unique destination ports by source IP
        ports_by_ip: Dict[str, Dict[datetime, Set[int]]] = defaultdict(lambda: defaultdict(set))

        for entry in entries:
            # Extract source IP and destination port from firewall logs
            if entry.log_format == LogFormat.FIREWALL:
                src_ip = entry.fields.get('src_ip', '')
                dst_port = entry.fields.get('dst_port', '')

                if src_ip and dst_port:
                    try:
                        port = int(dst_port)
                        # Group by minute for windowing
                        minute = entry.timestamp.replace(second=0, microsecond=0)
                        ports_by_ip[src_ip][minute].add(port)
                    except ValueError:
                        pass

        # Analyze port patterns
        for ip, time_ports in ports_by_ip.items():
            # Aggregate ports across time window
            all_ports = set()
            for minute, ports in time_ports.items():
                all_ports.update(ports)

            if len(all_ports) >= threshold:
                alert = SecurityAlert(
                    id=f"PS-{ip}-{datetime.now().isoformat()}",
                    timestamp=datetime.now(),
                    event_type=EventType.PORT_SCAN,
                    severity=Severity.WARNING,
                    source_ip=ip,
                    description=f"Port scan detected from {ip}: {len(all_ports)} unique ports",
                    recommendations=[
                        f"Investigate traffic from {ip}",
                        "Review firewall rules",
                        "Consider blacklisting source IP"
                    ]
                )

                alert.fingerprint = hashlib.md5(f"PS-{ip}".encode()).hexdigest()
                alerts.append(alert)

        return alerts


# =============================================================================
# LOG ANALYZER - Main analysis engine
# =============================================================================

class LogAnalyzer:
    """
    Main log analysis engine that coordinates parsing, pattern detection,
    and report generation. Provides high-level analysis functions.
    """

    def __init__(self):
        """
        Initialize the log analyzer with parser and detector components.
        """
        self.parser = LogParser()                    # Log file parser
        self.detector = SecurityPatternDetector()    # Pattern detector
        self.entries: List[LogEntry] = []            # Parsed entries
        self.alerts: List[SecurityAlert] = []        # Generated alerts
        self.statistics: Dict[str, Any] = {}         # Analysis statistics

    def analyze_file(self, filepath: str, max_lines: int = None) -> AnalysisReport:
        """
        Perform complete analysis on a log file.

        Args:
            filepath: Path to log file to analyze
            max_lines: Optional limit on lines to process

        Returns:
            AnalysisReport containing all findings
        """
        print(f"[*] Analyzing: {filepath}")
        start_time = datetime.now()

        # Parse log file
        print("[*] Parsing log entries...")
        self.entries = self.parser.parse_file(filepath, max_lines)
        print(f"    Parsed {len(self.entries)} entries")

        # Classify each entry
        print("[*] Classifying entries...")
        entries_by_severity: Dict[Severity, int] = defaultdict(int)
        entries_by_type: Dict[EventType, int] = defaultdict(int)
        source_ip_counter: Counter = Counter()
        target_counter: Counter = Counter()

        for entry in self.entries:
            # Classify the entry
            event_type, severity, description = self.detector.classify_entry(entry)
            entry.event_type = event_type
            entry.severity = severity

            # Update counters
            entries_by_severity[severity] += 1
            entries_by_type[event_type] += 1

            # Track source IPs
            source_ip = entry.fields.get('ip', entry.fields.get('src_ip', ''))
            if source_ip:
                source_ip_counter[source_ip] += 1

            # Track targets (requested URLs for web logs)
            if entry.log_format in [LogFormat.APACHE, LogFormat.NGINX]:
                request = entry.fields.get('request', '')
                if request:
                    # Extract URL path
                    parts = request.split()
                    if len(parts) >= 2:
                        target_counter[parts[1]] += 1

        # Detect attacks
        print("[*] Detecting security incidents...")
        self.alerts = []

        # Brute force detection
        bf_alerts = self.detector.detect_brute_force(self.entries)
        self.alerts.extend(bf_alerts)

        # Port scan detection
        ps_alerts = self.detector.detect_port_scan(self.entries)
        self.alerts.extend(ps_alerts)

        # Create alerts for high-severity entries
        for entry in self.entries:
            if entry.severity in [Severity.CRITICAL, Severity.ALERT]:
                alert = SecurityAlert(
                    id=f"EVT-{entry.timestamp.isoformat()}",
                    timestamp=entry.timestamp,
                    event_type=entry.event_type,
                    severity=entry.severity,
                    source_ip=entry.fields.get('ip', entry.fields.get('src_ip', '')),
                    description=entry.message[:200],  # Truncate long messages
                    evidence=[entry]
                )
                self.alerts.append(alert)

        print(f"    Generated {len(self.alerts)} alerts")

        # Build timeline
        print("[*] Building timeline...")
        timeline: Dict[str, int] = defaultdict(int)
        for entry in self.entries:
            hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
            timeline[hour_key] += 1

        # Create report
        end_time = datetime.now()

        report = AnalysisReport(
            start_time=start_time,
            end_time=end_time,
            total_entries=len(self.entries),
            entries_by_severity=dict(entries_by_severity),
            entries_by_type=dict(entries_by_type),
            alerts=self.alerts,
            top_source_ips=source_ip_counter.most_common(20),
            top_targets=target_counter.most_common(20),
            timeline=dict(timeline),
            statistics={
                'analysis_duration': (end_time - start_time).total_seconds(),
                'alerts_critical': sum(1 for a in self.alerts if a.severity == Severity.CRITICAL),
                'alerts_warning': sum(1 for a in self.alerts if a.severity == Severity.WARNING),
                'unique_sources': len(source_ip_counter),
                'unique_targets': len(target_counter),
            }
        )

        return report

    def analyze_entries(self, entries: List[LogEntry]) -> AnalysisReport:
        """
        Analyze a list of pre-parsed log entries.

        Args:
            entries: List of LogEntry objects to analyze

        Returns:
            AnalysisReport with findings
        """
        self.entries = entries

        # Use similar logic to analyze_file but without parsing step
        start_time = datetime.now()
        entries_by_severity: Dict[Severity, int] = defaultdict(int)
        entries_by_type: Dict[EventType, int] = defaultdict(int)

        for entry in self.entries:
            self.detector.classify_entry(entry)
            entries_by_severity[entry.severity] += 1
            entries_by_type[entry.event_type] += 1

        # Detect attacks
        self.alerts = []
        self.alerts.extend(self.detector.detect_brute_force(self.entries))
        self.alerts.extend(self.detector.detect_port_scan(self.entries))

        end_time = datetime.now()

        return AnalysisReport(
            start_time=start_time,
            end_time=end_time,
            total_entries=len(self.entries),
            entries_by_severity=dict(entries_by_severity),
            entries_by_type=dict(entries_by_type),
            alerts=self.alerts
        )

    def get_entries_by_severity(self, min_severity: Severity) -> List[LogEntry]:
        """
        Filter entries by minimum severity level.

        Args:
            min_severity: Minimum severity to include

        Returns:
            List of entries meeting severity threshold
        """
        return [e for e in self.entries if e.severity.value >= min_severity.value]

    def get_entries_by_type(self, event_type: EventType) -> List[LogEntry]:
        """
        Filter entries by event type.

        Args:
            event_type: Event type to filter for

        Returns:
            List of entries matching event type
        """
        return [e for e in self.entries if e.event_type == event_type]

    def search_entries(self, pattern: str, case_sensitive: bool = False) -> List[LogEntry]:
        """
        Search entries for a regex pattern.

        Args:
            pattern: Regex pattern to search for
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            List of entries matching the pattern
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        return [e for e in self.entries if regex.search(e.message) or regex.search(e.raw)]


# =============================================================================
# REPORT GENERATOR - Generate analysis reports in various formats
# =============================================================================

class ReportGenerator:
    """
    Generates analysis reports in multiple formats (text, JSON, HTML).
    Creates human-readable summaries and machine-parseable exports.
    """

    def __init__(self, report: AnalysisReport):
        """
        Initialize the report generator with analysis results.

        Args:
            report: AnalysisReport to generate output from
        """
        self.report = report

    def generate_text_report(self) -> str:
        """
        Generate a plain text report suitable for console output.

        Returns:
            Formatted text report string
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("                    LOG ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"  Analysis Start:    {self.report.start_time}")
        lines.append(f"  Analysis End:      {self.report.end_time}")
        lines.append(f"  Duration:          {self.report.statistics.get('analysis_duration', 0):.2f} seconds")
        lines.append(f"  Total Entries:     {self.report.total_entries}")
        lines.append(f"  Total Alerts:      {len(self.report.alerts)}")
        lines.append(f"  Critical Alerts:   {self.report.statistics.get('alerts_critical', 0)}")
        lines.append("")

        # Severity breakdown
        lines.append("ENTRIES BY SEVERITY")
        lines.append("-" * 40)
        for severity, count in sorted(self.report.entries_by_severity.items(),
                                       key=lambda x: x[0].value, reverse=True):
            pct = (count / self.report.total_entries * 100) if self.report.total_entries > 0 else 0
            bar = "█" * int(pct / 5)  # Visual bar
            lines.append(f"  {severity.name:12s}: {count:6d} ({pct:5.1f}%) {bar}")
        lines.append("")

        # Event type breakdown
        lines.append("ENTRIES BY EVENT TYPE")
        lines.append("-" * 40)
        for event_type, count in sorted(self.report.entries_by_type.items(),
                                         key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {event_type.name:25s}: {count:6d}")
        lines.append("")

        # Top source IPs
        if self.report.top_source_ips:
            lines.append("TOP SOURCE IPS")
            lines.append("-" * 40)
            for ip, count in self.report.top_source_ips[:10]:
                lines.append(f"  {ip:20s}: {count:6d}")
            lines.append("")

        # Alerts
        if self.report.alerts:
            lines.append("SECURITY ALERTS")
            lines.append("-" * 40)
            for alert in sorted(self.report.alerts, key=lambda a: a.severity.value, reverse=True)[:20]:
                severity_marker = "🔴" if alert.severity == Severity.CRITICAL else "🟡" if alert.severity == Severity.WARNING else "🟢"
                lines.append(f"  [{alert.severity.name}] {alert.event_type.name}")
                lines.append(f"      Source: {alert.source_ip or 'N/A'}")
                lines.append(f"      {alert.description[:60]}...")
                if alert.recommendations:
                    lines.append(f"      Recommendation: {alert.recommendations[0]}")
                lines.append("")

        lines.append("=" * 80)
        lines.append("                    END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """
        Generate a JSON-formatted report for machine parsing.

        Returns:
            JSON string representation of the report
        """
        # Convert to serializable format
        data = {
            'summary': {
                'start_time': self.report.start_time.isoformat(),
                'end_time': self.report.end_time.isoformat(),
                'total_entries': self.report.total_entries,
                'statistics': self.report.statistics,
            },
            'entries_by_severity': {
                sev.name: count for sev, count in self.report.entries_by_severity.items()
            },
            'entries_by_type': {
                evt.name: count for evt, count in self.report.entries_by_type.items()
            },
            'top_source_ips': [
                {'ip': ip, 'count': count} for ip, count in self.report.top_source_ips
            ],
            'top_targets': [
                {'target': target, 'count': count} for target, count in self.report.top_targets
            ],
            'alerts': [
                {
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'event_type': alert.event_type.name,
                    'severity': alert.severity.name,
                    'source_ip': alert.source_ip,
                    'description': alert.description,
                    'recommendations': alert.recommendations,
                }
                for alert in self.report.alerts
            ],
            'timeline': self.report.timeline,
        }

        return json.dumps(data, indent=2)

    def generate_html_report(self) -> str:
        """
        Generate an HTML report with styling for web viewing.

        Returns:
            HTML string of the report
        """
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Log Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #666; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-box { background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-box.warning { background: #fff3e0; }
        .stat-box.danger { background: #ffebee; }
        .stat-value { font-size: 24px; font-weight: bold; color: #333; }
        .stat-label { color: #666; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f5f5f5; }
        .severity-critical { color: #d32f2f; font-weight: bold; }
        .severity-warning { color: #f57c00; }
        .severity-info { color: #1976d2; }
        .alert-card { background: #fff; border-left: 4px solid #d32f2f; padding: 15px; margin: 10px 0; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .alert-card.warning { border-left-color: #f57c00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Log Analysis Report</h1>

        <div class="summary">
            <div class="stat-box">
                <div class="stat-value">""" + str(self.report.total_entries) + """</div>
                <div class="stat-label">Total Entries</div>
            </div>
            <div class="stat-box danger">
                <div class="stat-value">""" + str(len(self.report.alerts)) + """</div>
                <div class="stat-label">Security Alerts</div>
            </div>
            <div class="stat-box warning">
                <div class="stat-value">""" + str(self.report.statistics.get('alerts_critical', 0)) + """</div>
                <div class="stat-label">Critical Alerts</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">""" + str(self.report.statistics.get('unique_sources', 0)) + """</div>
                <div class="stat-label">Unique Sources</div>
            </div>
        </div>

        <h2>Severity Breakdown</h2>
        <table>
            <tr><th>Severity</th><th>Count</th><th>Percentage</th></tr>"""

        for severity, count in sorted(self.report.entries_by_severity.items(),
                                       key=lambda x: x[0].value, reverse=True):
            pct = (count / self.report.total_entries * 100) if self.report.total_entries > 0 else 0
            css_class = 'severity-critical' if severity == Severity.CRITICAL else 'severity-warning' if severity == Severity.WARNING else 'severity-info'
            html += f"""
            <tr class="{css_class}">
                <td>{severity.name}</td>
                <td>{count}</td>
                <td>{pct:.1f}%</td>
            </tr>"""

        html += """
        </table>

        <h2>Security Alerts</h2>"""

        for alert in sorted(self.report.alerts, key=lambda a: a.severity.value, reverse=True)[:20]:
            card_class = 'alert-card' if alert.severity == Severity.CRITICAL else 'alert-card warning'
            html += f"""
        <div class="{card_class}">
            <strong>[{alert.severity.name}] {alert.event_type.name}</strong><br>
            <small>Source: {alert.source_ip or 'N/A'}</small><br>
            {alert.description[:100]}...
        </div>"""

        html += """
    </div>
</body>
</html>"""

        return html


# =============================================================================
# REAL-TIME LOG MONITOR - Monitor logs in real-time
# =============================================================================

class LogMonitor:
    """
    Real-time log file monitor that watches log files for new entries
    and triggers alerts when security events are detected.
    """

    def __init__(self, callback: Callable[[LogEntry], None] = None):
        """
        Initialize the log monitor.

        Args:
            callback: Optional function to call for each new entry
        """
        self.parser = LogParser()                    # Log parser instance
        self.detector = SecurityPatternDetector()    # Pattern detector
        self.callback = callback                     # Entry callback
        self.running = False                         # Monitor state
        self.threads: List[threading.Thread] = []    # Monitor threads
        self.alert_queue: queue.Queue = queue.Queue()  # Alert queue

    def monitor_file(self, filepath: str, poll_interval: float = 1.0):
        """
        Monitor a log file for new entries using tail-like behavior.

        Args:
            filepath: Path to log file to monitor
            poll_interval: Seconds between polls for new content
        """
        try:
            with open(filepath, 'r') as f:
                # Seek to end of file
                f.seek(0, 2)  # SEEK_END

                while self.running:
                    # Read new lines
                    line = f.readline()

                    if line:
                        # Parse and process the line
                        entry = self.parser.parse_line(line)
                        if entry:
                            # Classify the entry
                            event_type, severity, desc = self.detector.classify_entry(entry)

                            # Call callback if provided
                            if self.callback:
                                self.callback(entry)

                            # Generate alert for high severity
                            if severity.value >= Severity.WARNING.value:
                                alert = SecurityAlert(
                                    id=f"RT-{datetime.now().isoformat()}",
                                    timestamp=datetime.now(),
                                    event_type=event_type,
                                    severity=severity,
                                    description=desc,
                                    evidence=[entry]
                                )
                                self.alert_queue.put(alert)

                                # Print alert immediately
                                print(f"\n[ALERT] [{severity.name}] {event_type.name}: {desc}")
                                print(f"        {entry.message[:80]}")
                    else:
                        # No new data, wait before next poll
                        time.sleep(poll_interval)

        except FileNotFoundError:
            print(f"[ERROR] File not found: {filepath}")
        except Exception as e:
            print(f"[ERROR] Monitor error: {e}")

    def start(self, filepaths: List[str]):
        """
        Start monitoring multiple log files.

        Args:
            filepaths: List of log file paths to monitor
        """
        self.running = True

        print(f"[*] Starting real-time log monitor...")
        print(f"[*] Monitoring {len(filepaths)} file(s)")
        print("[*] Press Ctrl+C to stop\n")

        # Start a thread for each file
        for filepath in filepaths:
            thread = threading.Thread(
                target=self.monitor_file,
                args=(filepath,),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            print(f"    [+] Monitoring: {filepath}")

    def stop(self):
        """Stop all monitoring threads."""
        self.running = False
        print("\n[*] Stopping log monitor...")

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2.0)

        self.threads.clear()
        print("[*] Monitor stopped")

    def get_alerts(self) -> List[SecurityAlert]:
        """
        Get all alerts from the queue.

        Returns:
            List of SecurityAlert objects
        """
        alerts = []
        while not self.alert_queue.empty():
            try:
                alerts.append(self.alert_queue.get_nowait())
            except queue.Empty:
                break
        return alerts


# =============================================================================
# SAMPLE LOG GENERATOR - Generate sample logs for testing
# =============================================================================

def generate_sample_logs(output_file: str = None, num_entries: int = 100) -> List[str]:
    """
    Generate sample log entries for testing the analyzer.
    Creates a mix of normal and attack traffic.

    Args:
        output_file: Optional file path to write logs
        num_entries: Number of entries to generate

    Returns:
        List of generated log lines
    """
    import random

    # Sample data pools
    ips = [
        "192.168.1.100", "192.168.1.101", "10.0.0.50", "10.0.0.51",
        "172.16.0.10", "8.8.8.8", "1.2.3.4", "5.6.7.8"
    ]

    services = ["sshd", "nginx", "apache2", "mysql", "postfix"]

    users = ["root", "admin", "user1", "guest", "www-data"]

    # Log templates
    templates = [
        # Normal auth events
        ("AUTH", "{timestamp} server sshd[{pid}]: Accepted password for {user} from {ip} port 22 ssh2"),
        ("AUTH", "{timestamp} server sshd[{pid}]: Failed password for {user} from {ip} port 22 ssh2"),
        ("AUTH", "{timestamp} server sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/bin/ls"),

        # Web server events
        ("APACHE", '{ip} - - [{timestamp}] "GET /index.html HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'),
        ("APACHE", '{ip} - - [{timestamp}] "POST /login HTTP/1.1" 302 0 "-" "Mozilla/5.0"'),
        ("APACHE", '{ip} - - [{timestamp}] "GET /admin HTTP/1.1" 403 500 "-" "Mozilla/5.0"'),

        # Attack patterns
        ("APACHE", '{ip} - - [{timestamp}] "GET /page?id=1\' OR \'1\'=\'1 HTTP/1.1" 200 5000 "-" "sqlmap/1.0"'),
        ("APACHE", '{ip} - - [{timestamp}] "GET /<script>alert(1)</script> HTTP/1.1" 404 0 "-" "Mozilla/5.0"'),
        ("APACHE", '{ip} - - [{timestamp}] "GET /../../../etc/passwd HTTP/1.1" 400 0 "-" "Nikto"'),

        # Brute force simulation
        ("AUTH", "{timestamp} server sshd[{pid}]: Failed password for invalid user admin from {ip} port 22"),
        ("AUTH", "{timestamp} server sshd[{pid}]: POSSIBLE BREAK-IN ATTEMPT! from {ip}"),

        # System events
        ("SYSLOG", "{timestamp} server kernel: [12345.678] Out of memory: Kill process 1234"),
        ("SYSLOG", "{timestamp} server systemd[1]: nginx.service: Failed with result 'exit-code'"),
    ]

    logs = []
    base_time = datetime.now() - timedelta(hours=1)

    for i in range(num_entries):
        # Pick random template
        log_type, template = random.choice(templates)

        # Generate timestamp
        timestamp = base_time + timedelta(seconds=i * 36)  # Spread over an hour

        # Format based on log type
        if log_type == "APACHE":
            ts_str = timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
        else:
            ts_str = timestamp.strftime("%b %d %H:%M:%S")

        # Fill template
        log_line = template.format(
            timestamp=ts_str,
            ip=random.choice(ips),
            user=random.choice(users),
            pid=random.randint(1000, 65535)
        )

        logs.append(log_line)

    # Write to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(logs))
        print(f"[*] Generated {num_entries} sample logs to {output_file}")

    return logs


# =============================================================================
# DEMO AND MAIN ENTRY POINT
# =============================================================================

def run_demo():
    """
    Run a demonstration of the Log Analyzer capabilities.
    Generates sample logs and analyzes them.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ELECTRODUCTION LOG ANALYZER                               ║
║                    Security Log Analysis Tool                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Generate sample logs
    print("[*] Generating sample log data...")
    sample_file = "/tmp/sample_security.log"
    generate_sample_logs(sample_file, 200)

    # Initialize analyzer
    print("\n[*] Initializing Log Analyzer...")
    analyzer = LogAnalyzer()

    # Analyze the sample logs
    print("\n[*] Running analysis...")
    report = analyzer.analyze_file(sample_file)

    # Generate and print text report
    print("\n")
    generator = ReportGenerator(report)
    print(generator.generate_text_report())

    # Save JSON report
    json_report = generator.generate_json_report()
    json_file = "/tmp/log_analysis_report.json"
    with open(json_file, 'w') as f:
        f.write(json_report)
    print(f"\n[*] JSON report saved to: {json_file}")

    # Save HTML report
    html_report = generator.generate_html_report()
    html_file = "/tmp/log_analysis_report.html"
    with open(html_file, 'w') as f:
        f.write(html_report)
    print(f"[*] HTML report saved to: {html_file}")

    # Demonstrate search functionality
    print("\n[*] Demonstrating search functionality...")
    failed_logins = analyzer.search_entries("Failed password")
    print(f"    Found {len(failed_logins)} failed login attempts")

    sql_attempts = analyzer.search_entries("OR.*=")
    print(f"    Found {len(sql_attempts)} potential SQL injection attempts")

    # Show some examples
    print("\n[*] Sample high-severity entries:")
    high_severity = analyzer.get_entries_by_severity(Severity.WARNING)[:5]
    for entry in high_severity:
        print(f"    [{entry.severity.name}] {entry.message[:60]}...")

    print("\n[*] Demo completed!")
    print("[*] In production, point this at real log files like /var/log/auth.log")


def main():
    """
    Main entry point for the Log Analyzer.
    Handles command-line arguments and dispatches to appropriate functions.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ELECTRODUCTION LOG ANALYZER                               ║
║                    Security Log Analysis Tool v1.0                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Parse command-line arguments
    if len(sys.argv) < 2:
        # No arguments - run demo
        run_demo()
    elif sys.argv[1] == '--monitor':
        # Real-time monitoring mode
        if len(sys.argv) > 2:
            files = sys.argv[2:]
        else:
            # Default files to monitor
            files = ['/var/log/auth.log', '/var/log/syslog']
            print("[*] No files specified, using defaults:")
            for f in files:
                print(f"    - {f}")

        monitor = LogMonitor()
        try:
            monitor.start(files)
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
    elif sys.argv[1] == '--help':
        print("""
Usage:
    python log_analyzer.py                     Run demo with sample logs
    python log_analyzer.py <logfile>           Analyze specific log file
    python log_analyzer.py --monitor [files]   Real-time monitoring mode
    python log_analyzer.py --help              Show this help

Examples:
    python log_analyzer.py /var/log/auth.log
    python log_analyzer.py /var/log/apache2/access.log
    python log_analyzer.py --monitor /var/log/auth.log /var/log/syslog
        """)
    else:
        # Analyze specified file
        filepath = sys.argv[1]

        if not os.path.exists(filepath):
            print(f"[ERROR] File not found: {filepath}")
            sys.exit(1)

        analyzer = LogAnalyzer()
        report = analyzer.analyze_file(filepath)

        generator = ReportGenerator(report)
        print(generator.generate_text_report())


if __name__ == "__main__":
    main()
