#!/usr/bin/env python3
"""
Automation Toolkit
==================

Tools for task scheduling, file watching, and batch processing.

Author: Electroduction Security Team
Version: 1.0.0
"""

import os
import sys
import time
import threading
import queue
import json
import shutil
import fnmatch
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class Task:
    """Represents a scheduled task."""
    name: str
    action: Callable
    interval_seconds: int
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    enabled: bool = True
    max_runs: Optional[int] = None


@dataclass
class FileEvent:
    """Represents a file system event."""
    event_type: str  # created, modified, deleted, moved
    path: str
    timestamp: datetime
    is_directory: bool


@dataclass
class BatchResult:
    """Result of a batch operation."""
    success: int
    failed: int
    skipped: int
    errors: List[str]
    duration_seconds: float


class TaskScheduler:
    """Schedule and run tasks at intervals."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_task(self, name: str, action: Callable, interval_seconds: int,
                 args: tuple = (), kwargs: dict = None, max_runs: int = None) -> Task:
        """Add a scheduled task."""
        task = Task(
            name=name,
            action=action,
            interval_seconds=interval_seconds,
            args=args,
            kwargs=kwargs or {},
            next_run=datetime.now(),
            max_runs=max_runs
        )
        with self._lock:
            self.tasks[name] = task
        return task

    def remove_task(self, name: str) -> bool:
        """Remove a task."""
        with self._lock:
            if name in self.tasks:
                del self.tasks[name]
                return True
        return False

    def enable_task(self, name: str) -> bool:
        """Enable a task."""
        with self._lock:
            if name in self.tasks:
                self.tasks[name].enabled = True
                return True
        return False

    def disable_task(self, name: str) -> bool:
        """Disable a task."""
        with self._lock:
            if name in self.tasks:
                self.tasks[name].enabled = False
                return True
        return False

    def run_task_now(self, name: str) -> bool:
        """Run a task immediately."""
        with self._lock:
            task = self.tasks.get(name)
        if task:
            self._execute_task(task)
            return True
        return False

    def _execute_task(self, task: Task):
        """Execute a task."""
        try:
            task.action(*task.args, **task.kwargs)
            task.last_run = datetime.now()
            task.run_count += 1
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

            if task.max_runs and task.run_count >= task.max_runs:
                task.enabled = False
        except Exception as e:
            print(f"Task {task.name} failed: {e}")

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()

            with self._lock:
                tasks_to_run = [
                    t for t in self.tasks.values()
                    if t.enabled and t.next_run and t.next_run <= now
                ]

            for task in tasks_to_run:
                self._execute_task(task)

            time.sleep(1)

    def start(self):
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        with self._lock:
            return {
                'running': self._running,
                'tasks': {
                    name: {
                        'enabled': t.enabled,
                        'interval': t.interval_seconds,
                        'run_count': t.run_count,
                        'last_run': t.last_run.isoformat() if t.last_run else None,
                        'next_run': t.next_run.isoformat() if t.next_run else None
                    }
                    for name, t in self.tasks.items()
                }
            }


class FileWatcher:
    """Watch directories for file changes."""

    def __init__(self, paths: List[str], patterns: List[str] = None):
        """
        Initialize file watcher.

        Args:
            paths: Directories to watch
            patterns: File patterns to match (e.g., ['*.py', '*.txt'])
        """
        self.paths = paths
        self.patterns = patterns or ['*']
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[FileEvent], None]] = []
        self._file_states: Dict[str, float] = {}
        self._poll_interval = 1.0

    def add_callback(self, callback: Callable[[FileEvent], None]):
        """Add callback for file events."""
        self._callbacks.append(callback)

    def _matches_pattern(self, filename: str) -> bool:
        """Check if filename matches any pattern."""
        return any(fnmatch.fnmatch(filename, p) for p in self.patterns)

    def _scan_directory(self, path: str) -> Dict[str, float]:
        """Scan directory and return file modification times."""
        files = {}
        try:
            for root, dirs, filenames in os.walk(path):
                for name in filenames:
                    if self._matches_pattern(name):
                        filepath = os.path.join(root, name)
                        try:
                            files[filepath] = os.path.getmtime(filepath)
                        except:
                            pass
        except:
            pass
        return files

    def _detect_changes(self) -> List[FileEvent]:
        """Detect file changes."""
        events = []
        current_state = {}

        for path in self.paths:
            current_state.update(self._scan_directory(path))

        now = datetime.now()

        # Check for new and modified files
        for filepath, mtime in current_state.items():
            if filepath not in self._file_states:
                events.append(FileEvent(
                    event_type='created',
                    path=filepath,
                    timestamp=now,
                    is_directory=False
                ))
            elif mtime > self._file_states[filepath]:
                events.append(FileEvent(
                    event_type='modified',
                    path=filepath,
                    timestamp=now,
                    is_directory=False
                ))

        # Check for deleted files
        for filepath in self._file_states:
            if filepath not in current_state:
                events.append(FileEvent(
                    event_type='deleted',
                    path=filepath,
                    timestamp=now,
                    is_directory=False
                ))

        self._file_states = current_state
        return events

    def _watch_loop(self):
        """Main watch loop."""
        # Initial scan
        for path in self.paths:
            self._file_states.update(self._scan_directory(path))

        while self._running:
            events = self._detect_changes()

            for event in events:
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"Callback error: {e}")

            time.sleep(self._poll_interval)

    def start(self):
        """Start watching."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


class BatchProcessor:
    """Process files in batches."""

    def __init__(self, max_workers: int = 4):
        """Initialize batch processor."""
        self.max_workers = max_workers

    def process_files(self, files: List[str],
                      processor: Callable[[str], bool]) -> BatchResult:
        """
        Process multiple files.

        Args:
            files: List of file paths
            processor: Function that processes a file and returns success status
        """
        start_time = time.time()
        success = 0
        failed = 0
        skipped = 0
        errors = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(processor, f): f for f in files}

            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    result = future.result()
                    if result:
                        success += 1
                    else:
                        skipped += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"{filepath}: {e}")

        return BatchResult(
            success=success,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration_seconds=time.time() - start_time
        )

    def find_files(self, directory: str, pattern: str = '*',
                   recursive: bool = True) -> List[str]:
        """Find files matching pattern."""
        files = []
        if recursive:
            for root, dirs, filenames in os.walk(directory):
                for name in filenames:
                    if fnmatch.fnmatch(name, pattern):
                        files.append(os.path.join(root, name))
        else:
            for name in os.listdir(directory):
                filepath = os.path.join(directory, name)
                if os.path.isfile(filepath) and fnmatch.fnmatch(name, pattern):
                    files.append(filepath)
        return files

    def batch_rename(self, directory: str, pattern: str,
                     replacement: str, dry_run: bool = True) -> List[Tuple[str, str]]:
        """Batch rename files."""
        import re
        renames = []

        for name in os.listdir(directory):
            filepath = os.path.join(directory, name)
            if os.path.isfile(filepath):
                new_name = re.sub(pattern, replacement, name)
                if new_name != name:
                    new_path = os.path.join(directory, new_name)
                    renames.append((filepath, new_path))

                    if not dry_run:
                        os.rename(filepath, new_path)

        return renames

    def batch_copy(self, files: List[str], dest_dir: str,
                   preserve_structure: bool = False,
                   base_dir: str = None) -> BatchResult:
        """Copy multiple files to destination."""
        def copy_file(src: str) -> bool:
            try:
                if preserve_structure and base_dir:
                    rel_path = os.path.relpath(src, base_dir)
                    dest = os.path.join(dest_dir, rel_path)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                else:
                    dest = os.path.join(dest_dir, os.path.basename(src))

                shutil.copy2(src, dest)
                return True
            except:
                return False

        os.makedirs(dest_dir, exist_ok=True)
        return self.process_files(files, copy_file)

    def batch_delete(self, files: List[str], dry_run: bool = True) -> BatchResult:
        """Delete multiple files."""
        def delete_file(path: str) -> bool:
            if dry_run:
                return True
            try:
                os.remove(path)
                return True
            except:
                return False

        return self.process_files(files, delete_file)


class CommandRunner:
    """Run shell commands with timeout and output capture."""

    def run(self, command: str, timeout: int = 60,
            shell: bool = True) -> Dict[str, Any]:
        """Run a command and capture output."""
        start = time.time()

        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': time.time() - start
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'duration': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': time.time() - start
            }

    def run_multiple(self, commands: List[str], parallel: bool = False,
                     timeout: int = 60) -> List[Dict[str, Any]]:
        """Run multiple commands."""
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(self.run, cmd, timeout) for cmd in commands]
                return [f.result() for f in as_completed(futures)]
        else:
            return [self.run(cmd, timeout) for cmd in commands]


class AutomationToolkit:
    """Main automation toolkit."""

    def __init__(self):
        self.scheduler = TaskScheduler()
        self.batch = BatchProcessor()
        self.commands = CommandRunner()

    def create_watcher(self, paths: List[str], patterns: List[str] = None) -> FileWatcher:
        """Create a new file watcher."""
        return FileWatcher(paths, patterns)

    def schedule_command(self, name: str, command: str,
                         interval_seconds: int) -> Task:
        """Schedule a command to run periodically."""
        return self.scheduler.add_task(
            name=name,
            action=lambda: self.commands.run(command),
            interval_seconds=interval_seconds
        )


def main():
    """Command-line demo."""
    print("=" * 60)
    print("AUTOMATION TOOLKIT")
    print("=" * 60)
    print()

    toolkit = AutomationToolkit()

    # Task Scheduler Demo
    print("1. TASK SCHEDULER DEMO")
    print("-" * 40)

    counter = {'value': 0}

    def increment_counter():
        counter['value'] += 1
        print(f"  Counter: {counter['value']}")

    toolkit.scheduler.add_task(
        name="counter",
        action=increment_counter,
        interval_seconds=1,
        max_runs=3
    )

    print("Starting scheduler (3 runs)...")
    toolkit.scheduler.start()
    time.sleep(4)
    toolkit.scheduler.stop()

    status = toolkit.scheduler.get_status()
    print(f"Task 'counter' ran {status['tasks']['counter']['run_count']} times")
    print()

    # Batch Processor Demo
    print("2. BATCH PROCESSOR DEMO")
    print("-" * 40)

    # Create temp files for demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    for i in range(5):
        with open(os.path.join(temp_dir, f"file_{i}.txt"), 'w') as f:
            f.write(f"Content {i}")

    files = toolkit.batch.find_files(temp_dir, "*.txt")
    print(f"Found {len(files)} files")

    def process_file(path):
        # Simulate processing
        return True

    result = toolkit.batch.process_files(files, process_file)
    print(f"Processed: {result.success} success, {result.failed} failed")
    print(f"Duration: {result.duration_seconds:.3f}s")

    # Cleanup
    shutil.rmtree(temp_dir)
    print()

    # Command Runner Demo
    print("3. COMMAND RUNNER DEMO")
    print("-" * 40)

    result = toolkit.commands.run("echo 'Hello, Automation!'")
    print(f"Command output: {result['stdout'].strip()}")
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration']:.3f}s")
    print()

    # File Watcher Demo (brief)
    print("4. FILE WATCHER DEMO")
    print("-" * 40)

    temp_dir = tempfile.mkdtemp()
    events_log = []

    def on_event(event):
        events_log.append(event)
        print(f"  Event: {event.event_type} - {os.path.basename(event.path)}")

    watcher = toolkit.create_watcher([temp_dir], ['*.txt'])
    watcher.add_callback(on_event)
    watcher.start()

    # Create a file to trigger event
    time.sleep(1.5)
    with open(os.path.join(temp_dir, "test.txt"), 'w') as f:
        f.write("test")
    time.sleep(1.5)

    watcher.stop()
    print(f"Events detected: {len(events_log)}")

    # Cleanup
    shutil.rmtree(temp_dir)
    print()

    print("=" * 60)
    print("Automation Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
