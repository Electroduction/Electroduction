#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION SECURITY SYSTEM - SECURITY OPERATIONS CENTER (SOC) CORE
================================================================================
The central nervous system of the security infrastructure. This module
coordinates all security components, aggregates data from all entry points,
and orchestrates threat detection and response.

ARCHITECTURE OVERVIEW:
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY OPERATIONS CENTER                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Firewall │  │   IDS    │  │   IPS    │  │  SIEM    │  │ Honeypot │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │             │             │
│       └─────────────┴──────┬──────┴─────────────┴─────────────┘             │
│                            │                                                 │
│                    ┌───────▼───────┐                                        │
│                    │  EVENT BUS    │  (Central event routing)               │
│                    └───────┬───────┘                                        │
│                            │                                                 │
│       ┌────────────────────┼────────────────────┐                           │
│       │                    │                    │                           │
│  ┌────▼────┐         ┌─────▼─────┐        ┌─────▼─────┐                    │
│  │ Threat  │         │ Automated │        │ Dashboard │                    │
│  │ Intel   │         │ Response  │        │ & Alerts  │                    │
│  └─────────┘         └───────────┘        └───────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘

Features:
- Centralized event bus for all security events
- Real-time threat correlation and analysis
- Automated incident response orchestration
- Multi-source log aggregation
- Threat intelligence integration
- Alert management and escalation
- Audit trail and forensics support

Usage:
    from security_system.core.soc_core import SecurityOperationsCenter
    soc = SecurityOperationsCenter()
    soc.start()
================================================================================
"""

# =============================================================================
# IMPORTS - Required libraries for SOC functionality
# =============================================================================

import os                        # Operating system interface for file/process operations
import sys                       # System-specific parameters and functions
import time                      # Time-related functions for timestamps and delays
import json                      # JSON encoding/decoding for data serialization
import queue                     # Thread-safe queue for event passing between components
import threading                 # Thread-based parallelism for concurrent operations
import logging                   # Logging facility for audit trails
import hashlib                   # Hash functions for event fingerprinting
import socket                    # Network interface for communication
import signal                    # Signal handling for graceful shutdown
from datetime import datetime, timedelta  # Date/time manipulation
from typing import (             # Type hints for better code documentation
    Dict, List, Optional, Tuple, Any, Set, Callable, Union
)
from dataclasses import dataclass, field  # Decorator for creating data classes
from enum import Enum, auto      # Enumeration support for categorization
from collections import defaultdict, deque  # Specialized container types
from pathlib import Path         # Object-oriented filesystem paths
from abc import ABC, abstractmethod  # Abstract base classes for interfaces
import uuid                      # Unique identifier generation
import sqlite3                   # SQLite database for event storage
import pickle                    # Object serialization for complex data


# =============================================================================
# CONFIGURATION - System-wide settings
# =============================================================================

# Default configuration values
# These can be overridden via config file or environment variables
DEFAULT_CONFIG = {
    # Event bus settings
    'event_queue_size': 10000,       # Maximum events in queue before blocking
    'event_batch_size': 100,         # Events processed per batch
    'event_timeout': 1.0,            # Seconds to wait for events

    # Database settings
    'db_path': '/tmp/soc_events.db', # SQLite database path
    'db_retention_days': 30,         # Days to retain events

    # Alert settings
    'alert_threshold_critical': 10,   # Critical alerts trigger immediate response
    'alert_cooldown_seconds': 300,    # Minimum time between duplicate alerts

    # Network settings
    'listen_port': 5514,             # Syslog listener port
    'api_port': 8443,                # REST API port

    # Logging settings
    'log_level': 'INFO',             # Logging verbosity
    'log_file': '/tmp/soc.log',      # Log file path
}


# =============================================================================
# ENUMERATIONS - Define categories and types
# =============================================================================

class EventSeverity(Enum):
    """
    Severity levels for security events.
    Based on syslog severity levels (RFC 5424).

    Values:
        EMERGENCY (0): System is unusable
        ALERT (1): Action must be taken immediately
        CRITICAL (2): Critical conditions
        ERROR (3): Error conditions
        WARNING (4): Warning conditions
        NOTICE (5): Normal but significant condition
        INFO (6): Informational messages
        DEBUG (7): Debug-level messages
    """
    EMERGENCY = 0    # System is unusable - immediate action required
    ALERT = 1        # Action must be taken immediately
    CRITICAL = 2     # Critical conditions requiring urgent attention
    ERROR = 3        # Error conditions that may cause issues
    WARNING = 4      # Warning conditions that should be monitored
    NOTICE = 5       # Normal but significant events
    INFO = 6         # Informational messages for tracking
    DEBUG = 7        # Detailed debug information


class EventCategory(Enum):
    """
    Categories of security events for classification.
    Used to route events to appropriate handlers.

    Categories cover the main security domains:
    - Authentication/Authorization
    - Network activity
    - Malware/Threats
    - System integrity
    - Compliance
    """
    AUTHENTICATION = auto()      # Login attempts, session management
    AUTHORIZATION = auto()       # Permission checks, access control
    NETWORK = auto()             # Network traffic, connections
    MALWARE = auto()             # Malware detection, suspicious files
    INTRUSION = auto()           # Intrusion attempts, exploits
    DATA_LOSS = auto()           # Data exfiltration, leakage
    POLICY_VIOLATION = auto()    # Security policy breaches
    SYSTEM = auto()              # System health, configuration
    COMPLIANCE = auto()          # Regulatory compliance events
    AUDIT = auto()               # Audit trail events
    THREAT_INTEL = auto()        # Threat intelligence updates
    HONEYPOT = auto()            # Honeypot interactions
    CUSTOM = auto()              # User-defined events


class ResponseAction(Enum):
    """
    Automated response actions that can be taken.
    Each action has different impact levels and requirements.
    """
    LOG_ONLY = auto()            # Just log the event, no action
    ALERT = auto()               # Generate alert for human review
    BLOCK_IP = auto()            # Block source IP address
    BLOCK_USER = auto()          # Disable user account
    ISOLATE_HOST = auto()        # Network isolate affected host
    KILL_PROCESS = auto()        # Terminate malicious process
    QUARANTINE_FILE = auto()     # Move file to quarantine
    RESET_CONNECTION = auto()    # Reset network connection
    RATE_LIMIT = auto()          # Apply rate limiting
    ESCALATE = auto()            # Escalate to security team
    CUSTOM = auto()              # Custom response script


class ComponentStatus(Enum):
    """
    Status states for security components.
    Used for health monitoring and dashboard display.
    """
    INITIALIZING = auto()        # Component is starting up
    RUNNING = auto()             # Component is operational
    DEGRADED = auto()            # Component has issues but functional
    STOPPED = auto()             # Component is stopped
    ERROR = auto()               # Component has errors
    UNKNOWN = auto()             # Status cannot be determined


# =============================================================================
# DATA CLASSES - Structured data containers
# =============================================================================

@dataclass
class SecurityEvent:
    """
    Represents a single security event from any source.

    This is the fundamental data unit that flows through the SOC.
    All security components generate events in this format.

    Attributes:
        id: Unique identifier for this event (UUID)
        timestamp: When the event occurred (ISO format)
        source: Component that generated the event
        category: Event classification category
        severity: Importance/urgency level
        title: Short description of the event
        description: Detailed event information
        source_ip: IP address of event source (if applicable)
        dest_ip: IP address of event destination (if applicable)
        source_port: Source port number
        dest_port: Destination port number
        protocol: Network protocol (TCP/UDP/ICMP/etc)
        user: Username associated with event
        hostname: Host where event occurred
        raw_data: Original raw event data
        indicators: List of IOCs (Indicators of Compromise)
        tags: Classification tags for filtering
        correlation_id: ID for grouping related events
        fingerprint: Hash for deduplication
        metadata: Additional key-value data
    """
    # Required fields - must be provided
    id: str                                          # Unique event identifier
    timestamp: str                                   # ISO format timestamp
    source: str                                      # Event source component
    category: EventCategory                          # Event classification
    severity: EventSeverity                          # Severity level
    title: str                                       # Short event title

    # Optional fields with defaults
    description: str = ""                            # Detailed description
    source_ip: str = ""                              # Source IP address
    dest_ip: str = ""                                # Destination IP
    source_port: int = 0                             # Source port
    dest_port: int = 0                               # Destination port
    protocol: str = ""                               # Network protocol
    user: str = ""                                   # Associated username
    hostname: str = ""                               # Host name
    raw_data: str = ""                               # Original raw data
    indicators: List[str] = field(default_factory=list)    # IOCs
    tags: List[str] = field(default_factory=list)          # Tags
    correlation_id: str = ""                         # Correlation group ID
    fingerprint: str = ""                            # Dedup fingerprint
    metadata: Dict[str, Any] = field(default_factory=dict) # Extra data

    def __post_init__(self):
        """
        Post-initialization processing.
        Generates fingerprint if not provided.
        """
        # Generate fingerprint for deduplication if not set
        if not self.fingerprint:
            # Create fingerprint from key fields
            fp_data = f"{self.source}:{self.category.name}:{self.title}:{self.source_ip}"
            self.fingerprint = hashlib.md5(fp_data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'source': self.source,
            'category': self.category.name,
            'severity': self.severity.name,
            'title': self.title,
            'description': self.description,
            'source_ip': self.source_ip,
            'dest_ip': self.dest_ip,
            'source_port': self.source_port,
            'dest_port': self.dest_port,
            'protocol': self.protocol,
            'user': self.user,
            'hostname': self.hostname,
            'indicators': self.indicators,
            'tags': self.tags,
            'correlation_id': self.correlation_id,
            'fingerprint': self.fingerprint,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityEvent':
        """
        Create event from dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            SecurityEvent instance
        """
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            source=data.get('source', 'unknown'),
            category=EventCategory[data.get('category', 'SYSTEM')],
            severity=EventSeverity[data.get('severity', 'INFO')],
            title=data.get('title', ''),
            description=data.get('description', ''),
            source_ip=data.get('source_ip', ''),
            dest_ip=data.get('dest_ip', ''),
            source_port=data.get('source_port', 0),
            dest_port=data.get('dest_port', 0),
            protocol=data.get('protocol', ''),
            user=data.get('user', ''),
            hostname=data.get('hostname', ''),
            indicators=data.get('indicators', []),
            tags=data.get('tags', []),
            correlation_id=data.get('correlation_id', ''),
            fingerprint=data.get('fingerprint', ''),
            metadata=data.get('metadata', {})
        )


@dataclass
class Alert:
    """
    Security alert generated from event analysis.

    Alerts are created when events match threat patterns
    or exceed thresholds. They trigger notifications and
    potentially automated responses.

    Attributes:
        id: Unique alert identifier
        timestamp: When alert was generated
        title: Alert title
        description: Detailed alert description
        severity: Alert severity level
        category: Alert category
        source_events: List of event IDs that triggered alert
        source_ips: IP addresses involved
        affected_hosts: Hosts affected by the threat
        recommended_actions: Suggested response actions
        auto_response: Whether auto-response was triggered
        status: Current alert status (new/acknowledged/resolved)
        assigned_to: Security analyst assignment
        notes: Analyst notes
    """
    id: str                                          # Unique identifier
    timestamp: str                                   # Creation timestamp
    title: str                                       # Alert title
    description: str                                 # Detailed description
    severity: EventSeverity                          # Severity level
    category: EventCategory                          # Alert category
    source_events: List[str] = field(default_factory=list)   # Triggering events
    source_ips: List[str] = field(default_factory=list)      # IPs involved
    affected_hosts: List[str] = field(default_factory=list)  # Affected hosts
    recommended_actions: List[ResponseAction] = field(default_factory=list)
    auto_response: bool = False                      # Auto-response triggered
    status: str = "new"                              # Alert status
    assigned_to: str = ""                            # Analyst assignment
    notes: List[str] = field(default_factory=list)   # Analyst notes


@dataclass
class ThreatIndicator:
    """
    Indicator of Compromise (IOC) for threat matching.

    IOCs are artifacts that indicate potential malicious activity.
    They are used to detect known threats across the infrastructure.

    Types include:
    - IP addresses (malicious hosts)
    - Domain names (C2 servers)
    - File hashes (malware samples)
    - URLs (phishing/malware distribution)
    - Email addresses (phishing sources)
    """
    id: str                          # Unique identifier
    type: str                        # IOC type (ip/domain/hash/url/email)
    value: str                       # The actual indicator value
    threat_type: str                 # Type of threat (malware/phishing/c2/etc)
    confidence: int                  # Confidence score (0-100)
    severity: EventSeverity          # Threat severity
    source: str                      # Intelligence source
    first_seen: str                  # First observation timestamp
    last_seen: str                   # Last observation timestamp
    description: str = ""            # Threat description
    tags: List[str] = field(default_factory=list)    # Classification tags
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseRule:
    """
    Automated response rule configuration.

    Rules define what actions to take when specific
    conditions are met. They enable automated threat response.

    Attributes:
        id: Unique rule identifier
        name: Human-readable rule name
        description: What the rule does
        enabled: Whether rule is active
        conditions: Conditions that trigger the rule
        actions: Actions to take when triggered
        cooldown: Minimum time between triggers (seconds)
        last_triggered: Last trigger timestamp
        trigger_count: Number of times triggered
    """
    id: str                          # Unique identifier
    name: str                        # Rule name
    description: str                 # Rule description
    enabled: bool = True             # Whether rule is active
    conditions: Dict[str, Any] = field(default_factory=dict)  # Trigger conditions
    actions: List[ResponseAction] = field(default_factory=list)  # Actions to take
    cooldown: int = 300              # Cooldown period in seconds
    last_triggered: str = ""         # Last trigger time
    trigger_count: int = 0           # Total trigger count


# =============================================================================
# EVENT BUS - Central event routing system
# =============================================================================

class EventBus:
    """
    Central event bus for routing security events.

    The event bus is the backbone of the SOC. All security
    components publish events to the bus, and subscribers
    receive events based on their subscriptions.

    Features:
    - Thread-safe event queue
    - Topic-based subscriptions
    - Event persistence
    - Rate limiting
    - Dead letter queue for failed events

    Architecture:
        Publishers → Event Queue → Dispatcher → Subscribers
                                      ↓
                              Event Database
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the event bus.

        Args:
            config: Configuration dictionary
        """
        # Merge provided config with defaults
        # This allows partial configuration overrides
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        # Main event queue - thread-safe for concurrent access
        # maxsize prevents memory exhaustion under heavy load
        self.event_queue: queue.Queue = queue.Queue(
            maxsize=self.config['event_queue_size']
        )

        # Subscriber registry - maps topics to callback functions
        # Each topic can have multiple subscribers
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)

        # All-events subscribers - receive every event
        self.global_subscribers: List[Callable] = []

        # Dead letter queue for events that fail processing
        # Events here can be retried or manually reviewed
        self.dead_letter_queue: deque = deque(maxlen=1000)

        # Event statistics for monitoring
        self.stats = {
            'events_received': 0,      # Total events received
            'events_processed': 0,     # Successfully processed
            'events_failed': 0,        # Failed processing
            'events_dropped': 0,       # Dropped (queue full)
        }

        # Control flags
        self.running = False           # Bus operational state
        self.dispatcher_thread = None  # Event dispatcher thread

        # Recent event fingerprints for deduplication
        # Prevents duplicate alerts from flooding the system
        self.recent_fingerprints: deque = deque(maxlen=10000)

        # Setup logging
        self.logger = logging.getLogger('EventBus')

    def start(self):
        """
        Start the event bus dispatcher.

        Creates a background thread that continuously
        processes events from the queue and routes them
        to subscribers.
        """
        if self.running:
            self.logger.warning("Event bus already running")
            return

        self.running = True

        # Start dispatcher thread
        # daemon=True ensures thread dies with main process
        self.dispatcher_thread = threading.Thread(
            target=self._dispatch_loop,
            name="EventBusDispatcher",
            daemon=True
        )
        self.dispatcher_thread.start()

        self.logger.info("Event bus started")

    def stop(self):
        """
        Stop the event bus dispatcher.

        Gracefully shuts down the dispatcher thread
        and processes remaining events in the queue.
        """
        self.running = False

        if self.dispatcher_thread:
            # Put sentinel to unblock queue.get()
            self.event_queue.put(None)
            self.dispatcher_thread.join(timeout=5.0)

        self.logger.info(f"Event bus stopped. Stats: {self.stats}")

    def publish(self, event: SecurityEvent) -> bool:
        """
        Publish an event to the bus.

        Args:
            event: SecurityEvent to publish

        Returns:
            True if event was queued, False if dropped
        """
        try:
            # Check for duplicates using fingerprint
            if event.fingerprint in self.recent_fingerprints:
                self.logger.debug(f"Duplicate event suppressed: {event.fingerprint}")
                return True  # Not an error, just suppressed

            # Try to add to queue without blocking
            self.event_queue.put_nowait(event)
            self.stats['events_received'] += 1

            # Track fingerprint for deduplication
            self.recent_fingerprints.append(event.fingerprint)

            return True

        except queue.Full:
            # Queue is full - drop event and log
            self.stats['events_dropped'] += 1
            self.logger.warning(f"Event dropped (queue full): {event.title}")
            return False

    def subscribe(self, topic: str, callback: Callable[[SecurityEvent], None]):
        """
        Subscribe to events of a specific topic/category.

        Args:
            topic: Topic to subscribe to (category name or 'all')
            callback: Function to call with matching events
        """
        if topic == 'all':
            self.global_subscribers.append(callback)
        else:
            self.subscribers[topic].append(callback)

        self.logger.debug(f"Subscriber added for topic: {topic}")

    def unsubscribe(self, topic: str, callback: Callable):
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            callback: Callback function to remove
        """
        if topic == 'all':
            if callback in self.global_subscribers:
                self.global_subscribers.remove(callback)
        else:
            if callback in self.subscribers[topic]:
                self.subscribers[topic].remove(callback)

    def _dispatch_loop(self):
        """
        Main dispatcher loop (runs in background thread).

        Continuously pulls events from the queue and
        routes them to appropriate subscribers.
        """
        while self.running:
            try:
                # Get event from queue with timeout
                # Timeout allows checking self.running periodically
                event = self.event_queue.get(
                    timeout=self.config['event_timeout']
                )

                # Check for shutdown sentinel
                if event is None:
                    break

                # Dispatch event to subscribers
                self._dispatch_event(event)

                self.event_queue.task_done()

            except queue.Empty:
                # No events - just continue loop
                continue
            except Exception as e:
                self.logger.error(f"Dispatcher error: {e}")

    def _dispatch_event(self, event: SecurityEvent):
        """
        Dispatch a single event to all matching subscribers.

        Args:
            event: Event to dispatch
        """
        try:
            # Call global subscribers (receive all events)
            for callback in self.global_subscribers:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Global subscriber error: {e}")

            # Call topic-specific subscribers
            topic = event.category.name
            for callback in self.subscribers.get(topic, []):
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Subscriber error for {topic}: {e}")

            # Also dispatch to severity-based subscribers
            severity_topic = f"SEVERITY_{event.severity.name}"
            for callback in self.subscribers.get(severity_topic, []):
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Severity subscriber error: {e}")

            self.stats['events_processed'] += 1

        except Exception as e:
            # Move to dead letter queue for later analysis
            self.dead_letter_queue.append((event, str(e)))
            self.stats['events_failed'] += 1
            self.logger.error(f"Event dispatch failed: {e}")


# =============================================================================
# EVENT STORE - Persistent event storage
# =============================================================================

class EventStore:
    """
    Persistent storage for security events.

    Uses SQLite for simplicity and portability.
    In production, this could be replaced with:
    - Elasticsearch for full-text search
    - ClickHouse for time-series analytics
    - PostgreSQL for relational queries

    Features:
    - Event persistence
    - Efficient querying by time range
    - Automatic data retention
    - Event correlation support
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the event store.

        Args:
            db_path: Path to SQLite database file
        """
        # Use provided path or default
        self.db_path = db_path or DEFAULT_CONFIG['db_path']

        # Setup logging
        self.logger = logging.getLogger('EventStore')

        # Initialize database
        self._init_database()

    def _init_database(self):
        """
        Initialize the database schema.

        Creates tables if they don't exist.
        Uses WAL mode for better concurrent access.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Events table - stores all security events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,           -- Unique event ID
                timestamp TEXT NOT NULL,       -- ISO timestamp
                source TEXT NOT NULL,          -- Event source component
                category TEXT NOT NULL,        -- Event category
                severity INTEGER NOT NULL,     -- Severity level (0-7)
                title TEXT NOT NULL,           -- Event title
                description TEXT,              -- Detailed description
                source_ip TEXT,                -- Source IP address
                dest_ip TEXT,                  -- Destination IP
                source_port INTEGER,           -- Source port
                dest_port INTEGER,             -- Destination port
                protocol TEXT,                 -- Network protocol
                username TEXT,                 -- Associated user
                hostname TEXT,                 -- Host name
                fingerprint TEXT,              -- Dedup fingerprint
                correlation_id TEXT,           -- Correlation group
                raw_data TEXT,                 -- Original raw data
                metadata TEXT,                 -- JSON metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON events(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON events(severity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_ip ON events(source_ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprint ON events(fingerprint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_correlation ON events(correlation_id)')

        # Alerts table - stores generated alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                severity INTEGER NOT NULL,
                category TEXT NOT NULL,
                source_events TEXT,            -- JSON list of event IDs
                source_ips TEXT,               -- JSON list of IPs
                affected_hosts TEXT,           -- JSON list of hosts
                status TEXT DEFAULT 'new',
                assigned_to TEXT,
                notes TEXT,                    -- JSON list of notes
                auto_response INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Threat indicators table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indicators (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,            -- ip/domain/hash/url
                value TEXT NOT NULL UNIQUE,    -- Indicator value
                threat_type TEXT,              -- malware/phishing/c2
                confidence INTEGER,            -- 0-100
                severity INTEGER,              -- Severity level
                source TEXT,                   -- Intel source
                first_seen TEXT,
                last_seen TEXT,
                description TEXT,
                tags TEXT,                     -- JSON list
                metadata TEXT,                 -- JSON data
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicator_value ON indicators(value)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicator_type ON indicators(type)')

        # Enable WAL mode for better concurrency
        cursor.execute('PRAGMA journal_mode=WAL')

        conn.commit()
        conn.close()

        self.logger.info(f"Database initialized: {self.db_path}")

    def store_event(self, event: SecurityEvent) -> bool:
        """
        Store a security event in the database.

        Args:
            event: SecurityEvent to store

        Returns:
            True if stored successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO events
                (id, timestamp, source, category, severity, title, description,
                 source_ip, dest_ip, source_port, dest_port, protocol,
                 username, hostname, fingerprint, correlation_id, raw_data, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.id,
                event.timestamp,
                event.source,
                event.category.name,
                event.severity.value,
                event.title,
                event.description,
                event.source_ip,
                event.dest_ip,
                event.source_port,
                event.dest_port,
                event.protocol,
                event.user,
                event.hostname,
                event.fingerprint,
                event.correlation_id,
                event.raw_data,
                json.dumps(event.metadata)
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Failed to store event: {e}")
            return False

    def store_alert(self, alert: Alert) -> bool:
        """
        Store an alert in the database.

        Args:
            alert: Alert to store

        Returns:
            True if stored successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO alerts
                (id, timestamp, title, description, severity, category,
                 source_events, source_ips, affected_hosts, status,
                 assigned_to, notes, auto_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.timestamp,
                alert.title,
                alert.description,
                alert.severity.value,
                alert.category.name,
                json.dumps(alert.source_events),
                json.dumps(alert.source_ips),
                json.dumps(alert.affected_hosts),
                alert.status,
                alert.assigned_to,
                json.dumps(alert.notes),
                1 if alert.auto_response else 0
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")
            return False

    def query_events(self,
                     start_time: str = None,
                     end_time: str = None,
                     category: str = None,
                     min_severity: int = None,
                     source_ip: str = None,
                     limit: int = 1000) -> List[Dict]:
        """
        Query events with filters.

        Args:
            start_time: Start of time range (ISO format)
            end_time: End of time range (ISO format)
            category: Filter by category
            min_severity: Minimum severity level
            source_ip: Filter by source IP
            limit: Maximum results to return

        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if category:
            query += " AND category = ?"
            params.append(category)

        if min_severity is not None:
            query += " AND severity <= ?"  # Lower number = higher severity
            params.append(min_severity)

        if source_ip:
            query += " AND source_ip = ?"
            params.append(source_ip)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        return [dict(row) for row in rows]

    def get_event_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get event statistics for the specified time period.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate time threshold
        threshold = (datetime.now() - timedelta(hours=hours)).isoformat()

        stats = {}

        # Total events
        cursor.execute(
            "SELECT COUNT(*) FROM events WHERE timestamp >= ?",
            (threshold,)
        )
        stats['total_events'] = cursor.fetchone()[0]

        # Events by severity
        cursor.execute('''
            SELECT severity, COUNT(*) FROM events
            WHERE timestamp >= ? GROUP BY severity
        ''', (threshold,))
        stats['by_severity'] = dict(cursor.fetchall())

        # Events by category
        cursor.execute('''
            SELECT category, COUNT(*) FROM events
            WHERE timestamp >= ? GROUP BY category
        ''', (threshold,))
        stats['by_category'] = dict(cursor.fetchall())

        # Top source IPs
        cursor.execute('''
            SELECT source_ip, COUNT(*) as cnt FROM events
            WHERE timestamp >= ? AND source_ip != ''
            GROUP BY source_ip ORDER BY cnt DESC LIMIT 10
        ''', (threshold,))
        stats['top_source_ips'] = cursor.fetchall()

        # Events per hour
        cursor.execute('''
            SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour, COUNT(*)
            FROM events WHERE timestamp >= ?
            GROUP BY hour ORDER BY hour
        ''', (threshold,))
        stats['hourly_trend'] = cursor.fetchall()

        conn.close()

        return stats

    def cleanup_old_events(self, retention_days: int = None):
        """
        Delete events older than retention period.

        Args:
            retention_days: Days to retain (default from config)
        """
        if retention_days is None:
            retention_days = DEFAULT_CONFIG['db_retention_days']

        threshold = (datetime.now() - timedelta(days=retention_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM events WHERE timestamp < ?", (threshold,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        self.logger.info(f"Cleaned up {deleted} old events")
        return deleted


# =============================================================================
# CORRELATION ENGINE - Correlate related events
# =============================================================================

class CorrelationEngine:
    """
    Correlates related security events to identify attack patterns.

    Correlation rules link multiple events into a single incident
    based on shared attributes like IP addresses, timeframes,
    and attack signatures.

    Correlation Types:
    - Time-based: Events within a time window
    - IP-based: Events from same source/destination
    - Session-based: Events in same user session
    - Pattern-based: Events matching attack signatures
    """

    def __init__(self, event_store: EventStore):
        """
        Initialize the correlation engine.

        Args:
            event_store: EventStore instance for querying events
        """
        self.event_store = event_store
        self.logger = logging.getLogger('CorrelationEngine')

        # Active correlation windows
        # Key: correlation_id, Value: list of events
        self.active_correlations: Dict[str, List[SecurityEvent]] = defaultdict(list)

        # Correlation rules
        self.rules = self._load_default_rules()

        # Time window for correlation (seconds)
        self.correlation_window = 300  # 5 minutes

    def _load_default_rules(self) -> List[Dict]:
        """
        Load default correlation rules.

        Returns:
            List of correlation rule dictionaries
        """
        return [
            {
                'id': 'brute_force',
                'name': 'Brute Force Detection',
                'description': 'Multiple failed logins from same IP',
                'category': EventCategory.AUTHENTICATION,
                'conditions': {
                    'title_contains': 'Failed',
                    'min_count': 5,
                    'time_window': 300,
                    'group_by': 'source_ip'
                },
                'severity': EventSeverity.CRITICAL,
                'actions': [ResponseAction.BLOCK_IP, ResponseAction.ALERT]
            },
            {
                'id': 'port_scan',
                'name': 'Port Scan Detection',
                'description': 'Multiple ports accessed from same IP',
                'category': EventCategory.NETWORK,
                'conditions': {
                    'min_unique_ports': 10,
                    'time_window': 60,
                    'group_by': 'source_ip'
                },
                'severity': EventSeverity.WARNING,
                'actions': [ResponseAction.RATE_LIMIT, ResponseAction.ALERT]
            },
            {
                'id': 'data_exfil',
                'name': 'Data Exfiltration',
                'description': 'Large outbound data transfer',
                'category': EventCategory.DATA_LOSS,
                'conditions': {
                    'bytes_threshold': 100_000_000,  # 100MB
                    'time_window': 3600
                },
                'severity': EventSeverity.CRITICAL,
                'actions': [ResponseAction.ISOLATE_HOST, ResponseAction.ALERT]
            },
            {
                'id': 'lateral_movement',
                'name': 'Lateral Movement',
                'description': 'Same user accessing multiple hosts',
                'category': EventCategory.INTRUSION,
                'conditions': {
                    'min_hosts': 3,
                    'time_window': 600,
                    'group_by': 'user'
                },
                'severity': EventSeverity.ALERT,
                'actions': [ResponseAction.BLOCK_USER, ResponseAction.ESCALATE]
            }
        ]

    def correlate_event(self, event: SecurityEvent) -> Optional[str]:
        """
        Attempt to correlate an event with existing correlations.

        Args:
            event: New event to correlate

        Returns:
            Correlation ID if correlated, None otherwise
        """
        # Generate potential correlation keys
        keys = self._generate_correlation_keys(event)

        for key in keys:
            if key in self.active_correlations:
                # Check if within time window
                existing = self.active_correlations[key]
                if existing:
                    first_event_time = datetime.fromisoformat(existing[0].timestamp)
                    current_time = datetime.fromisoformat(event.timestamp)

                    if (current_time - first_event_time).total_seconds() <= self.correlation_window:
                        # Add to existing correlation
                        existing.append(event)
                        event.correlation_id = key

                        # Check if correlation triggers any rules
                        self._check_correlation_rules(key, existing)

                        return key

        # No existing correlation found - start new one
        if keys:
            key = keys[0]
            self.active_correlations[key].append(event)
            event.correlation_id = key
            return key

        return None

    def _generate_correlation_keys(self, event: SecurityEvent) -> List[str]:
        """
        Generate potential correlation keys for an event.

        Args:
            event: Event to generate keys for

        Returns:
            List of correlation key strings
        """
        keys = []

        # IP-based correlation
        if event.source_ip:
            keys.append(f"ip:{event.source_ip}")

        # User-based correlation
        if event.user:
            keys.append(f"user:{event.user}")

        # Host-based correlation
        if event.hostname:
            keys.append(f"host:{event.hostname}")

        # Category + source IP
        if event.source_ip:
            keys.append(f"{event.category.name}:{event.source_ip}")

        return keys

    def _check_correlation_rules(self, correlation_id: str, events: List[SecurityEvent]):
        """
        Check if correlated events trigger any rules.

        Args:
            correlation_id: Correlation group ID
            events: List of correlated events
        """
        for rule in self.rules:
            conditions = rule.get('conditions', {})

            # Check minimum count
            min_count = conditions.get('min_count', 0)
            if len(events) >= min_count:
                self.logger.info(
                    f"Correlation rule triggered: {rule['name']} "
                    f"({len(events)} events)"
                )
                # Rule actions would be triggered here

    def cleanup_old_correlations(self):
        """
        Remove old correlation groups that have expired.
        """
        now = datetime.now()
        expired = []

        for key, events in self.active_correlations.items():
            if events:
                last_time = datetime.fromisoformat(events[-1].timestamp)
                if (now - last_time).total_seconds() > self.correlation_window * 2:
                    expired.append(key)

        for key in expired:
            del self.active_correlations[key]

        if expired:
            self.logger.debug(f"Cleaned up {len(expired)} expired correlations")


# =============================================================================
# SECURITY OPERATIONS CENTER - Main orchestrator
# =============================================================================

class SecurityOperationsCenter:
    """
    Main Security Operations Center class.

    Orchestrates all security components and provides
    the central management interface for the security system.

    Components:
    - Event Bus: Central event routing
    - Event Store: Persistent storage
    - Correlation Engine: Event correlation
    - Response Engine: Automated response (loaded separately)

    The SOC provides:
    - Component lifecycle management
    - Event flow coordination
    - Health monitoring
    - Configuration management
    - API endpoints
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Security Operations Center.

        Args:
            config: Configuration dictionary (merges with defaults)
        """
        # Merge configuration with defaults
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger('SOC')

        # Initialize core components
        self.logger.info("Initializing Security Operations Center...")

        # Event bus - central event routing
        self.event_bus = EventBus(self.config)

        # Event store - persistent storage
        self.event_store = EventStore(self.config.get('db_path'))

        # Correlation engine - event correlation
        self.correlation_engine = CorrelationEngine(self.event_store)

        # Component registry - tracks all security components
        self.components: Dict[str, Dict[str, Any]] = {}

        # Alert handlers - functions to call on new alerts
        self.alert_handlers: List[Callable[[Alert], None]] = []

        # Statistics
        self.stats = {
            'start_time': None,
            'events_total': 0,
            'alerts_total': 0,
            'responses_total': 0,
        }

        # Running state
        self.running = False

        # Subscribe to all events for storage
        self.event_bus.subscribe('all', self._handle_event)

        self.logger.info("SOC initialization complete")

    def _setup_logging(self):
        """
        Configure logging for the SOC.
        """
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        log_file = self.config.get('log_file')

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            handlers=[
                logging.StreamHandler(),  # Console output
                logging.FileHandler(log_file) if log_file else logging.NullHandler()
            ]
        )

    def start(self):
        """
        Start the Security Operations Center.

        Starts all components and begins event processing.
        """
        if self.running:
            self.logger.warning("SOC already running")
            return

        self.logger.info("Starting Security Operations Center...")

        # Record start time
        self.stats['start_time'] = datetime.now().isoformat()

        # Start event bus
        self.event_bus.start()

        # Set running flag
        self.running = True

        # Start component health monitoring
        self._start_health_monitor()

        self.logger.info("SOC started successfully")

        # Log startup event
        self.publish_event(SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source='SOC',
            category=EventCategory.SYSTEM,
            severity=EventSeverity.INFO,
            title='Security Operations Center started',
            description='All components initialized successfully'
        ))

    def stop(self):
        """
        Stop the Security Operations Center.

        Gracefully shuts down all components.
        """
        if not self.running:
            return

        self.logger.info("Stopping Security Operations Center...")

        # Log shutdown event
        self.publish_event(SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source='SOC',
            category=EventCategory.SYSTEM,
            severity=EventSeverity.INFO,
            title='Security Operations Center stopping',
            description='Initiating graceful shutdown'
        ))

        # Stop running flag
        self.running = False

        # Stop event bus
        self.event_bus.stop()

        # Cleanup old data
        self.event_store.cleanup_old_events()

        self.logger.info("SOC stopped")

    def publish_event(self, event: SecurityEvent):
        """
        Publish a security event to the SOC.

        Args:
            event: SecurityEvent to publish
        """
        # Try to correlate event
        self.correlation_engine.correlate_event(event)

        # Publish to event bus
        self.event_bus.publish(event)

        # Update stats
        self.stats['events_total'] += 1

    def _handle_event(self, event: SecurityEvent):
        """
        Handle incoming security event.

        Called for every event that passes through the bus.

        Args:
            event: Event to handle
        """
        # Store event in database
        self.event_store.store_event(event)

        # Check if event should generate alert
        if event.severity.value <= EventSeverity.WARNING.value:
            self._generate_alert(event)

    def _generate_alert(self, event: SecurityEvent):
        """
        Generate an alert from a security event.

        Args:
            event: Event that triggered the alert
        """
        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            title=f"Alert: {event.title}",
            description=event.description,
            severity=event.severity,
            category=event.category,
            source_events=[event.id],
            source_ips=[event.source_ip] if event.source_ip else []
        )

        # Store alert
        self.event_store.store_alert(alert)

        # Update stats
        self.stats['alerts_total'] += 1

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")

        self.logger.warning(f"Alert generated: {alert.title}")

    def register_component(self, name: str, component: Any):
        """
        Register a security component with the SOC.

        Args:
            name: Component name
            component: Component instance
        """
        self.components[name] = {
            'instance': component,
            'status': ComponentStatus.INITIALIZING,
            'registered_at': datetime.now().isoformat(),
            'last_heartbeat': datetime.now().isoformat()
        }

        self.logger.info(f"Component registered: {name}")

    def update_component_status(self, name: str, status: ComponentStatus):
        """
        Update a component's status.

        Args:
            name: Component name
            status: New status
        """
        if name in self.components:
            self.components[name]['status'] = status
            self.components[name]['last_heartbeat'] = datetime.now().isoformat()

    def _start_health_monitor(self):
        """
        Start background health monitoring thread.
        """
        def monitor_loop():
            while self.running:
                # Cleanup old correlations
                self.correlation_engine.cleanup_old_correlations()

                # Check component health
                for name, info in self.components.items():
                    last_hb = datetime.fromisoformat(info['last_heartbeat'])
                    if (datetime.now() - last_hb).total_seconds() > 60:
                        if info['status'] != ComponentStatus.STOPPED:
                            info['status'] = ComponentStatus.UNKNOWN
                            self.logger.warning(f"Component {name} not responding")

                time.sleep(30)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """
        Add an alert handler callback.

        Args:
            handler: Function to call on new alerts
        """
        self.alert_handlers.append(handler)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current SOC status.

        Returns:
            Status dictionary with component states and statistics
        """
        return {
            'running': self.running,
            'start_time': self.stats['start_time'],
            'uptime_seconds': (
                datetime.now() - datetime.fromisoformat(self.stats['start_time'])
            ).total_seconds() if self.stats['start_time'] else 0,
            'stats': self.stats,
            'event_bus_stats': self.event_bus.stats,
            'components': {
                name: {
                    'status': info['status'].name,
                    'last_heartbeat': info['last_heartbeat']
                }
                for name, info in self.components.items()
            }
        }

    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """
        Get recent security events.

        Args:
            limit: Maximum events to return

        Returns:
            List of event dictionaries
        """
        return self.event_store.query_events(limit=limit)

    def get_event_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get event statistics for the specified period.

        Args:
            hours: Hours to analyze

        Returns:
            Statistics dictionary
        """
        return self.event_store.get_event_stats(hours)


# =============================================================================
# DEMO AND TESTING
# =============================================================================

def run_demo():
    """
    Demonstrate the SOC functionality.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ELECTRODUCTION SECURITY OPERATIONS CENTER                       ║
║                           Core System Demo                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Create SOC instance
    print("[*] Initializing Security Operations Center...")
    soc = SecurityOperationsCenter()

    # Add alert handler
    def alert_handler(alert: Alert):
        print(f"[ALERT] {alert.severity.name}: {alert.title}")

    soc.add_alert_handler(alert_handler)

    # Start SOC
    print("[*] Starting SOC...")
    soc.start()

    # Generate some test events
    print("\n[*] Generating test security events...")

    test_events = [
        SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source='Firewall',
            category=EventCategory.NETWORK,
            severity=EventSeverity.INFO,
            title='Connection established',
            source_ip='192.168.1.100',
            dest_ip='10.0.0.1',
            dest_port=443,
            protocol='TCP'
        ),
        SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source='IDS',
            category=EventCategory.INTRUSION,
            severity=EventSeverity.WARNING,
            title='Port scan detected',
            source_ip='10.0.0.50',
            description='Multiple ports probed from single source'
        ),
        SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source='Auth',
            category=EventCategory.AUTHENTICATION,
            severity=EventSeverity.CRITICAL,
            title='Failed login attempt',
            source_ip='203.0.113.100',
            user='admin',
            description='5 failed password attempts'
        ),
    ]

    for event in test_events:
        soc.publish_event(event)
        print(f"    Published: {event.title}")
        time.sleep(0.1)

    # Wait for processing
    time.sleep(1)

    # Get statistics
    print("\n[*] SOC Status:")
    status = soc.get_status()
    print(f"    Running: {status['running']}")
    print(f"    Events processed: {status['event_bus_stats']['events_processed']}")
    print(f"    Alerts generated: {status['stats']['alerts_total']}")

    # Get event statistics
    print("\n[*] Event Statistics (last 24h):")
    stats = soc.get_event_statistics(24)
    print(f"    Total events: {stats['total_events']}")
    print(f"    By category: {stats['by_category']}")

    # Cleanup
    print("\n[*] Stopping SOC...")
    soc.stop()

    print("\n[*] Demo completed!")


if __name__ == "__main__":
    run_demo()
