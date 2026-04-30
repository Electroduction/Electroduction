#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION IT SECURITY SUITE - SYSTEM MONITOR
================================================================================
A comprehensive system monitoring tool that tracks CPU, memory, disk, network,
and process metrics in real-time. Provides alerts for resource thresholds
and historical trending.

Features:
- Real-time CPU usage monitoring (per-core and overall)
- Memory usage tracking (RAM and swap)
- Disk I/O and space monitoring
- Network traffic analysis
- Process monitoring and top consumers
- Temperature monitoring (if available)
- Alert system for threshold breaches
- Historical data logging
- Dashboard display mode

Usage:
    python system_monitor.py                # Interactive dashboard
    python system_monitor.py --once         # Single snapshot
    python system_monitor.py --log          # Log mode (continuous)
    python system_monitor.py --process PID  # Monitor specific process
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os                    # Operating system interface for system info
import sys                   # System-specific parameters
import time                  # Time-related functions
import json                  # JSON encoding for data export
import threading             # Threading for background monitoring
import signal                # Signal handling for graceful shutdown
from datetime import datetime, timedelta  # Date/time handling
from typing import Dict, List, Optional, Tuple, Any, Callable  # Type hints
from dataclasses import dataclass, field  # Data class decorators
from enum import Enum, auto  # Enumeration support
from collections import deque  # Fixed-size history buffers
from pathlib import Path     # Object-oriented paths
import subprocess            # Process execution


# =============================================================================
# ENUMERATIONS - Resource and alert categories
# =============================================================================

class ResourceType(Enum):
    """
    Enumeration of monitored resource types.
    Each type has specific collection and alerting logic.
    """
    CPU = auto()        # CPU utilization
    MEMORY = auto()     # RAM and swap usage
    DISK = auto()       # Disk space and I/O
    NETWORK = auto()    # Network traffic
    PROCESS = auto()    # Process-level metrics
    TEMPERATURE = auto()  # Hardware temperatures


class AlertLevel(Enum):
    """
    Alert severity levels for threshold breaches.
    Used to prioritize and filter notifications.
    """
    INFO = 0       # Informational, no action needed
    WARNING = 1    # Warning, may need attention soon
    CRITICAL = 2   # Critical, immediate action required
    EMERGENCY = 3  # Emergency, system at risk


# =============================================================================
# DATA CLASSES - Structured metric containers
# =============================================================================

@dataclass
class CPUMetrics:
    """
    Container for CPU utilization metrics.

    Attributes:
        overall: Total CPU usage percentage (0-100)
        per_core: List of per-core usage percentages
        user: User space CPU time percentage
        system: Kernel space CPU time percentage
        idle: Idle time percentage
        iowait: I/O wait percentage
        load_avg: Load averages (1, 5, 15 minutes)
        frequency: Current CPU frequency in MHz
        temperature: CPU temperature in Celsius (if available)
    """
    overall: float = 0.0                              # Total CPU usage %
    per_core: List[float] = field(default_factory=list)  # Per-core %
    user: float = 0.0                                 # User CPU time %
    system: float = 0.0                               # System CPU time %
    idle: float = 0.0                                 # Idle time %
    iowait: float = 0.0                               # I/O wait %
    load_avg: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Load averages
    frequency: float = 0.0                            # CPU frequency MHz
    temperature: float = 0.0                          # Temperature Celsius


@dataclass
class MemoryMetrics:
    """
    Container for memory usage metrics.

    Attributes:
        total: Total physical memory in bytes
        available: Available memory in bytes
        used: Used memory in bytes
        percent: Memory usage percentage
        swap_total: Total swap space in bytes
        swap_used: Used swap space in bytes
        swap_percent: Swap usage percentage
        buffers: Memory used for buffers
        cached: Memory used for cache
    """
    total: int = 0              # Total RAM bytes
    available: int = 0          # Available RAM bytes
    used: int = 0               # Used RAM bytes
    percent: float = 0.0        # RAM usage %
    swap_total: int = 0         # Total swap bytes
    swap_used: int = 0          # Used swap bytes
    swap_percent: float = 0.0   # Swap usage %
    buffers: int = 0            # Buffer memory bytes
    cached: int = 0             # Cached memory bytes


@dataclass
class DiskMetrics:
    """
    Container for disk usage and I/O metrics.

    Attributes:
        partitions: Dict of partition info (mount -> usage)
        read_bytes: Total bytes read
        write_bytes: Total bytes written
        read_count: Number of read operations
        write_count: Number of write operations
        read_time: Time spent reading (ms)
        write_time: Time spent writing (ms)
    """
    partitions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    read_bytes: int = 0         # Total read bytes
    write_bytes: int = 0        # Total write bytes
    read_count: int = 0         # Read operation count
    write_count: int = 0        # Write operation count
    read_time: int = 0          # Read time ms
    write_time: int = 0         # Write time ms


@dataclass
class NetworkMetrics:
    """
    Container for network traffic metrics.

    Attributes:
        interfaces: Dict of interface info (name -> stats)
        bytes_sent: Total bytes sent
        bytes_recv: Total bytes received
        packets_sent: Total packets sent
        packets_recv: Total packets received
        errors_in: Inbound errors
        errors_out: Outbound errors
        connections: Number of active connections
    """
    interfaces: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    bytes_sent: int = 0         # Total sent bytes
    bytes_recv: int = 0         # Total received bytes
    packets_sent: int = 0       # Sent packet count
    packets_recv: int = 0       # Received packet count
    errors_in: int = 0          # Inbound errors
    errors_out: int = 0         # Outbound errors
    connections: int = 0        # Active connection count


@dataclass
class ProcessMetrics:
    """
    Container for process-level metrics.

    Attributes:
        pid: Process ID
        name: Process name
        cpu_percent: CPU usage percentage
        memory_percent: Memory usage percentage
        memory_rss: Resident set size (physical memory)
        threads: Number of threads
        status: Process status string
        user: Owner username
        create_time: Process creation timestamp
        cmdline: Command line arguments
    """
    pid: int = 0                # Process ID
    name: str = ""              # Process name
    cpu_percent: float = 0.0    # CPU usage %
    memory_percent: float = 0.0  # Memory usage %
    memory_rss: int = 0         # RSS memory bytes
    threads: int = 0            # Thread count
    status: str = ""            # Process status
    user: str = ""              # Owner user
    create_time: float = 0.0    # Creation timestamp
    cmdline: str = ""           # Command line


@dataclass
class SystemSnapshot:
    """
    Complete system state snapshot at a point in time.

    Attributes:
        timestamp: When the snapshot was taken
        cpu: CPU metrics
        memory: Memory metrics
        disk: Disk metrics
        network: Network metrics
        top_processes: List of top resource-consuming processes
        uptime: System uptime in seconds
        hostname: System hostname
    """
    timestamp: datetime = field(default_factory=datetime.now)
    cpu: CPUMetrics = field(default_factory=CPUMetrics)
    memory: MemoryMetrics = field(default_factory=MemoryMetrics)
    disk: DiskMetrics = field(default_factory=DiskMetrics)
    network: NetworkMetrics = field(default_factory=NetworkMetrics)
    top_processes: List[ProcessMetrics] = field(default_factory=list)
    uptime: float = 0.0         # Uptime seconds
    hostname: str = ""          # System hostname


@dataclass
class Alert:
    """
    System alert for threshold breaches.

    Attributes:
        timestamp: When the alert was generated
        level: Alert severity level
        resource: Type of resource triggering alert
        message: Human-readable alert message
        value: Current value that triggered alert
        threshold: Threshold that was breached
    """
    timestamp: datetime          # Alert time
    level: AlertLevel            # Severity level
    resource: ResourceType       # Resource type
    message: str                 # Alert message
    value: float                 # Current value
    threshold: float             # Threshold value


# =============================================================================
# SYSTEM METRICS COLLECTOR - Gather system statistics
# =============================================================================

class MetricsCollector:
    """
    Collects system metrics from /proc filesystem and system utilities.
    Works without external dependencies on Linux systems.
    """

    def __init__(self):
        """
        Initialize the metrics collector.
        Detects available metrics sources and caches previous values
        for calculating deltas (rates).
        """
        # Previous values for calculating rates
        self._prev_cpu_times: Dict[str, int] = {}    # Previous CPU times
        self._prev_disk_io: Dict[str, int] = {}      # Previous disk I/O
        self._prev_net_io: Dict[str, int] = {}       # Previous network I/O
        self._prev_timestamp: float = time.time()    # Previous collection time

        # Cache for expensive operations
        self._cpu_count = self._get_cpu_count()      # Number of CPU cores
        self._hostname = self._get_hostname()        # System hostname

    def _get_cpu_count(self) -> int:
        """
        Get the number of CPU cores.

        Returns:
            Number of CPU cores/threads
        """
        try:
            # Read from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                return sum(1 for line in f if line.startswith('processor'))
        except:
            return 1  # Default to 1 if can't determine

    def _get_hostname(self) -> str:
        """
        Get the system hostname.

        Returns:
            Hostname string
        """
        try:
            with open('/proc/sys/kernel/hostname', 'r') as f:
                return f.read().strip()
        except:
            return "unknown"

    def collect_cpu(self) -> CPUMetrics:
        """
        Collect CPU utilization metrics from /proc/stat.

        Returns:
            CPUMetrics with current CPU usage
        """
        metrics = CPUMetrics()

        try:
            # Read /proc/stat for CPU times
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()

            # Parse overall CPU line (first line)
            # Format: cpu user nice system idle iowait irq softirq steal guest
            cpu_line = lines[0].split()
            if cpu_line[0] == 'cpu':
                # Extract time values
                user = int(cpu_line[1])
                nice = int(cpu_line[2])
                system = int(cpu_line[3])
                idle = int(cpu_line[4])
                iowait = int(cpu_line[5]) if len(cpu_line) > 5 else 0
                irq = int(cpu_line[6]) if len(cpu_line) > 6 else 0
                softirq = int(cpu_line[7]) if len(cpu_line) > 7 else 0

                # Calculate total
                total = user + nice + system + idle + iowait + irq + softirq

                # Calculate percentages (need delta from previous reading)
                if 'cpu_total' in self._prev_cpu_times:
                    prev_total = self._prev_cpu_times['cpu_total']
                    prev_idle = self._prev_cpu_times['cpu_idle']

                    total_delta = total - prev_total
                    idle_delta = idle - prev_idle

                    if total_delta > 0:
                        # Calculate usage as non-idle percentage
                        metrics.overall = ((total_delta - idle_delta) / total_delta) * 100
                        metrics.idle = (idle_delta / total_delta) * 100

                # Store current values for next calculation
                self._prev_cpu_times['cpu_total'] = total
                self._prev_cpu_times['cpu_idle'] = idle

            # Parse per-core CPU lines
            per_core = []
            for line in lines[1:]:
                if line.startswith('cpu'):
                    parts = line.split()
                    if len(parts) >= 5:
                        # Similar calculation for each core
                        core_user = int(parts[1])
                        core_nice = int(parts[2])
                        core_system = int(parts[3])
                        core_idle = int(parts[4])
                        core_total = core_user + core_nice + core_system + core_idle

                        core_name = parts[0]
                        if f'{core_name}_total' in self._prev_cpu_times:
                            prev_total = self._prev_cpu_times[f'{core_name}_total']
                            prev_idle = self._prev_cpu_times[f'{core_name}_idle']
                            delta_total = core_total - prev_total
                            delta_idle = core_idle - prev_idle
                            if delta_total > 0:
                                usage = ((delta_total - delta_idle) / delta_total) * 100
                                per_core.append(usage)

                        self._prev_cpu_times[f'{core_name}_total'] = core_total
                        self._prev_cpu_times[f'{core_name}_idle'] = core_idle
                else:
                    break  # No more CPU lines

            metrics.per_core = per_core

            # Get load averages from /proc/loadavg
            try:
                with open('/proc/loadavg', 'r') as f:
                    parts = f.read().split()
                    metrics.load_avg = (
                        float(parts[0]),  # 1-minute average
                        float(parts[1]),  # 5-minute average
                        float(parts[2])   # 15-minute average
                    )
            except:
                pass

            # Try to get CPU frequency
            try:
                # Read from cpufreq
                freq_file = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'
                if os.path.exists(freq_file):
                    with open(freq_file, 'r') as f:
                        # Value is in kHz, convert to MHz
                        metrics.frequency = int(f.read().strip()) / 1000
            except:
                pass

            # Try to get CPU temperature
            try:
                # Check thermal zones
                for i in range(10):
                    temp_file = f'/sys/class/thermal/thermal_zone{i}/temp'
                    if os.path.exists(temp_file):
                        with open(temp_file, 'r') as f:
                            # Value is in millidegrees Celsius
                            temp = int(f.read().strip()) / 1000
                            if temp > 0:  # Valid reading
                                metrics.temperature = temp
                                break
            except:
                pass

        except Exception as e:
            print(f"[ERROR] CPU collection failed: {e}")

        return metrics

    def collect_memory(self) -> MemoryMetrics:
        """
        Collect memory usage metrics from /proc/meminfo.

        Returns:
            MemoryMetrics with current memory usage
        """
        metrics = MemoryMetrics()

        try:
            # Read /proc/meminfo
            meminfo = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    # Format: "MemTotal:       16384 kB"
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value_parts = parts[1].strip().split()
                        # Convert to bytes (values are in kB)
                        value = int(value_parts[0]) * 1024
                        meminfo[key] = value

            # Extract key values
            metrics.total = meminfo.get('MemTotal', 0)
            metrics.available = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
            metrics.buffers = meminfo.get('Buffers', 0)
            metrics.cached = meminfo.get('Cached', 0)

            # Calculate used memory
            metrics.used = metrics.total - metrics.available

            # Calculate percentage
            if metrics.total > 0:
                metrics.percent = (metrics.used / metrics.total) * 100

            # Swap info
            metrics.swap_total = meminfo.get('SwapTotal', 0)
            swap_free = meminfo.get('SwapFree', 0)
            metrics.swap_used = metrics.swap_total - swap_free

            if metrics.swap_total > 0:
                metrics.swap_percent = (metrics.swap_used / metrics.swap_total) * 100

        except Exception as e:
            print(f"[ERROR] Memory collection failed: {e}")

        return metrics

    def collect_disk(self) -> DiskMetrics:
        """
        Collect disk usage and I/O metrics.

        Returns:
            DiskMetrics with current disk statistics
        """
        metrics = DiskMetrics()

        try:
            # Get disk partitions from /proc/mounts
            partitions = {}
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        device = parts[0]
                        mount = parts[1]

                        # Skip virtual filesystems
                        if device.startswith('/dev/') and not mount.startswith('/sys'):
                            try:
                                # Use statvfs to get space info
                                stat = os.statvfs(mount)
                                total = stat.f_blocks * stat.f_frsize
                                free = stat.f_bfree * stat.f_frsize
                                used = total - free
                                percent = (used / total * 100) if total > 0 else 0

                                partitions[mount] = {
                                    'device': device,
                                    'total': total,
                                    'used': used,
                                    'free': free,
                                    'percent': percent
                                }
                            except (OSError, PermissionError):
                                pass  # Skip inaccessible mounts

            metrics.partitions = partitions

            # Get disk I/O from /proc/diskstats
            with open('/proc/diskstats', 'r') as f:
                total_read = 0
                total_write = 0

                for line in f:
                    parts = line.split()
                    if len(parts) >= 14:
                        # Fields: major minor name reads_completed reads_merged
                        #         sectors_read ms_reading writes_completed writes_merged
                        #         sectors_written ms_writing ios_in_progress ms_io weighted_ms_io
                        device_name = parts[2]

                        # Only count physical devices (not partitions)
                        if device_name.startswith('sd') and len(device_name) == 3:
                            # sectors_read * 512 = bytes read
                            sectors_read = int(parts[5])
                            sectors_written = int(parts[9])

                            total_read += sectors_read * 512
                            total_write += sectors_written * 512

                metrics.read_bytes = total_read
                metrics.write_bytes = total_write

        except Exception as e:
            print(f"[ERROR] Disk collection failed: {e}")

        return metrics

    def collect_network(self) -> NetworkMetrics:
        """
        Collect network interface statistics from /proc/net/dev.

        Returns:
            NetworkMetrics with current network statistics
        """
        metrics = NetworkMetrics()

        try:
            # Read /proc/net/dev
            interfaces = {}
            total_sent = 0
            total_recv = 0
            total_packets_sent = 0
            total_packets_recv = 0
            total_errors = 0

            with open('/proc/net/dev', 'r') as f:
                # Skip header lines
                next(f)
                next(f)

                for line in f:
                    # Format: interface: recv_bytes packets errs drop fifo frame compressed multicast
                    #                    send_bytes packets errs drop fifo colls carrier compressed
                    parts = line.split(':')
                    if len(parts) == 2:
                        iface = parts[0].strip()
                        stats = parts[1].split()

                        if len(stats) >= 16:
                            recv_bytes = int(stats[0])
                            recv_packets = int(stats[1])
                            recv_errs = int(stats[2])

                            send_bytes = int(stats[8])
                            send_packets = int(stats[9])
                            send_errs = int(stats[10])

                            interfaces[iface] = {
                                'bytes_recv': recv_bytes,
                                'bytes_sent': send_bytes,
                                'packets_recv': recv_packets,
                                'packets_sent': send_packets,
                                'errors_in': recv_errs,
                                'errors_out': send_errs
                            }

                            # Aggregate totals (skip loopback)
                            if iface != 'lo':
                                total_recv += recv_bytes
                                total_sent += send_bytes
                                total_packets_recv += recv_packets
                                total_packets_sent += send_packets
                                total_errors += recv_errs + send_errs

            metrics.interfaces = interfaces
            metrics.bytes_recv = total_recv
            metrics.bytes_sent = total_sent
            metrics.packets_recv = total_packets_recv
            metrics.packets_sent = total_packets_sent
            metrics.errors_in = total_errors

            # Count active connections from /proc/net/tcp and /proc/net/udp
            connection_count = 0
            for proto_file in ['/proc/net/tcp', '/proc/net/udp']:
                try:
                    with open(proto_file, 'r') as f:
                        # Skip header
                        next(f)
                        connection_count += sum(1 for line in f)
                except:
                    pass

            metrics.connections = connection_count

        except Exception as e:
            print(f"[ERROR] Network collection failed: {e}")

        return metrics

    def collect_processes(self, top_n: int = 10) -> List[ProcessMetrics]:
        """
        Collect metrics for top resource-consuming processes.

        Args:
            top_n: Number of top processes to return

        Returns:
            List of ProcessMetrics sorted by CPU usage
        """
        processes = []

        try:
            # List all process directories in /proc
            for entry in os.listdir('/proc'):
                if entry.isdigit():
                    pid = int(entry)
                    try:
                        proc = self._get_process_info(pid)
                        if proc:
                            processes.append(proc)
                    except (FileNotFoundError, PermissionError, ProcessLookupError):
                        pass  # Process may have exited

            # Sort by CPU usage and return top N
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
            return processes[:top_n]

        except Exception as e:
            print(f"[ERROR] Process collection failed: {e}")
            return []

    def _get_process_info(self, pid: int) -> Optional[ProcessMetrics]:
        """
        Get metrics for a specific process.

        Args:
            pid: Process ID to query

        Returns:
            ProcessMetrics or None if process not accessible
        """
        proc_dir = f'/proc/{pid}'

        if not os.path.exists(proc_dir):
            return None

        metrics = ProcessMetrics(pid=pid)

        try:
            # Read process status
            with open(f'{proc_dir}/status', 'r') as f:
                for line in f:
                    if line.startswith('Name:'):
                        metrics.name = line.split(':', 1)[1].strip()
                    elif line.startswith('State:'):
                        metrics.status = line.split(':', 1)[1].strip().split()[0]
                    elif line.startswith('Uid:'):
                        uid = int(line.split()[1])
                        metrics.user = self._get_username(uid)
                    elif line.startswith('Threads:'):
                        metrics.threads = int(line.split(':', 1)[1].strip())
                    elif line.startswith('VmRSS:'):
                        # RSS in kB
                        metrics.memory_rss = int(line.split()[1]) * 1024

            # Read stat for CPU usage
            with open(f'{proc_dir}/stat', 'r') as f:
                parts = f.read().split()
                if len(parts) >= 22:
                    # Field 14: utime, 15: stime (in clock ticks)
                    utime = int(parts[13])
                    stime = int(parts[14])
                    total_time = utime + stime

                    # Store for rate calculation
                    prev_key = f'proc_{pid}_time'
                    prev_time = self._prev_cpu_times.get(prev_key, 0)
                    now = time.time()
                    prev_timestamp = self._prev_cpu_times.get(f'proc_{pid}_ts', now)

                    elapsed = now - prev_timestamp
                    if elapsed > 0 and prev_time > 0:
                        # Convert ticks to percentage
                        # Assume 100 ticks per second (SC_CLK_TCK)
                        ticks_delta = total_time - prev_time
                        metrics.cpu_percent = (ticks_delta / 100.0 / elapsed) * 100

                    self._prev_cpu_times[prev_key] = total_time
                    self._prev_cpu_times[f'proc_{pid}_ts'] = now

                    # Field 22: start time in clock ticks since boot
                    start_time = int(parts[21])
                    metrics.create_time = start_time / 100.0  # Approx

            # Calculate memory percentage
            total_mem = self.collect_memory().total
            if total_mem > 0:
                metrics.memory_percent = (metrics.memory_rss / total_mem) * 100

            # Read command line
            try:
                with open(f'{proc_dir}/cmdline', 'r') as f:
                    cmdline = f.read().replace('\x00', ' ').strip()
                    metrics.cmdline = cmdline[:100]  # Truncate long command lines
            except:
                metrics.cmdline = metrics.name

            return metrics

        except (FileNotFoundError, PermissionError):
            return None

    def _get_username(self, uid: int) -> str:
        """
        Convert UID to username.

        Args:
            uid: User ID to look up

        Returns:
            Username string or UID as string if not found
        """
        try:
            with open('/etc/passwd', 'r') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) >= 3 and int(parts[2]) == uid:
                        return parts[0]
        except:
            pass
        return str(uid)

    def collect_uptime(self) -> float:
        """
        Get system uptime in seconds.

        Returns:
            Uptime in seconds
        """
        try:
            with open('/proc/uptime', 'r') as f:
                return float(f.read().split()[0])
        except:
            return 0.0

    def collect_all(self) -> SystemSnapshot:
        """
        Collect a complete system snapshot.

        Returns:
            SystemSnapshot with all current metrics
        """
        return SystemSnapshot(
            timestamp=datetime.now(),
            cpu=self.collect_cpu(),
            memory=self.collect_memory(),
            disk=self.collect_disk(),
            network=self.collect_network(),
            top_processes=self.collect_processes(10),
            uptime=self.collect_uptime(),
            hostname=self._hostname
        )


# =============================================================================
# ALERT MANAGER - Threshold monitoring and alerting
# =============================================================================

class AlertManager:
    """
    Manages threshold-based alerts for system resources.
    Tracks thresholds and generates alerts when breached.
    """

    def __init__(self):
        """
        Initialize the alert manager with default thresholds.
        """
        # Default thresholds (can be customized)
        self.thresholds = {
            'cpu_warning': 70.0,       # CPU usage warning threshold
            'cpu_critical': 90.0,      # CPU usage critical threshold
            'memory_warning': 75.0,    # Memory usage warning
            'memory_critical': 90.0,   # Memory usage critical
            'disk_warning': 80.0,      # Disk usage warning
            'disk_critical': 95.0,     # Disk usage critical
            'swap_warning': 50.0,      # Swap usage warning
            'load_warning': 4.0,       # Load average warning (per core)
            'temp_warning': 70.0,      # Temperature warning (Celsius)
            'temp_critical': 85.0,     # Temperature critical
        }

        # Alert history for deduplication
        self.recent_alerts: deque = deque(maxlen=100)

        # Alert callbacks
        self.callbacks: List[Callable[[Alert], None]] = []

    def set_threshold(self, name: str, value: float):
        """
        Set a threshold value.

        Args:
            name: Threshold name (e.g., 'cpu_warning')
            value: Threshold value
        """
        self.thresholds[name] = value

    def add_callback(self, callback: Callable[[Alert], None]):
        """
        Add an alert callback function.

        Args:
            callback: Function to call when alert is generated
        """
        self.callbacks.append(callback)

    def check_snapshot(self, snapshot: SystemSnapshot) -> List[Alert]:
        """
        Check a system snapshot against all thresholds.

        Args:
            snapshot: SystemSnapshot to check

        Returns:
            List of Alert objects for threshold breaches
        """
        alerts = []

        # Check CPU
        cpu_alerts = self._check_cpu(snapshot.cpu)
        alerts.extend(cpu_alerts)

        # Check Memory
        mem_alerts = self._check_memory(snapshot.memory)
        alerts.extend(mem_alerts)

        # Check Disk
        disk_alerts = self._check_disk(snapshot.disk)
        alerts.extend(disk_alerts)

        # Trigger callbacks for each alert
        for alert in alerts:
            for callback in self.callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"[ERROR] Alert callback failed: {e}")

        # Store in history
        self.recent_alerts.extend(alerts)

        return alerts

    def _check_cpu(self, cpu: CPUMetrics) -> List[Alert]:
        """
        Check CPU metrics against thresholds.

        Args:
            cpu: CPUMetrics to check

        Returns:
            List of CPU-related alerts
        """
        alerts = []

        # Check overall CPU usage
        if cpu.overall >= self.thresholds['cpu_critical']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.CRITICAL,
                resource=ResourceType.CPU,
                message=f"Critical CPU usage: {cpu.overall:.1f}%",
                value=cpu.overall,
                threshold=self.thresholds['cpu_critical']
            ))
        elif cpu.overall >= self.thresholds['cpu_warning']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                resource=ResourceType.CPU,
                message=f"High CPU usage: {cpu.overall:.1f}%",
                value=cpu.overall,
                threshold=self.thresholds['cpu_warning']
            ))

        # Check load average
        if cpu.load_avg[0] >= self.thresholds['load_warning']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                resource=ResourceType.CPU,
                message=f"High load average: {cpu.load_avg[0]:.2f}",
                value=cpu.load_avg[0],
                threshold=self.thresholds['load_warning']
            ))

        # Check temperature
        if cpu.temperature >= self.thresholds['temp_critical']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.CRITICAL,
                resource=ResourceType.TEMPERATURE,
                message=f"Critical CPU temperature: {cpu.temperature:.1f}°C",
                value=cpu.temperature,
                threshold=self.thresholds['temp_critical']
            ))
        elif cpu.temperature >= self.thresholds['temp_warning']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                resource=ResourceType.TEMPERATURE,
                message=f"High CPU temperature: {cpu.temperature:.1f}°C",
                value=cpu.temperature,
                threshold=self.thresholds['temp_warning']
            ))

        return alerts

    def _check_memory(self, memory: MemoryMetrics) -> List[Alert]:
        """
        Check memory metrics against thresholds.

        Args:
            memory: MemoryMetrics to check

        Returns:
            List of memory-related alerts
        """
        alerts = []

        # Check RAM usage
        if memory.percent >= self.thresholds['memory_critical']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.CRITICAL,
                resource=ResourceType.MEMORY,
                message=f"Critical memory usage: {memory.percent:.1f}%",
                value=memory.percent,
                threshold=self.thresholds['memory_critical']
            ))
        elif memory.percent >= self.thresholds['memory_warning']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                resource=ResourceType.MEMORY,
                message=f"High memory usage: {memory.percent:.1f}%",
                value=memory.percent,
                threshold=self.thresholds['memory_warning']
            ))

        # Check swap usage
        if memory.swap_percent >= self.thresholds['swap_warning']:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                resource=ResourceType.MEMORY,
                message=f"High swap usage: {memory.swap_percent:.1f}%",
                value=memory.swap_percent,
                threshold=self.thresholds['swap_warning']
            ))

        return alerts

    def _check_disk(self, disk: DiskMetrics) -> List[Alert]:
        """
        Check disk metrics against thresholds.

        Args:
            disk: DiskMetrics to check

        Returns:
            List of disk-related alerts
        """
        alerts = []

        # Check each partition
        for mount, info in disk.partitions.items():
            percent = info.get('percent', 0)

            if percent >= self.thresholds['disk_critical']:
                alerts.append(Alert(
                    timestamp=datetime.now(),
                    level=AlertLevel.CRITICAL,
                    resource=ResourceType.DISK,
                    message=f"Critical disk usage on {mount}: {percent:.1f}%",
                    value=percent,
                    threshold=self.thresholds['disk_critical']
                ))
            elif percent >= self.thresholds['disk_warning']:
                alerts.append(Alert(
                    timestamp=datetime.now(),
                    level=AlertLevel.WARNING,
                    resource=ResourceType.DISK,
                    message=f"High disk usage on {mount}: {percent:.1f}%",
                    value=percent,
                    threshold=self.thresholds['disk_warning']
                ))

        return alerts


# =============================================================================
# DISPLAY FORMATTER - Format metrics for display
# =============================================================================

class DisplayFormatter:
    """
    Formats system metrics for console display.
    Provides various output formats (dashboard, table, JSON).
    """

    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """
        Format bytes into human-readable string.

        Args:
            bytes_val: Bytes value to format

        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"

    @staticmethod
    def format_uptime(seconds: float) -> str:
        """
        Format uptime seconds into human-readable string.

        Args:
            seconds: Uptime in seconds

        Returns:
            Formatted string (e.g., "5d 12h 30m")
        """
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        return " ".join(parts)

    @staticmethod
    def format_bar(percent: float, width: int = 20) -> str:
        """
        Create a visual progress bar.

        Args:
            percent: Percentage value (0-100)
            width: Bar width in characters

        Returns:
            Formatted bar string (e.g., "[████████░░░░░░░░░░░░]")
        """
        filled = int(percent / 100 * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def format_dashboard(self, snapshot: SystemSnapshot) -> str:
        """
        Format a complete dashboard display.

        Args:
            snapshot: SystemSnapshot to display

        Returns:
            Formatted dashboard string
        """
        lines = []

        # Header
        lines.append("═" * 80)
        lines.append(f"  SYSTEM MONITOR - {snapshot.hostname}")
        lines.append(f"  {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Uptime: {self.format_uptime(snapshot.uptime)}")
        lines.append("═" * 80)

        # CPU Section
        lines.append("")
        lines.append("┌─ CPU ─────────────────────────────────────────────────────────────────────┐")

        cpu = snapshot.cpu
        bar = self.format_bar(cpu.overall)
        lines.append(f"│  Overall: {bar} {cpu.overall:5.1f}%")

        # Per-core display (show first 8 cores on one line)
        if cpu.per_core:
            core_strs = [f"C{i}:{p:4.0f}%" for i, p in enumerate(cpu.per_core[:8])]
            lines.append(f"│  Cores:   {' '.join(core_strs)}")

        lines.append(f"│  Load:    1m: {cpu.load_avg[0]:.2f}  5m: {cpu.load_avg[1]:.2f}  15m: {cpu.load_avg[2]:.2f}")

        if cpu.frequency > 0:
            lines.append(f"│  Freq:    {cpu.frequency:.0f} MHz")
        if cpu.temperature > 0:
            lines.append(f"│  Temp:    {cpu.temperature:.1f}°C")

        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

        # Memory Section
        lines.append("")
        lines.append("┌─ MEMORY ──────────────────────────────────────────────────────────────────┐")

        mem = snapshot.memory
        bar = self.format_bar(mem.percent)
        lines.append(f"│  RAM:     {bar} {mem.percent:5.1f}%")
        lines.append(f"│           {self.format_bytes(mem.used)} / {self.format_bytes(mem.total)}")

        if mem.swap_total > 0:
            swap_bar = self.format_bar(mem.swap_percent)
            lines.append(f"│  Swap:    {swap_bar} {mem.swap_percent:5.1f}%")

        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

        # Disk Section
        lines.append("")
        lines.append("┌─ DISK ────────────────────────────────────────────────────────────────────┐")

        for mount, info in list(snapshot.disk.partitions.items())[:4]:
            percent = info.get('percent', 0)
            bar = self.format_bar(percent, 15)
            used = self.format_bytes(info.get('used', 0))
            total = self.format_bytes(info.get('total', 0))
            lines.append(f"│  {mount[:15]:<15} {bar} {percent:5.1f}% ({used}/{total})")

        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

        # Network Section
        lines.append("")
        lines.append("┌─ NETWORK ──────────────────────────────────────────────────────────────────┐")

        net = snapshot.network
        lines.append(f"│  Total Recv: {self.format_bytes(net.bytes_recv):<12} Sent: {self.format_bytes(net.bytes_sent)}")
        lines.append(f"│  Packets:    {net.packets_recv:>10} in   {net.packets_sent:>10} out")
        lines.append(f"│  Connections: {net.connections}")

        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

        # Top Processes Section
        lines.append("")
        lines.append("┌─ TOP PROCESSES ───────────────────────────────────────────────────────────┐")
        lines.append("│  PID      NAME                    CPU%    MEM%    THREADS")

        for proc in snapshot.top_processes[:5]:
            lines.append(f"│  {proc.pid:<8} {proc.name[:22]:<22} {proc.cpu_percent:5.1f}   {proc.memory_percent:5.1f}   {proc.threads:>5}")

        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

        return "\n".join(lines)

    def format_json(self, snapshot: SystemSnapshot) -> str:
        """
        Format snapshot as JSON.

        Args:
            snapshot: SystemSnapshot to format

        Returns:
            JSON string
        """
        data = {
            'timestamp': snapshot.timestamp.isoformat(),
            'hostname': snapshot.hostname,
            'uptime': snapshot.uptime,
            'cpu': {
                'overall': snapshot.cpu.overall,
                'per_core': snapshot.cpu.per_core,
                'load_avg': snapshot.cpu.load_avg,
                'frequency': snapshot.cpu.frequency,
                'temperature': snapshot.cpu.temperature
            },
            'memory': {
                'total': snapshot.memory.total,
                'used': snapshot.memory.used,
                'percent': snapshot.memory.percent,
                'swap_percent': snapshot.memory.swap_percent
            },
            'disk': {
                'partitions': snapshot.disk.partitions,
                'read_bytes': snapshot.disk.read_bytes,
                'write_bytes': snapshot.disk.write_bytes
            },
            'network': {
                'bytes_sent': snapshot.network.bytes_sent,
                'bytes_recv': snapshot.network.bytes_recv,
                'connections': snapshot.network.connections
            },
            'top_processes': [
                {
                    'pid': p.pid,
                    'name': p.name,
                    'cpu_percent': p.cpu_percent,
                    'memory_percent': p.memory_percent
                }
                for p in snapshot.top_processes
            ]
        }

        return json.dumps(data, indent=2)


# =============================================================================
# SYSTEM MONITOR - Main monitoring class
# =============================================================================

class SystemMonitor:
    """
    Main system monitoring class that coordinates collection,
    alerting, and display. Supports continuous and one-shot modes.
    """

    def __init__(self):
        """
        Initialize the system monitor.
        """
        self.collector = MetricsCollector()   # Metrics collector
        self.alert_manager = AlertManager()   # Alert manager
        self.formatter = DisplayFormatter()   # Display formatter
        self.running = False                  # Monitor state
        self.history: deque = deque(maxlen=3600)  # 1 hour of snapshots at 1/s

    def collect_snapshot(self) -> SystemSnapshot:
        """
        Collect a single system snapshot.

        Returns:
            Current SystemSnapshot
        """
        return self.collector.collect_all()

    def run_once(self, json_output: bool = False) -> str:
        """
        Run a single collection and display.

        Args:
            json_output: If True, output JSON instead of dashboard

        Returns:
            Formatted output string
        """
        snapshot = self.collect_snapshot()

        if json_output:
            return self.formatter.format_json(snapshot)
        else:
            return self.formatter.format_dashboard(snapshot)

    def run_continuous(self, interval: float = 1.0, clear_screen: bool = True):
        """
        Run continuous monitoring with dashboard display.

        Args:
            interval: Seconds between updates
            clear_screen: Whether to clear screen between updates
        """
        self.running = True

        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.running = False
            print("\n[*] Stopping monitor...")

        signal.signal(signal.SIGINT, signal_handler)

        # Initial collection to prime rate calculations
        self.collector.collect_all()
        time.sleep(0.1)

        print("[*] Starting system monitor... Press Ctrl+C to stop")
        time.sleep(1)

        try:
            while self.running:
                # Collect snapshot
                snapshot = self.collect_snapshot()
                self.history.append(snapshot)

                # Check alerts
                alerts = self.alert_manager.check_snapshot(snapshot)

                # Clear screen and display dashboard
                if clear_screen:
                    print("\033[2J\033[H", end="")  # ANSI clear screen

                print(self.formatter.format_dashboard(snapshot))

                # Display any alerts
                if alerts:
                    print("\n⚠️  ALERTS:")
                    for alert in alerts:
                        level_color = "\033[91m" if alert.level == AlertLevel.CRITICAL else "\033[93m"
                        print(f"  {level_color}[{alert.level.name}]\033[0m {alert.message}")

                time.sleep(interval)

        except KeyboardInterrupt:
            pass

        print("\n[*] Monitor stopped")

    def run_logging(self, interval: float = 60.0, log_file: str = None):
        """
        Run continuous logging mode (no dashboard, just log entries).

        Args:
            interval: Seconds between log entries
            log_file: Optional file to write logs
        """
        self.running = True

        def signal_handler(sig, frame):
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)

        print(f"[*] Starting logging mode (interval: {interval}s)")
        if log_file:
            print(f"[*] Logging to: {log_file}")

        log_handle = None
        if log_file:
            log_handle = open(log_file, 'a')

        try:
            while self.running:
                snapshot = self.collect_snapshot()

                # Format log entry
                log_entry = {
                    'timestamp': snapshot.timestamp.isoformat(),
                    'cpu_percent': snapshot.cpu.overall,
                    'memory_percent': snapshot.memory.percent,
                    'disk_percent': max(
                        [p.get('percent', 0) for p in snapshot.disk.partitions.values()] or [0]
                    ),
                    'load_1m': snapshot.cpu.load_avg[0],
                    'connections': snapshot.network.connections
                }

                log_line = json.dumps(log_entry)
                print(log_line)

                if log_handle:
                    log_handle.write(log_line + '\n')
                    log_handle.flush()

                time.sleep(interval)

        except KeyboardInterrupt:
            pass

        if log_handle:
            log_handle.close()

        print("\n[*] Logging stopped")

    def monitor_process(self, pid: int, interval: float = 1.0):
        """
        Monitor a specific process.

        Args:
            pid: Process ID to monitor
            interval: Seconds between updates
        """
        self.running = True

        def signal_handler(sig, frame):
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)

        print(f"[*] Monitoring process {pid}... Press Ctrl+C to stop")

        try:
            while self.running:
                proc = self.collector._get_process_info(pid)

                if proc is None:
                    print(f"\n[!] Process {pid} not found or inaccessible")
                    break

                # Clear screen
                print("\033[2J\033[H", end="")

                # Display process info
                print("═" * 60)
                print(f"  PROCESS MONITOR - PID {pid}")
                print("═" * 60)
                print(f"  Name:     {proc.name}")
                print(f"  Status:   {proc.status}")
                print(f"  User:     {proc.user}")
                print(f"  Threads:  {proc.threads}")
                print(f"  CPU:      {proc.cpu_percent:.1f}%")
                print(f"  Memory:   {proc.memory_percent:.1f}% ({self.formatter.format_bytes(proc.memory_rss)})")
                print(f"  Command:  {proc.cmdline[:50]}...")
                print("═" * 60)

                time.sleep(interval)

        except KeyboardInterrupt:
            pass

        print("\n[*] Process monitoring stopped")


# =============================================================================
# DEMO AND MAIN ENTRY POINT
# =============================================================================

def run_demo():
    """
    Run a demonstration of the System Monitor capabilities.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ELECTRODUCTION SYSTEM MONITOR                             ║
║                    Real-time System Monitoring Tool                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    monitor = SystemMonitor()

    print("[*] Collecting system snapshot...")
    time.sleep(0.5)  # Brief delay to calculate rates

    # Get a snapshot
    snapshot = monitor.collect_snapshot()

    # Display dashboard
    print(monitor.formatter.format_dashboard(snapshot))

    # Check for alerts
    alerts = monitor.alert_manager.check_snapshot(snapshot)
    if alerts:
        print("\n⚠️  ALERTS DETECTED:")
        for alert in alerts:
            print(f"  [{alert.level.name}] {alert.message}")

    print("\n[*] Demo completed!")
    print("[*] Use --continuous for live monitoring")


def main():
    """
    Main entry point for the System Monitor.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ELECTRODUCTION SYSTEM MONITOR                             ║
║                    Real-time System Monitoring Tool v1.0                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        # Default: run demo
        run_demo()
    elif sys.argv[1] == '--once':
        # Single snapshot
        monitor = SystemMonitor()
        print(monitor.run_once())
    elif sys.argv[1] == '--json':
        # JSON output
        monitor = SystemMonitor()
        time.sleep(0.2)
        print(monitor.run_once(json_output=True))
    elif sys.argv[1] == '--continuous' or sys.argv[1] == '-c':
        # Continuous monitoring
        monitor = SystemMonitor()
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        monitor.run_continuous(interval=interval)
    elif sys.argv[1] == '--log':
        # Logging mode
        monitor = SystemMonitor()
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
        log_file = sys.argv[3] if len(sys.argv) > 3 else None
        monitor.run_logging(interval=interval, log_file=log_file)
    elif sys.argv[1] == '--process' or sys.argv[1] == '-p':
        # Process monitoring
        if len(sys.argv) < 3:
            print("[ERROR] Please specify a PID")
            print("Usage: python system_monitor.py --process PID")
            sys.exit(1)
        pid = int(sys.argv[2])
        monitor = SystemMonitor()
        monitor.monitor_process(pid)
    elif sys.argv[1] == '--help':
        print("""
Usage:
    python system_monitor.py                      Run demo (single snapshot)
    python system_monitor.py --once               Single snapshot display
    python system_monitor.py --json               Single snapshot as JSON
    python system_monitor.py --continuous [sec]   Live monitoring (default: 1s)
    python system_monitor.py --log [sec] [file]   Logging mode (default: 60s)
    python system_monitor.py --process PID        Monitor specific process
    python system_monitor.py --help               Show this help

Examples:
    python system_monitor.py --continuous 2       Update every 2 seconds
    python system_monitor.py --log 60 /var/log/metrics.log
    python system_monitor.py --process 1234
        """)
    else:
        print(f"[ERROR] Unknown option: {sys.argv[1]}")
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
