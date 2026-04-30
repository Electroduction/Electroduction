#!/usr/bin/env python3
"""
System Administration Toolkit
==============================

Tools for system monitoring, process management, and administration tasks.

Author: Electroduction Security Team
Version: 1.0.0
"""

import os
import re
import sys
import time
import socket
import platform
import subprocess
import shutil
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessInfo:
    """Process information."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_mb: float
    user: str
    command: str


@dataclass
class DiskInfo:
    """Disk usage information."""
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float


@dataclass
class SystemInfo:
    """System information."""
    hostname: str
    platform: str
    architecture: str
    processor: str
    python_version: str
    uptime_seconds: float
    boot_time: datetime


class SystemMonitor:
    """Monitor system resources and performance."""

    def get_system_info(self) -> SystemInfo:
        """Get basic system information."""
        boot_time = self._get_boot_time()
        uptime = (datetime.now() - boot_time).total_seconds() if boot_time else 0

        return SystemInfo(
            hostname=socket.gethostname(),
            platform=platform.system(),
            architecture=platform.machine(),
            processor=platform.processor() or "Unknown",
            python_version=platform.python_version(),
            uptime_seconds=uptime,
            boot_time=boot_time or datetime.now()
        )

    def _get_boot_time(self) -> Optional[datetime]:
        """Get system boot time."""
        try:
            if os.path.exists('/proc/uptime'):
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                    return datetime.now() - timedelta(seconds=uptime_seconds)
        except:
            pass
        return None

    def get_cpu_usage(self) -> Dict[str, float]:
        """Get CPU usage statistics."""
        try:
            if os.path.exists('/proc/stat'):
                with open('/proc/stat', 'r') as f:
                    line = f.readline()
                    parts = line.split()[1:8]
                    values = [int(x) for x in parts]

                    total = sum(values)
                    idle = values[3]
                    usage = ((total - idle) / total) * 100 if total > 0 else 0

                    return {
                        'total_percent': round(usage, 2),
                        'user': values[0],
                        'system': values[2],
                        'idle': values[3],
                        'iowait': values[4] if len(values) > 4 else 0
                    }
        except:
            pass

        return {'total_percent': 0, 'user': 0, 'system': 0, 'idle': 0, 'iowait': 0}

    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = int(parts[1].strip().split()[0])
                            meminfo[key] = value

                    total = meminfo.get('MemTotal', 0) / 1024  # MB
                    free = meminfo.get('MemFree', 0) / 1024
                    available = meminfo.get('MemAvailable', free) / 1024
                    buffers = meminfo.get('Buffers', 0) / 1024
                    cached = meminfo.get('Cached', 0) / 1024
                    used = total - available

                    return {
                        'total_mb': round(total, 2),
                        'used_mb': round(used, 2),
                        'free_mb': round(free, 2),
                        'available_mb': round(available, 2),
                        'buffers_mb': round(buffers, 2),
                        'cached_mb': round(cached, 2),
                        'percent_used': round((used / total) * 100, 2) if total > 0 else 0
                    }
        except:
            pass

        return {'total_mb': 0, 'used_mb': 0, 'free_mb': 0, 'percent_used': 0}

    def get_disk_usage(self, paths: Optional[List[str]] = None) -> List[DiskInfo]:
        """Get disk usage for specified paths."""
        if paths is None:
            paths = ['/']

        results = []
        for path in paths:
            try:
                usage = shutil.disk_usage(path)
                results.append(DiskInfo(
                    path=path,
                    total_gb=round(usage.total / (1024**3), 2),
                    used_gb=round(usage.used / (1024**3), 2),
                    free_gb=round(usage.free / (1024**3), 2),
                    percent_used=round((usage.used / usage.total) * 100, 2)
                ))
            except:
                pass

        return results

    def get_network_stats(self) -> Dict[str, Dict[str, int]]:
        """Get network interface statistics."""
        stats = {}
        try:
            if os.path.exists('/proc/net/dev'):
                with open('/proc/net/dev', 'r') as f:
                    lines = f.readlines()[2:]  # Skip headers
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 10:
                            iface = parts[0].rstrip(':')
                            stats[iface] = {
                                'rx_bytes': int(parts[1]),
                                'rx_packets': int(parts[2]),
                                'tx_bytes': int(parts[9]),
                                'tx_packets': int(parts[10])
                            }
        except:
            pass

        return stats

    def get_load_average(self) -> Tuple[float, float, float]:
        """Get system load averages (1, 5, 15 minutes)."""
        try:
            if os.path.exists('/proc/loadavg'):
                with open('/proc/loadavg', 'r') as f:
                    parts = f.read().split()[:3]
                    return tuple(float(x) for x in parts)
        except:
            pass
        return (0.0, 0.0, 0.0)


class ProcessManager:
    """Manage system processes."""

    def list_processes(self) -> List[ProcessInfo]:
        """List all running processes."""
        processes = []

        try:
            if os.path.exists('/proc'):
                for pid_dir in os.listdir('/proc'):
                    if pid_dir.isdigit():
                        info = self._get_process_info(int(pid_dir))
                        if info:
                            processes.append(info)
        except:
            pass

        return sorted(processes, key=lambda p: p.memory_mb, reverse=True)

    def _get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get information about a specific process."""
        try:
            proc_dir = f'/proc/{pid}'

            # Get command
            with open(f'{proc_dir}/cmdline', 'r') as f:
                cmdline = f.read().replace('\x00', ' ').strip()

            # Get status
            with open(f'{proc_dir}/status', 'r') as f:
                status_data = {}
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        status_data[parts[0].strip()] = parts[1].strip()

            # Get stat for CPU
            with open(f'{proc_dir}/stat', 'r') as f:
                stat_parts = f.read().split()

            name = status_data.get('Name', 'unknown')
            state = status_data.get('State', '?').split()[0]
            uid = status_data.get('Uid', '0').split()[0]

            # Memory in MB
            vm_rss = int(status_data.get('VmRSS', '0 kB').split()[0]) / 1024

            return ProcessInfo(
                pid=pid,
                name=name,
                status=state,
                cpu_percent=0.0,  # Would need sampling to calculate
                memory_mb=round(vm_rss, 2),
                user=uid,
                command=cmdline or name
            )
        except:
            return None

    def find_process(self, name: str) -> List[ProcessInfo]:
        """Find processes by name."""
        all_procs = self.list_processes()
        return [p for p in all_procs if name.lower() in p.name.lower()]

    def kill_process(self, pid: int, signal_num: int = signal.SIGTERM) -> bool:
        """Send signal to a process."""
        try:
            os.kill(pid, signal_num)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return False

    def get_process_count(self) -> int:
        """Get total number of running processes."""
        try:
            return len([d for d in os.listdir('/proc') if d.isdigit()])
        except:
            return 0


class ServiceManager:
    """Manage system services (systemd)."""

    def list_services(self) -> List[Dict[str, str]]:
        """List all services."""
        services = []
        try:
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service', '--all', '--no-pager'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n')[1:]:
                    parts = line.split()
                    if len(parts) >= 4 and parts[0].endswith('.service'):
                        services.append({
                            'name': parts[0],
                            'load': parts[1],
                            'active': parts[2],
                            'sub': parts[3],
                            'description': ' '.join(parts[4:]) if len(parts) > 4 else ''
                        })
        except:
            pass
        return services

    def get_service_status(self, service: str) -> Dict[str, Any]:
        """Get status of a specific service."""
        try:
            result = subprocess.run(
                ['systemctl', 'status', service, '--no-pager'],
                capture_output=True, text=True, timeout=10
            )
            return {
                'name': service,
                'running': 'active (running)' in result.stdout,
                'enabled': self._is_enabled(service),
                'output': result.stdout
            }
        except:
            return {'name': service, 'running': False, 'enabled': False, 'output': ''}

    def _is_enabled(self, service: str) -> bool:
        """Check if service is enabled."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-enabled', service],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() == 'enabled'
        except:
            return False


class DiskManager:
    """Manage disk operations."""

    def get_mounted_filesystems(self) -> List[Dict[str, str]]:
        """Get list of mounted filesystems."""
        mounts = []
        try:
            if os.path.exists('/proc/mounts'):
                with open('/proc/mounts', 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 4:
                            mounts.append({
                                'device': parts[0],
                                'mount_point': parts[1],
                                'fs_type': parts[2],
                                'options': parts[3]
                            })
        except:
            pass
        return mounts

    def find_large_files(self, path: str, min_size_mb: int = 100,
                         max_files: int = 20) -> List[Dict[str, Any]]:
        """Find large files in a directory."""
        large_files = []
        min_size = min_size_mb * 1024 * 1024

        try:
            for root, dirs, files in os.walk(path):
                for name in files:
                    try:
                        filepath = os.path.join(root, name)
                        size = os.path.getsize(filepath)
                        if size >= min_size:
                            large_files.append({
                                'path': filepath,
                                'size_mb': round(size / (1024 * 1024), 2),
                                'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
                            })
                    except:
                        pass

                if len(large_files) >= max_files * 2:
                    break

        except:
            pass

        return sorted(large_files, key=lambda x: x['size_mb'], reverse=True)[:max_files]

    def get_directory_size(self, path: str) -> float:
        """Get total size of a directory in MB."""
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for name in files:
                    try:
                        total += os.path.getsize(os.path.join(root, name))
                    except:
                        pass
        except:
            pass
        return round(total / (1024 * 1024), 2)


class LogManager:
    """Manage system logs."""

    LOG_PATHS = [
        '/var/log/syslog',
        '/var/log/messages',
        '/var/log/auth.log',
        '/var/log/secure',
        '/var/log/kern.log',
        '/var/log/dmesg'
    ]

    def tail_log(self, path: str, lines: int = 50) -> List[str]:
        """Get last N lines from a log file."""
        try:
            with open(path, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except:
            return []

    def search_log(self, path: str, pattern: str, max_results: int = 100) -> List[str]:
        """Search log file for pattern."""
        results = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            with open(path, 'r') as f:
                for line in f:
                    if regex.search(line):
                        results.append(line.strip())
                        if len(results) >= max_results:
                            break
        except:
            pass
        return results

    def get_available_logs(self) -> List[str]:
        """Get list of available log files."""
        return [p for p in self.LOG_PATHS if os.path.exists(p)]


class SysAdminToolkit:
    """Main system administration toolkit."""

    def __init__(self):
        self.monitor = SystemMonitor()
        self.processes = ProcessManager()
        self.services = ServiceManager()
        self.disks = DiskManager()
        self.logs = LogManager()

    def get_system_summary(self) -> Dict[str, Any]:
        """Get complete system summary."""
        sys_info = self.monitor.get_system_info()
        cpu = self.monitor.get_cpu_usage()
        memory = self.monitor.get_memory_usage()
        disks = self.monitor.get_disk_usage(['/'])
        load = self.monitor.get_load_average()

        return {
            'system': {
                'hostname': sys_info.hostname,
                'platform': sys_info.platform,
                'architecture': sys_info.architecture,
                'uptime_hours': round(sys_info.uptime_seconds / 3600, 2)
            },
            'cpu': {
                'usage_percent': cpu['total_percent'],
                'load_1min': load[0],
                'load_5min': load[1],
                'load_15min': load[2]
            },
            'memory': {
                'total_mb': memory['total_mb'],
                'used_mb': memory['used_mb'],
                'percent_used': memory['percent_used']
            },
            'disk': {
                'path': disks[0].path if disks else '/',
                'total_gb': disks[0].total_gb if disks else 0,
                'used_gb': disks[0].used_gb if disks else 0,
                'percent_used': disks[0].percent_used if disks else 0
            },
            'processes': self.processes.get_process_count()
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        summary = self.get_system_summary()

        issues = []
        status = 'healthy'

        # Check CPU
        if summary['cpu']['usage_percent'] > 90:
            issues.append('High CPU usage (>90%)')
            status = 'critical'
        elif summary['cpu']['usage_percent'] > 70:
            issues.append('Elevated CPU usage (>70%)')
            if status != 'critical':
                status = 'warning'

        # Check memory
        if summary['memory']['percent_used'] > 90:
            issues.append('High memory usage (>90%)')
            status = 'critical'
        elif summary['memory']['percent_used'] > 80:
            issues.append('Elevated memory usage (>80%)')
            if status != 'critical':
                status = 'warning'

        # Check disk
        if summary['disk']['percent_used'] > 90:
            issues.append('Low disk space (<10% free)')
            status = 'critical'
        elif summary['disk']['percent_used'] > 80:
            issues.append('Disk space warning (<20% free)')
            if status != 'critical':
                status = 'warning'

        # Check load average
        if summary['cpu']['load_1min'] > 4:
            issues.append('High system load')
            if status != 'critical':
                status = 'warning'

        return {
            'status': status,
            'issues': issues,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Command-line demo."""
    print("=" * 60)
    print("SYSTEM ADMINISTRATION TOOLKIT")
    print("=" * 60)
    print()

    toolkit = SysAdminToolkit()

    # System Summary
    print("1. SYSTEM SUMMARY")
    print("-" * 40)
    summary = toolkit.get_system_summary()
    print(f"Hostname: {summary['system']['hostname']}")
    print(f"Platform: {summary['system']['platform']} {summary['system']['architecture']}")
    print(f"Uptime: {summary['system']['uptime_hours']:.1f} hours")
    print()

    # CPU & Memory
    print("2. RESOURCE USAGE")
    print("-" * 40)
    print(f"CPU Usage: {summary['cpu']['usage_percent']:.1f}%")
    print(f"Load Average: {summary['cpu']['load_1min']:.2f}, {summary['cpu']['load_5min']:.2f}, {summary['cpu']['load_15min']:.2f}")
    print(f"Memory: {summary['memory']['used_mb']:.0f}MB / {summary['memory']['total_mb']:.0f}MB ({summary['memory']['percent_used']:.1f}%)")
    print(f"Disk: {summary['disk']['used_gb']:.1f}GB / {summary['disk']['total_gb']:.1f}GB ({summary['disk']['percent_used']:.1f}%)")
    print()

    # Processes
    print("3. TOP PROCESSES (by memory)")
    print("-" * 40)
    processes = toolkit.processes.list_processes()[:5]
    for p in processes:
        print(f"  PID {p.pid}: {p.name} - {p.memory_mb:.1f}MB")
    print(f"Total processes: {summary['processes']}")
    print()

    # Network
    print("4. NETWORK INTERFACES")
    print("-" * 40)
    net_stats = toolkit.monitor.get_network_stats()
    for iface, stats in list(net_stats.items())[:3]:
        rx_mb = stats['rx_bytes'] / (1024*1024)
        tx_mb = stats['tx_bytes'] / (1024*1024)
        print(f"  {iface}: RX {rx_mb:.1f}MB, TX {tx_mb:.1f}MB")
    print()

    # Health Check
    print("5. HEALTH CHECK")
    print("-" * 40)
    health = toolkit.health_check()
    status_icon = {'healthy': '✓', 'warning': '⚠', 'critical': '✗'}[health['status']]
    print(f"Status: {status_icon} {health['status'].upper()}")
    if health['issues']:
        print("Issues:")
        for issue in health['issues']:
            print(f"  - {issue}")
    else:
        print("No issues detected")
    print()

    print("=" * 60)
    print("System Administration Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
