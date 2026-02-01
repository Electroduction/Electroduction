#!/usr/bin/env python3
"""
File Processing Toolkit
=======================

Tools for file conversion, comparison, and batch operations.

Author: Electroduction Security Team
Version: 1.0.0
"""

import os
import sys
import csv
import json
import hashlib
import shutil
import zipfile
import tarfile
import tempfile
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Iterator
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class FileInfo:
    """File information."""
    path: str
    name: str
    extension: str
    size_bytes: int
    created: datetime
    modified: datetime
    is_directory: bool
    permissions: str


@dataclass
class ComparisonResult:
    """Result of file comparison."""
    identical: bool
    similarity: float
    additions: int
    deletions: int
    changes: int
    diff_lines: List[str]


class FileAnalyzer:
    """Analyze file properties and content."""

    def get_info(self, path: str) -> FileInfo:
        """Get detailed file information."""
        stat = os.stat(path)
        return FileInfo(
            path=path,
            name=os.path.basename(path),
            extension=os.path.splitext(path)[1],
            size_bytes=stat.st_size,
            created=datetime.fromtimestamp(stat.st_ctime),
            modified=datetime.fromtimestamp(stat.st_mtime),
            is_directory=os.path.isdir(path),
            permissions=oct(stat.st_mode)[-3:]
        )

    def get_hash(self, path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash."""
        h = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    def get_line_count(self, path: str) -> int:
        """Count lines in a text file."""
        count = 0
        with open(path, 'r', errors='ignore') as f:
            for _ in f:
                count += 1
        return count

    def get_word_count(self, path: str) -> int:
        """Count words in a text file."""
        count = 0
        with open(path, 'r', errors='ignore') as f:
            for line in f:
                count += len(line.split())
        return count

    def detect_encoding(self, path: str) -> str:
        """Try to detect file encoding."""
        with open(path, 'rb') as f:
            raw = f.read(4096)

        # Check for BOM
        if raw.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        if raw.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        if raw.startswith(b'\xfe\xff'):
            return 'utf-16-be'

        # Try UTF-8
        try:
            raw.decode('utf-8')
            return 'utf-8'
        except:
            pass

        return 'latin-1'

    def find_duplicates(self, directory: str, by_hash: bool = True) -> Dict[str, List[str]]:
        """Find duplicate files in directory."""
        file_groups = {}

        for root, dirs, files in os.walk(directory):
            for name in files:
                path = os.path.join(root, name)
                try:
                    if by_hash:
                        key = self.get_hash(path, 'md5')
                    else:
                        key = os.path.getsize(path)

                    if key not in file_groups:
                        file_groups[key] = []
                    file_groups[key].append(path)
                except:
                    pass

        return {k: v for k, v in file_groups.items() if len(v) > 1}


class FileComparer:
    """Compare files and directories."""

    def compare_text(self, file1: str, file2: str) -> ComparisonResult:
        """Compare two text files."""
        with open(file1, 'r', errors='ignore') as f:
            lines1 = f.readlines()
        with open(file2, 'r', errors='ignore') as f:
            lines2 = f.readlines()

        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))

        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        similarity = matcher.ratio()

        return ComparisonResult(
            identical=lines1 == lines2,
            similarity=similarity,
            additions=additions,
            deletions=deletions,
            changes=additions + deletions,
            diff_lines=diff
        )

    def compare_binary(self, file1: str, file2: str) -> ComparisonResult:
        """Compare two binary files."""
        with open(file1, 'rb') as f:
            content1 = f.read()
        with open(file2, 'rb') as f:
            content2 = f.read()

        identical = content1 == content2

        return ComparisonResult(
            identical=identical,
            similarity=1.0 if identical else 0.0,
            additions=0,
            deletions=0,
            changes=0 if identical else 1,
            diff_lines=[]
        )

    def compare_directories(self, dir1: str, dir2: str) -> Dict[str, Any]:
        """Compare two directories."""
        files1 = set()
        files2 = set()

        for root, dirs, files in os.walk(dir1):
            for name in files:
                rel_path = os.path.relpath(os.path.join(root, name), dir1)
                files1.add(rel_path)

        for root, dirs, files in os.walk(dir2):
            for name in files:
                rel_path = os.path.relpath(os.path.join(root, name), dir2)
                files2.add(rel_path)

        return {
            'only_in_first': list(files1 - files2),
            'only_in_second': list(files2 - files1),
            'in_both': list(files1 & files2),
            'total_first': len(files1),
            'total_second': len(files2)
        }


class FileConverter:
    """Convert between file formats."""

    def csv_to_json(self, csv_path: str, json_path: str = None) -> List[Dict]:
        """Convert CSV to JSON."""
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        if json_path:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        return data

    def json_to_csv(self, json_path: str, csv_path: str = None) -> bool:
        """Convert JSON to CSV."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list) or not data:
            return False

        if csv_path:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

        return True

    def xml_to_json(self, xml_path: str, json_path: str = None) -> Dict:
        """Convert XML to JSON."""
        def element_to_dict(element):
            result = {}
            if element.attrib:
                result['@attributes'] = dict(element.attrib)
            if element.text and element.text.strip():
                if len(element) == 0:
                    return element.text.strip()
                result['#text'] = element.text.strip()
            for child in element:
                child_data = element_to_dict(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            return result or ''

        tree = ET.parse(xml_path)
        data = {tree.getroot().tag: element_to_dict(tree.getroot())}

        if json_path:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        return data

    def text_to_lines(self, input_path: str, output_path: str = None) -> List[str]:
        """Convert text file to list of lines (JSON)."""
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.rstrip('\n\r') for line in f]

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(lines, f, indent=2)

        return lines


class ArchiveManager:
    """Manage archive files (ZIP, TAR, etc.)."""

    def create_zip(self, source: str, output: str,
                   compression: int = zipfile.ZIP_DEFLATED) -> bool:
        """Create a ZIP archive."""
        try:
            with zipfile.ZipFile(output, 'w', compression) as zf:
                if os.path.isfile(source):
                    zf.write(source, os.path.basename(source))
                else:
                    for root, dirs, files in os.walk(source):
                        for name in files:
                            filepath = os.path.join(root, name)
                            arcname = os.path.relpath(filepath, source)
                            zf.write(filepath, arcname)
            return True
        except:
            return False

    def extract_zip(self, archive: str, dest: str) -> bool:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(archive, 'r') as zf:
                zf.extractall(dest)
            return True
        except:
            return False

    def list_zip(self, archive: str) -> List[Dict[str, Any]]:
        """List contents of a ZIP archive."""
        contents = []
        try:
            with zipfile.ZipFile(archive, 'r') as zf:
                for info in zf.infolist():
                    contents.append({
                        'name': info.filename,
                        'size': info.file_size,
                        'compressed': info.compress_size,
                        'is_dir': info.is_dir()
                    })
        except:
            pass
        return contents

    def create_tar(self, source: str, output: str, mode: str = 'gz') -> bool:
        """Create a TAR archive."""
        try:
            tar_mode = f'w:{mode}' if mode else 'w'
            with tarfile.open(output, tar_mode) as tf:
                tf.add(source, arcname=os.path.basename(source))
            return True
        except:
            return False

    def extract_tar(self, archive: str, dest: str) -> bool:
        """Extract a TAR archive."""
        try:
            with tarfile.open(archive, 'r:*') as tf:
                tf.extractall(dest)
            return True
        except:
            return False


class BatchRenamer:
    """Batch rename files."""

    def preview_rename(self, directory: str, pattern: str,
                       replacement: str) -> List[Tuple[str, str]]:
        """Preview rename operations."""
        import re
        renames = []

        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                new_name = re.sub(pattern, replacement, name)
                if new_name != name:
                    renames.append((name, new_name))

        return renames

    def apply_rename(self, directory: str, renames: List[Tuple[str, str]]) -> int:
        """Apply rename operations."""
        success = 0
        for old_name, new_name in renames:
            try:
                old_path = os.path.join(directory, old_name)
                new_path = os.path.join(directory, new_name)
                os.rename(old_path, new_path)
                success += 1
            except:
                pass
        return success

    def add_prefix(self, directory: str, prefix: str,
                   pattern: str = '*') -> List[Tuple[str, str]]:
        """Add prefix to filenames."""
        import fnmatch
        renames = []

        for name in os.listdir(directory):
            if fnmatch.fnmatch(name, pattern):
                renames.append((name, prefix + name))

        return renames

    def add_suffix(self, directory: str, suffix: str,
                   pattern: str = '*') -> List[Tuple[str, str]]:
        """Add suffix before extension."""
        import fnmatch
        renames = []

        for name in os.listdir(directory):
            if fnmatch.fnmatch(name, pattern):
                base, ext = os.path.splitext(name)
                renames.append((name, base + suffix + ext))

        return renames

    def sequential_rename(self, directory: str, template: str = 'file_{:03d}',
                          pattern: str = '*') -> List[Tuple[str, str]]:
        """Rename files with sequential numbers."""
        import fnmatch
        renames = []
        files = sorted([f for f in os.listdir(directory)
                        if fnmatch.fnmatch(f, pattern) and
                        os.path.isfile(os.path.join(directory, f))])

        for i, name in enumerate(files, 1):
            ext = os.path.splitext(name)[1]
            new_name = template.format(i) + ext
            renames.append((name, new_name))

        return renames


class FileToolkit:
    """Main file processing toolkit."""

    def __init__(self):
        self.analyzer = FileAnalyzer()
        self.comparer = FileComparer()
        self.converter = FileConverter()
        self.archives = ArchiveManager()
        self.renamer = BatchRenamer()

    def quick_info(self, path: str) -> Dict[str, Any]:
        """Get quick file information."""
        info = self.analyzer.get_info(path)
        return {
            'name': info.name,
            'size': self._format_size(info.size_bytes),
            'modified': info.modified.strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'directory' if info.is_directory else info.extension or 'file'
        }

    def _format_size(self, bytes: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} PB"

    def copy_with_progress(self, src: str, dest: str,
                           callback: Optional[callable] = None) -> bool:
        """Copy file with progress callback."""
        try:
            size = os.path.getsize(src)
            copied = 0

            with open(src, 'rb') as fsrc:
                with open(dest, 'wb') as fdst:
                    while True:
                        chunk = fsrc.read(65536)
                        if not chunk:
                            break
                        fdst.write(chunk)
                        copied += len(chunk)
                        if callback:
                            callback(copied, size)
            return True
        except:
            return False


def main():
    """Command-line demo."""
    print("=" * 60)
    print("FILE PROCESSING TOOLKIT")
    print("=" * 60)
    print()

    toolkit = FileToolkit()

    # Create temp directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Demo directory: {temp_dir}")
    print()

    # Create sample files
    csv_file = os.path.join(temp_dir, "data.csv")
    json_file = os.path.join(temp_dir, "data.json")
    text_file = os.path.join(temp_dir, "sample.txt")

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'age', 'city'])
        writer.writerow(['Alice', '30', 'New York'])
        writer.writerow(['Bob', '25', 'Boston'])

    with open(text_file, 'w') as f:
        f.write("Hello, World!\n")
        f.write("This is a test file.\n")
        f.write("It has multiple lines.\n")

    # File Analysis
    print("1. FILE ANALYSIS")
    print("-" * 40)
    info = toolkit.analyzer.get_info(text_file)
    print(f"File: {info.name}")
    print(f"Size: {toolkit._format_size(info.size_bytes)}")
    print(f"Lines: {toolkit.analyzer.get_line_count(text_file)}")
    print(f"Words: {toolkit.analyzer.get_word_count(text_file)}")
    print(f"Hash: {toolkit.analyzer.get_hash(text_file, 'md5')[:16]}...")
    print()

    # File Conversion
    print("2. FILE CONVERSION")
    print("-" * 40)
    data = toolkit.converter.csv_to_json(csv_file, json_file)
    print(f"CSV to JSON: {len(data)} records converted")
    print(f"JSON data: {data}")
    print()

    # File Comparison
    print("3. FILE COMPARISON")
    print("-" * 40)
    text_file2 = os.path.join(temp_dir, "sample2.txt")
    with open(text_file2, 'w') as f:
        f.write("Hello, World!\n")
        f.write("This is a modified file.\n")
        f.write("It has different content.\n")

    result = toolkit.comparer.compare_text(text_file, text_file2)
    print(f"Identical: {result.identical}")
    print(f"Similarity: {result.similarity:.1%}")
    print(f"Changes: +{result.additions} -{result.deletions}")
    print()

    # Archive Management
    print("4. ARCHIVE MANAGEMENT")
    print("-" * 40)
    zip_file = os.path.join(temp_dir, "archive.zip")
    toolkit.archives.create_zip(temp_dir, zip_file)
    contents = toolkit.archives.list_zip(zip_file)
    print(f"Created ZIP with {len(contents)} files")
    for item in contents[:3]:
        print(f"  - {item['name']} ({item['size']} bytes)")
    print()

    # Batch Rename Preview
    print("5. BATCH RENAME PREVIEW")
    print("-" * 40)
    # Create some test files
    for i in range(3):
        with open(os.path.join(temp_dir, f"test_{i}.txt"), 'w') as f:
            f.write(f"File {i}")

    renames = toolkit.renamer.add_prefix(temp_dir, "new_", "test_*.txt")
    print("Rename preview:")
    for old, new in renames:
        print(f"  {old} -> {new}")
    print()

    # Duplicate Detection
    print("6. DUPLICATE DETECTION")
    print("-" * 40)
    # Create a duplicate
    shutil.copy(text_file, os.path.join(temp_dir, "sample_copy.txt"))
    duplicates = toolkit.analyzer.find_duplicates(temp_dir)
    print(f"Found {len(duplicates)} groups of duplicates")
    for hash_val, files in list(duplicates.items())[:1]:
        print(f"  Hash {hash_val[:8]}...: {len(files)} files")
    print()

    # Cleanup
    shutil.rmtree(temp_dir)

    print("=" * 60)
    print("File Processing Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
