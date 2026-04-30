#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION SECURITY SYSTEM - THREAT INTELLIGENCE MODULE
================================================================================
Aggregates and manages threat intelligence data from multiple sources.
Provides IOC (Indicators of Compromise) matching and threat enrichment.

THREAT INTELLIGENCE SOURCES:
1. Internal: Events from IDS/IPS, honeypots, and security logs
2. External: Open-source threat feeds (abuse.ch, emergingthreats, etc.)
3. Custom: User-defined threat indicators

IOC TYPES SUPPORTED:
- IP addresses (IPv4/IPv6)
- Domain names
- URLs
- File hashes (MD5, SHA1, SHA256)
- Email addresses
- SSL certificate fingerprints
- User agents
- JA3/JA3S fingerprints

FEATURES:
- Multi-source feed aggregation
- IOC deduplication and scoring
- Automatic feed updates
- IOC aging and expiration
- Threat enrichment with context
- Integration with IPS for blocking

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                    THREAT INTELLIGENCE                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  Abuse.ch │  │ Emerging  │  │  Custom   │  │ Internal  │    │
│  │   Feeds   │  │  Threats  │  │   IOCs    │  │  Events   │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        │              │              │              │           │
│        └──────────────┴──────┬───────┴──────────────┘           │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   IOC Database    │                        │
│                    │   (Normalized)    │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│        ┌─────────────────────┼─────────────────────┐            │
│        ▼                     ▼                     ▼            │
│  ┌───────────┐        ┌───────────┐        ┌───────────┐       │
│  │   Match   │        │  Enrich   │        │   Export  │       │
│  │   Engine  │        │  Context  │        │   Share   │       │
│  └───────────┘        └───────────┘        └───────────┘       │
└─────────────────────────────────────────────────────────────────┘

Usage:
    from security_system.components.threat_intelligence import ThreatIntelligence
    ti = ThreatIntelligence()
    ti.start()
    result = ti.check_ip("1.2.3.4")
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
import sqlite3                   # SQLite database
import re                        # Regular expressions
import urllib.request            # URL fetching
import urllib.error              # URL error handling
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import ipaddress                 # IP address manipulation


# =============================================================================
# ENUMERATIONS
# =============================================================================

class IOCType(Enum):
    """
    Types of Indicators of Compromise.
    Each type has specific validation and matching rules.
    """
    IP_ADDRESS = "ip"            # IPv4 or IPv6 address
    DOMAIN = "domain"            # Domain name
    URL = "url"                  # Full URL
    HASH_MD5 = "md5"             # MD5 file hash
    HASH_SHA1 = "sha1"           # SHA1 file hash
    HASH_SHA256 = "sha256"       # SHA256 file hash
    EMAIL = "email"              # Email address
    USER_AGENT = "useragent"     # Browser user agent
    FILENAME = "filename"        # Malicious filename
    REGISTRY = "registry"        # Windows registry key
    SSL_CERT = "ssl"             # SSL certificate hash
    JA3 = "ja3"                  # TLS fingerprint


class ThreatType(Enum):
    """
    Categories of threats.
    Used to classify and prioritize indicators.
    """
    MALWARE = "malware"          # Malware distribution/C2
    BOTNET = "botnet"            # Botnet infrastructure
    RANSOMWARE = "ransomware"    # Ransomware
    PHISHING = "phishing"        # Phishing sites
    SPAM = "spam"                # Spam sources
    SCANNER = "scanner"          # Scanning/reconnaissance
    EXPLOIT = "exploit"          # Exploit kit
    APT = "apt"                  # Advanced Persistent Threat
    BRUTEFORCE = "bruteforce"    # Brute force sources
    TOR = "tor"                  # Tor exit nodes
    PROXY = "proxy"              # Anonymous proxies
    VPN = "vpn"                  # Known VPN endpoints
    MINER = "miner"              # Cryptominer
    UNKNOWN = "unknown"          # Unknown threat


class ConfidenceLevel(Enum):
    """
    Confidence levels for threat indicators.
    Higher confidence = more reliable indicator.
    """
    LOW = 25           # Possibly malicious
    MEDIUM = 50        # Likely malicious
    HIGH = 75          # Confirmed malicious
    CONFIRMED = 100    # Verified by multiple sources


class FeedType(Enum):
    """
    Types of threat intelligence feeds.
    """
    IP_BLOCKLIST = "ip_blocklist"
    DOMAIN_BLOCKLIST = "domain_blocklist"
    URL_BLOCKLIST = "url_blocklist"
    HASH_BLOCKLIST = "hash_blocklist"
    COMBINED = "combined"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ThreatIndicator:
    """
    A single threat indicator (IOC).

    Attributes:
        id: Unique identifier
        ioc_type: Type of indicator
        value: The indicator value
        threat_type: Category of threat
        confidence: Confidence score (0-100)
        severity: Threat severity (1-10)
        source: Intelligence source
        first_seen: First observation
        last_seen: Last observation
        expires: Expiration timestamp
        description: Threat description
        tags: Classification tags
        metadata: Additional data
        hit_count: Number of matches
    """
    id: str                                      # Unique ID
    ioc_type: IOCType                            # Indicator type
    value: str                                   # Indicator value
    threat_type: ThreatType                      # Threat category
    confidence: int = 50                         # 0-100
    severity: int = 5                            # 1-10
    source: str = "internal"                     # Intel source
    first_seen: str = ""                         # First seen
    last_seen: str = ""                          # Last seen
    expires: str = ""                            # Expiration
    description: str = ""                        # Description
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    hit_count: int = 0                           # Match count

    def __post_init__(self):
        """Initialize timestamps if not set."""
        now = datetime.now().isoformat()
        if not self.first_seen:
            self.first_seen = now
        if not self.last_seen:
            self.last_seen = now
        if not self.id:
            self.id = hashlib.md5(
                f"{self.ioc_type.value}:{self.value}".encode()
            ).hexdigest()[:16]

    def is_expired(self) -> bool:
        """Check if indicator has expired."""
        if not self.expires:
            return False
        return datetime.fromisoformat(self.expires) < datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'type': self.ioc_type.value,
            'value': self.value,
            'threat_type': self.threat_type.value,
            'confidence': self.confidence,
            'severity': self.severity,
            'source': self.source,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'expires': self.expires,
            'description': self.description,
            'tags': self.tags,
            'hit_count': self.hit_count
        }


@dataclass
class ThreatFeed:
    """
    Configuration for a threat intelligence feed.

    Attributes:
        id: Unique feed identifier
        name: Human-readable name
        url: Feed URL
        feed_type: Type of feed
        format: Data format (csv/json/txt)
        update_interval: Hours between updates
        enabled: Whether feed is active
        last_update: Last successful update
        ioc_count: Number of IOCs from this feed
    """
    id: str                          # Feed ID
    name: str                        # Feed name
    url: str                         # Feed URL
    feed_type: FeedType              # Feed type
    format: str = "txt"              # csv/json/txt
    update_interval: int = 24        # Hours
    enabled: bool = True             # Active
    last_update: str = ""            # Last update
    ioc_count: int = 0               # IOC count


@dataclass
class ThreatMatch:
    """
    Result of a threat lookup.

    Attributes:
        matched: Whether indicator was found
        indicator: Matching indicator (if found)
        context: Additional context
        recommendations: Suggested actions
    """
    matched: bool                    # Was found
    indicator: Optional[ThreatIndicator] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# THREAT INTELLIGENCE DATABASE
# =============================================================================

class ThreatDatabase:
    """
    SQLite-backed database for threat indicators.

    Provides persistent storage, efficient lookups,
    and automatic expiration handling.
    """

    def __init__(self, db_path: str = "/tmp/threat_intel.db"):
        """
        Initialize the threat database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger('ThreatDB')
        self._init_database()

        # In-memory cache for fast lookups
        self._cache: Dict[str, ThreatIndicator] = {}
        self._cache_loaded = False

    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # IOC table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indicators (
                id TEXT PRIMARY KEY,
                ioc_type TEXT NOT NULL,
                value TEXT NOT NULL,
                threat_type TEXT,
                confidence INTEGER DEFAULT 50,
                severity INTEGER DEFAULT 5,
                source TEXT,
                first_seen TEXT,
                last_seen TEXT,
                expires TEXT,
                description TEXT,
                tags TEXT,
                metadata TEXT,
                hit_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ioc_type, value)
            )
        ''')

        # Indexes for fast lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_value ON indicators(value)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON indicators(ioc_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_threat ON indicators(threat_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires ON indicators(expires)')

        # Feed tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feeds (
                id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                feed_type TEXT,
                format TEXT,
                update_interval INTEGER,
                enabled INTEGER DEFAULT 1,
                last_update TEXT,
                ioc_count INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

        self.logger.info(f"Database initialized: {self.db_path}")

    def add_indicator(self, indicator: ThreatIndicator) -> bool:
        """
        Add or update an indicator.

        Args:
            indicator: Indicator to add

        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO indicators
                (id, ioc_type, value, threat_type, confidence, severity,
                 source, first_seen, last_seen, expires, description,
                 tags, metadata, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                indicator.id,
                indicator.ioc_type.value,
                indicator.value.lower(),  # Normalize to lowercase
                indicator.threat_type.value,
                indicator.confidence,
                indicator.severity,
                indicator.source,
                indicator.first_seen,
                indicator.last_seen,
                indicator.expires,
                indicator.description,
                json.dumps(indicator.tags),
                json.dumps(indicator.metadata),
                indicator.hit_count
            ))

            conn.commit()
            conn.close()

            # Update cache
            self._cache[indicator.value.lower()] = indicator

            return True

        except Exception as e:
            self.logger.error(f"Failed to add indicator: {e}")
            return False

    def lookup(self, value: str, ioc_type: IOCType = None) -> Optional[ThreatIndicator]:
        """
        Look up a value in the database.

        Args:
            value: Value to look up
            ioc_type: Optional type filter

        Returns:
            ThreatIndicator if found
        """
        value = value.lower()

        # Check cache first
        if value in self._cache:
            indicator = self._cache[value]
            if not indicator.is_expired():
                # Update hit count
                indicator.hit_count += 1
                indicator.last_seen = datetime.now().isoformat()
                return indicator

        # Query database
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if ioc_type:
                cursor.execute(
                    'SELECT * FROM indicators WHERE value = ? AND ioc_type = ?',
                    (value, ioc_type.value)
                )
            else:
                cursor.execute('SELECT * FROM indicators WHERE value = ?', (value,))

            row = cursor.fetchone()
            conn.close()

            if row:
                indicator = self._row_to_indicator(row)
                if not indicator.is_expired():
                    # Update cache and hit count
                    self._cache[value] = indicator
                    self._update_hit_count(indicator.id)
                    return indicator

        except Exception as e:
            self.logger.error(f"Lookup error: {e}")

        return None

    def _row_to_indicator(self, row: sqlite3.Row) -> ThreatIndicator:
        """Convert database row to ThreatIndicator."""
        return ThreatIndicator(
            id=row['id'],
            ioc_type=IOCType(row['ioc_type']),
            value=row['value'],
            threat_type=ThreatType(row['threat_type']) if row['threat_type'] else ThreatType.UNKNOWN,
            confidence=row['confidence'],
            severity=row['severity'],
            source=row['source'],
            first_seen=row['first_seen'],
            last_seen=row['last_seen'],
            expires=row['expires'],
            description=row['description'] or "",
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            hit_count=row['hit_count']
        )

    def _update_hit_count(self, indicator_id: str):
        """Update hit count for an indicator."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE indicators SET hit_count = hit_count + 1, last_seen = ? WHERE id = ?',
                (datetime.now().isoformat(), indicator_id)
            )
            conn.commit()
            conn.close()
        except:
            pass

    def get_all_indicators(self, ioc_type: IOCType = None,
                           limit: int = 10000) -> List[ThreatIndicator]:
        """
        Get all indicators, optionally filtered by type.

        Args:
            ioc_type: Optional type filter
            limit: Maximum results

        Returns:
            List of ThreatIndicator
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if ioc_type:
                cursor.execute(
                    'SELECT * FROM indicators WHERE ioc_type = ? ORDER BY confidence DESC LIMIT ?',
                    (ioc_type.value, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM indicators ORDER BY confidence DESC LIMIT ?',
                    (limit,)
                )

            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_indicator(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Query error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {}

            # Total count
            cursor.execute('SELECT COUNT(*) FROM indicators')
            stats['total_indicators'] = cursor.fetchone()[0]

            # By type
            cursor.execute('''
                SELECT ioc_type, COUNT(*) FROM indicators GROUP BY ioc_type
            ''')
            stats['by_type'] = dict(cursor.fetchall())

            # By threat type
            cursor.execute('''
                SELECT threat_type, COUNT(*) FROM indicators GROUP BY threat_type
            ''')
            stats['by_threat'] = dict(cursor.fetchall())

            # Top hit indicators
            cursor.execute('''
                SELECT value, hit_count FROM indicators ORDER BY hit_count DESC LIMIT 10
            ''')
            stats['top_hits'] = cursor.fetchall()

            conn.close()
            return stats

        except Exception as e:
            self.logger.error(f"Stats error: {e}")
            return {}

    def cleanup_expired(self) -> int:
        """Remove expired indicators."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()
            cursor.execute(
                "DELETE FROM indicators WHERE expires != '' AND expires < ?",
                (now,)
            )
            deleted = cursor.rowcount

            conn.commit()
            conn.close()

            self.logger.info(f"Cleaned up {deleted} expired indicators")
            return deleted

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            return 0

    def load_cache(self):
        """Load high-confidence indicators into memory cache."""
        indicators = self.get_all_indicators(limit=50000)
        for ind in indicators:
            if not ind.is_expired():
                self._cache[ind.value.lower()] = ind
        self._cache_loaded = True
        self.logger.info(f"Loaded {len(self._cache)} indicators into cache")


# =============================================================================
# FEED MANAGER - Manage threat intelligence feeds
# =============================================================================

class FeedManager:
    """
    Manages threat intelligence feeds.

    Handles feed configuration, updates, and parsing.
    Supports multiple feed formats.
    """

    def __init__(self, database: ThreatDatabase):
        """
        Initialize feed manager.

        Args:
            database: ThreatDatabase instance
        """
        self.database = database
        self.logger = logging.getLogger('FeedManager')

        # Default feeds (open source)
        self.default_feeds = [
            ThreatFeed(
                id="abuse_ch_feodo",
                name="Abuse.ch Feodo Tracker",
                url="https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
                feed_type=FeedType.IP_BLOCKLIST,
                format="txt"
            ),
            ThreatFeed(
                id="abuse_ch_ssl",
                name="Abuse.ch SSL Blacklist",
                url="https://sslbl.abuse.ch/blacklist/sslipblacklist.txt",
                feed_type=FeedType.IP_BLOCKLIST,
                format="txt"
            ),
            ThreatFeed(
                id="emerging_threats_compromised",
                name="ET Compromised IPs",
                url="https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
                feed_type=FeedType.IP_BLOCKLIST,
                format="txt"
            ),
            ThreatFeed(
                id="blocklist_de",
                name="Blocklist.de All",
                url="https://lists.blocklist.de/lists/all.txt",
                feed_type=FeedType.IP_BLOCKLIST,
                format="txt"
            ),
            ThreatFeed(
                id="cinsscore_ci_army",
                name="CI Army Badguys",
                url="https://cinsscore.com/list/ci-badguys.txt",
                feed_type=FeedType.IP_BLOCKLIST,
                format="txt"
            ),
        ]

        # Active feeds
        self.feeds: Dict[str, ThreatFeed] = {f.id: f for f in self.default_feeds}

    def update_feed(self, feed: ThreatFeed) -> Tuple[int, int]:
        """
        Update a single feed.

        Args:
            feed: Feed to update

        Returns:
            Tuple of (added_count, error_count)
        """
        self.logger.info(f"Updating feed: {feed.name}")
        added = 0
        errors = 0

        try:
            # Fetch feed content
            req = urllib.request.Request(
                feed.url,
                headers={'User-Agent': 'ThreatIntel/1.0'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')

            # Parse based on format
            if feed.format == "txt":
                lines = content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#') or line.startswith(';'):
                        continue

                    # Try to extract IP
                    ip = self._extract_ip(line)
                    if ip:
                        indicator = ThreatIndicator(
                            id="",
                            ioc_type=IOCType.IP_ADDRESS,
                            value=ip,
                            threat_type=self._infer_threat_type(feed.name),
                            confidence=70,
                            severity=6,
                            source=feed.name,
                            expires=(datetime.now() + timedelta(days=7)).isoformat()
                        )
                        if self.database.add_indicator(indicator):
                            added += 1
                        else:
                            errors += 1

            elif feed.format == "csv":
                # CSV parsing (comma or other delimiter)
                lines = content.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split(',')
                    if parts:
                        ip = self._extract_ip(parts[0])
                        if ip:
                            indicator = ThreatIndicator(
                                id="",
                                ioc_type=IOCType.IP_ADDRESS,
                                value=ip,
                                threat_type=self._infer_threat_type(feed.name),
                                confidence=70,
                                source=feed.name,
                                expires=(datetime.now() + timedelta(days=7)).isoformat()
                            )
                            if self.database.add_indicator(indicator):
                                added += 1

            elif feed.format == "json":
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            value = item.get('ip') or item.get('indicator') or item.get('value')
                            if value:
                                indicator = ThreatIndicator(
                                    id="",
                                    ioc_type=IOCType.IP_ADDRESS,
                                    value=str(value),
                                    threat_type=ThreatType.UNKNOWN,
                                    confidence=70,
                                    source=feed.name
                                )
                                if self.database.add_indicator(indicator):
                                    added += 1

            # Update feed status
            feed.last_update = datetime.now().isoformat()
            feed.ioc_count = added

            self.logger.info(f"Feed {feed.name}: Added {added}, Errors {errors}")

        except urllib.error.URLError as e:
            self.logger.error(f"Feed fetch error: {e}")
        except Exception as e:
            self.logger.error(f"Feed update error: {e}")

        return (added, errors)

    def update_all_feeds(self) -> Dict[str, Tuple[int, int]]:
        """
        Update all enabled feeds.

        Returns:
            Dict mapping feed_id to (added, errors) tuples
        """
        results = {}
        for feed_id, feed in self.feeds.items():
            if feed.enabled:
                results[feed_id] = self.update_feed(feed)
        return results

    def _extract_ip(self, text: str) -> Optional[str]:
        """Extract IP address from text."""
        # IPv4 pattern
        ipv4_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        match = re.search(ipv4_pattern, text)
        if match:
            ip = match.group(1)
            try:
                # Validate IP
                ipaddress.ip_address(ip)
                return ip
            except:
                pass
        return None

    def _infer_threat_type(self, feed_name: str) -> ThreatType:
        """Infer threat type from feed name."""
        name_lower = feed_name.lower()
        if 'malware' in name_lower or 'feodo' in name_lower:
            return ThreatType.MALWARE
        elif 'botnet' in name_lower:
            return ThreatType.BOTNET
        elif 'phishing' in name_lower:
            return ThreatType.PHISHING
        elif 'spam' in name_lower:
            return ThreatType.SPAM
        elif 'tor' in name_lower:
            return ThreatType.TOR
        elif 'brute' in name_lower:
            return ThreatType.BRUTEFORCE
        else:
            return ThreatType.UNKNOWN


# =============================================================================
# THREAT INTELLIGENCE MAIN CLASS
# =============================================================================

class ThreatIntelligence:
    """
    Main Threat Intelligence class.

    Coordinates database, feeds, and provides lookup interface.
    Integrates with SOC and IPS for threat detection.
    """

    def __init__(self, soc=None, config: Dict[str, Any] = None):
        """
        Initialize Threat Intelligence.

        Args:
            soc: SecurityOperationsCenter instance
            config: Configuration dictionary
        """
        self.config = config or {}
        self.soc = soc
        self.logger = logging.getLogger('ThreatIntel')

        # Database path
        db_path = self.config.get('db_path', '/tmp/threat_intel.db')

        # Initialize components
        self.database = ThreatDatabase(db_path)
        self.feed_manager = FeedManager(self.database)

        # Statistics
        self.stats = {
            'lookups': 0,
            'matches': 0,
            'feeds_updated': 0,
        }

        # Running state
        self.running = False
        self._update_thread = None

        # Load built-in indicators
        self._load_builtin_indicators()

        self.logger.info("Threat Intelligence initialized")

    def _load_builtin_indicators(self):
        """Load built-in threat indicators."""
        # Known malicious IPs (example)
        builtin_indicators = [
            ThreatIndicator(
                id="", ioc_type=IOCType.IP_ADDRESS,
                value="185.220.101.1",
                threat_type=ThreatType.TOR,
                confidence=90, severity=3,
                source="builtin",
                description="Known Tor exit node"
            ),
            ThreatIndicator(
                id="", ioc_type=IOCType.DOMAIN,
                value="evil.com",
                threat_type=ThreatType.MALWARE,
                confidence=100, severity=10,
                source="builtin",
                description="Example malicious domain"
            ),
            # Known scanner user agents
            ThreatIndicator(
                id="", ioc_type=IOCType.USER_AGENT,
                value="sqlmap",
                threat_type=ThreatType.SCANNER,
                confidence=100, severity=8,
                source="builtin",
                description="SQLMap scanner"
            ),
            ThreatIndicator(
                id="", ioc_type=IOCType.USER_AGENT,
                value="nikto",
                threat_type=ThreatType.SCANNER,
                confidence=100, severity=7,
                source="builtin",
                description="Nikto web scanner"
            ),
            ThreatIndicator(
                id="", ioc_type=IOCType.USER_AGENT,
                value="nmap",
                threat_type=ThreatType.SCANNER,
                confidence=100, severity=6,
                source="builtin",
                description="Nmap scanner"
            ),
        ]

        for ind in builtin_indicators:
            self.database.add_indicator(ind)

        self.logger.info(f"Loaded {len(builtin_indicators)} built-in indicators")

    def start(self):
        """Start the Threat Intelligence service."""
        self.running = True

        # Load cache
        self.database.load_cache()

        # Start periodic update thread
        self._update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self._update_thread.start()

        # Register with SOC
        if self.soc:
            self.soc.register_component('ThreatIntel', self)

        self.logger.info("Threat Intelligence started")

    def stop(self):
        """Stop the service."""
        self.running = False
        if self._update_thread:
            self._update_thread.join(timeout=5.0)
        self.logger.info("Threat Intelligence stopped")

    def _update_loop(self):
        """Background thread for periodic feed updates."""
        # Initial update
        time.sleep(5)
        self._update_feeds()

        while self.running:
            # Update feeds every 6 hours
            time.sleep(6 * 3600)
            if self.running:
                self._update_feeds()

    def _update_feeds(self):
        """Update all threat feeds."""
        self.logger.info("Updating threat feeds...")
        results = self.feed_manager.update_all_feeds()

        total_added = sum(r[0] for r in results.values())
        self.stats['feeds_updated'] += 1

        self.logger.info(f"Feed update complete: {total_added} indicators added")

        # Cleanup expired
        self.database.cleanup_expired()

    def check_ip(self, ip: str) -> ThreatMatch:
        """
        Check if an IP is in threat intelligence.

        Args:
            ip: IP address to check

        Returns:
            ThreatMatch with results
        """
        self.stats['lookups'] += 1

        indicator = self.database.lookup(ip, IOCType.IP_ADDRESS)

        if indicator:
            self.stats['matches'] += 1
            return ThreatMatch(
                matched=True,
                indicator=indicator,
                context={
                    'threat_type': indicator.threat_type.value,
                    'confidence': indicator.confidence,
                    'severity': indicator.severity,
                    'source': indicator.source
                },
                recommendations=self._get_recommendations(indicator)
            )

        return ThreatMatch(matched=False)

    def check_domain(self, domain: str) -> ThreatMatch:
        """
        Check if a domain is in threat intelligence.

        Args:
            domain: Domain to check

        Returns:
            ThreatMatch with results
        """
        self.stats['lookups'] += 1

        indicator = self.database.lookup(domain, IOCType.DOMAIN)

        if indicator:
            self.stats['matches'] += 1
            return ThreatMatch(
                matched=True,
                indicator=indicator,
                context={
                    'threat_type': indicator.threat_type.value,
                    'confidence': indicator.confidence
                },
                recommendations=self._get_recommendations(indicator)
            )

        return ThreatMatch(matched=False)

    def check_hash(self, file_hash: str) -> ThreatMatch:
        """
        Check if a file hash is in threat intelligence.

        Args:
            file_hash: File hash (MD5/SHA1/SHA256)

        Returns:
            ThreatMatch with results
        """
        self.stats['lookups'] += 1

        # Determine hash type by length
        hash_len = len(file_hash)
        if hash_len == 32:
            ioc_type = IOCType.HASH_MD5
        elif hash_len == 40:
            ioc_type = IOCType.HASH_SHA1
        elif hash_len == 64:
            ioc_type = IOCType.HASH_SHA256
        else:
            ioc_type = None

        indicator = self.database.lookup(file_hash, ioc_type)

        if indicator:
            self.stats['matches'] += 1
            return ThreatMatch(
                matched=True,
                indicator=indicator,
                context={'hash_type': ioc_type.value if ioc_type else 'unknown'},
                recommendations=self._get_recommendations(indicator)
            )

        return ThreatMatch(matched=False)

    def check_user_agent(self, user_agent: str) -> ThreatMatch:
        """
        Check if user agent indicates a scanner/attacker.

        Args:
            user_agent: User agent string

        Returns:
            ThreatMatch with results
        """
        self.stats['lookups'] += 1

        # Check for known scanner patterns
        ua_lower = user_agent.lower()
        for indicator in self.database.get_all_indicators(IOCType.USER_AGENT, limit=1000):
            if indicator.value.lower() in ua_lower:
                self.stats['matches'] += 1
                return ThreatMatch(
                    matched=True,
                    indicator=indicator,
                    context={'matched_pattern': indicator.value},
                    recommendations=self._get_recommendations(indicator)
                )

        return ThreatMatch(matched=False)

    def add_indicator(self, ioc_type: IOCType, value: str,
                      threat_type: ThreatType = ThreatType.UNKNOWN,
                      confidence: int = 50, source: str = "manual",
                      description: str = "") -> bool:
        """
        Add a custom indicator.

        Args:
            ioc_type: Indicator type
            value: Indicator value
            threat_type: Threat category
            confidence: Confidence score
            source: Intelligence source
            description: Indicator description

        Returns:
            True if added successfully
        """
        indicator = ThreatIndicator(
            id="",
            ioc_type=ioc_type,
            value=value,
            threat_type=threat_type,
            confidence=confidence,
            source=source,
            description=description
        )

        return self.database.add_indicator(indicator)

    def _get_recommendations(self, indicator: ThreatIndicator) -> List[str]:
        """Generate recommendations based on indicator type and severity."""
        recommendations = []

        if indicator.severity >= 8:
            recommendations.append("CRITICAL: Block immediately and investigate")
        elif indicator.severity >= 5:
            recommendations.append("Block source and monitor for related activity")
        else:
            recommendations.append("Monitor and log for patterns")

        if indicator.threat_type == ThreatType.MALWARE:
            recommendations.append("Scan affected systems for malware")
            recommendations.append("Check for data exfiltration")
        elif indicator.threat_type == ThreatType.BOTNET:
            recommendations.append("Check for C2 communications")
            recommendations.append("Isolate infected hosts")
        elif indicator.threat_type == ThreatType.PHISHING:
            recommendations.append("Block related domains")
            recommendations.append("Alert users about phishing campaign")

        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """Get threat intelligence statistics."""
        db_stats = self.database.get_stats()
        return {
            **self.stats,
            **db_stats,
            'feeds_count': len(self.feed_manager.feeds)
        }

    def export_indicators(self, ioc_type: IOCType = None,
                          format: str = "json") -> str:
        """
        Export indicators to specified format.

        Args:
            ioc_type: Optional type filter
            format: Output format (json/csv/txt)

        Returns:
            Exported data as string
        """
        indicators = self.database.get_all_indicators(ioc_type)

        if format == "json":
            return json.dumps([i.to_dict() for i in indicators], indent=2)
        elif format == "csv":
            lines = ["type,value,threat_type,confidence,source"]
            for i in indicators:
                lines.append(f"{i.ioc_type.value},{i.value},{i.threat_type.value},{i.confidence},{i.source}")
            return "\n".join(lines)
        else:  # txt
            return "\n".join(i.value for i in indicators)


# =============================================================================
# DEMO AND TESTING
# =============================================================================

def run_demo():
    """Demonstrate Threat Intelligence functionality."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ELECTRODUCTION THREAT INTELLIGENCE                              ║
║                         IOC Management Demo                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Create TI instance
    ti = ThreatIntelligence()
    ti.start()

    # Add some test indicators
    print("[*] Adding test indicators...")
    ti.add_indicator(
        IOCType.IP_ADDRESS, "10.0.0.100",
        ThreatType.MALWARE, 80, "test",
        "Test malware C2 server"
    )
    ti.add_indicator(
        IOCType.DOMAIN, "malware-c2.evil.com",
        ThreatType.MALWARE, 90, "test",
        "Known malware C2 domain"
    )
    ti.add_indicator(
        IOCType.HASH_SHA256,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ThreatType.MALWARE, 100, "test",
        "Known malware hash"
    )

    # Test lookups
    print("\n[*] Testing threat lookups...\n")

    test_ips = ["10.0.0.100", "8.8.8.8", "192.168.1.1"]
    for ip in test_ips:
        result = ti.check_ip(ip)
        status = "🔴 THREAT" if result.matched else "🟢 CLEAN"
        print(f"  IP: {ip:20s} {status}")
        if result.matched:
            print(f"      Type: {result.indicator.threat_type.value}")
            print(f"      Confidence: {result.indicator.confidence}%")
            print(f"      Source: {result.indicator.source}")

    print()

    # Test domain lookup
    test_domains = ["malware-c2.evil.com", "google.com", "evil.com"]
    for domain in test_domains:
        result = ti.check_domain(domain)
        status = "🔴 THREAT" if result.matched else "🟢 CLEAN"
        print(f"  Domain: {domain:30s} {status}")
        if result.matched:
            print(f"      Description: {result.indicator.description}")

    print()

    # Test user agent lookup
    test_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "sqlmap/1.4.7#stable (http://sqlmap.org)",
        "Nikto/2.1.6",
    ]
    for ua in test_agents:
        result = ti.check_user_agent(ua)
        status = "🔴 SCANNER" if result.matched else "🟢 NORMAL"
        print(f"  User-Agent: {ua[:50]:50s}... {status}")

    # Show statistics
    print("\n[*] Threat Intelligence Statistics:")
    stats = ti.get_stats()
    for key, value in stats.items():
        if not isinstance(value, (list, dict)):
            print(f"    {key}: {value}")

    ti.stop()
    print("\n[*] Demo completed!")


if __name__ == "__main__":
    run_demo()
