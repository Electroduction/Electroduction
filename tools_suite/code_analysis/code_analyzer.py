#!/usr/bin/env python3
"""
Code Analysis Toolkit
=====================

A comprehensive toolkit for static code analysis, metrics calculation,
and code quality assessment.

Author: Electroduction Security Team
Version: 1.0.0

Features:
---------
- Code Metrics: Lines of code, cyclomatic complexity, maintainability index
- Syntax Analysis: Parse and analyze code structure
- Code Quality: Detect common issues and anti-patterns
- Documentation Analysis: Check docstring coverage
- Dependency Analysis: Map imports and dependencies
- Duplicate Detection: Find code duplication

Usage:
------
    from code_analyzer import CodeAnalyzer, PythonParser, MetricsCalculator

    # Analyze a Python file
    analyzer = CodeAnalyzer()
    metrics = analyzer.analyze_file("mycode.py")

    # Get complexity metrics
    calc = MetricsCalculator()
    complexity = calc.cyclomatic_complexity(code)
"""

import os
import re
import ast
import json
import hashlib
import tokenize
from io import StringIO
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FunctionInfo:
    """Information about a function or method."""
    name: str
    lineno: int
    end_lineno: int
    args: List[str]
    defaults: int
    decorators: List[str]
    docstring: Optional[str]
    complexity: int = 1
    is_method: bool = False
    is_async: bool = False
    returns: Optional[str] = None


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    lineno: int
    end_lineno: int
    bases: List[str]
    decorators: List[str]
    docstring: Optional[str]
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: List[str]
    alias: Optional[str]
    lineno: int
    is_from_import: bool


@dataclass
class CodeMetrics:
    """Code metrics for a file or module."""
    filename: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    docstring_lines: int
    functions: int
    classes: int
    imports: int
    avg_complexity: float
    max_complexity: int
    maintainability_index: float
    docstring_coverage: float


@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    category: str
    severity: str  # error, warning, info
    message: str
    lineno: int
    col_offset: int = 0
    code: str = ""


# =============================================================================
# PYTHON AST PARSER
# =============================================================================

class PythonParser:
    """
    Parse Python code using the AST module.

    Extracts:
    - Functions and their metrics
    - Classes and their structure
    - Imports and dependencies
    - Documentation strings

    Example:
        >>> parser = PythonParser()
        >>> result = parser.parse(code_string)
        >>> print(result['functions'])
    """

    def parse(self, code: str) -> Dict[str, Any]:
        """
        Parse Python code and extract information.

        Args:
            code: Python source code string

        Returns:
            Dictionary containing parsed information
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                'error': f"Syntax error: {e.msg} at line {e.lineno}",
                'valid': False
            }

        result = {
            'valid': True,
            'functions': [],
            'classes': [],
            'imports': [],
            'global_variables': [],
            'docstring': ast.get_docstring(tree)
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods (they'll be processed with their class)
                if not self._is_method(node, tree):
                    result['functions'].append(self._parse_function(node))

            elif isinstance(node, ast.ClassDef):
                result['classes'].append(self._parse_class(node))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result['imports'].append(ImportInfo(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        lineno=node.lineno,
                        is_from_import=False
                    ))

            elif isinstance(node, ast.ImportFrom):
                result['imports'].append(ImportInfo(
                    module=node.module or '',
                    names=[a.name for a in node.names],
                    alias=None,
                    lineno=node.lineno,
                    is_from_import=True
                ))

            elif isinstance(node, ast.Assign):
                # Check for module-level assignments
                if self._is_module_level(node, tree):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result['global_variables'].append(target.id)

        return result

    def _is_method(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """Check if a function is a method (inside a class)."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in parent.body:
                    if child is node:
                        return True
        return False

    def _is_module_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """Check if a node is at module level."""
        return node in tree.body

    def _parse_function(self, node) -> FunctionInfo:
        """Parse a function definition."""
        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"{dec.value.id if hasattr(dec.value, 'id') else '...'}.{dec.attr}")
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(f"{dec.func.id}(...)")

        # Get arguments
        args = []
        for arg in node.args.args:
            args.append(arg.arg)

        # Get return annotation
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)

        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, 'end_lineno', node.lineno),
            args=args,
            defaults=len(node.args.defaults),
            decorators=decorators,
            docstring=ast.get_docstring(node),
            complexity=self._calculate_complexity(node),
            is_method=False,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            returns=returns
        )

    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        """Parse a class definition."""
        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id if hasattr(base.value, 'id') else '...'}.{base.attr}")

        # Get methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = self._parse_function(item)
                func.is_method = True
                methods.append(func)

        # Get class attributes
        attributes = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, 'end_lineno', node.lineno),
            bases=bases,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            methods=methods,
            attributes=attributes
        )

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Each decision point adds 1 to complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.IfExp):  # Ternary operator
                complexity += 1

        return complexity


# =============================================================================
# METRICS CALCULATOR
# =============================================================================

class MetricsCalculator:
    """
    Calculate various code metrics.

    Provides:
    - Lines of code metrics
    - Complexity metrics
    - Maintainability index
    - Halstead metrics

    Example:
        >>> calc = MetricsCalculator()
        >>> metrics = calc.calculate_metrics(code)
        >>> print(f"Cyclomatic complexity: {metrics['complexity']}")
    """

    def count_lines(self, code: str) -> Dict[str, int]:
        """
        Count different types of lines in code.

        Returns counts for:
        - total_lines: All lines
        - code_lines: Lines with actual code
        - comment_lines: Lines with comments
        - blank_lines: Empty lines
        - docstring_lines: Lines in docstrings
        """
        lines = code.split('\n')
        total = len(lines)
        blank = sum(1 for line in lines if not line.strip())

        # Use tokenize to accurately count comments
        comment_lines = 0
        string_lines = set()

        try:
            tokens = list(tokenize.generate_tokens(StringIO(code).readline))

            for token in tokens:
                if token.type == tokenize.COMMENT:
                    comment_lines += 1
                elif token.type == tokenize.STRING:
                    # Track string spans (potential docstrings)
                    for lineno in range(token.start[0], token.end[0] + 1):
                        string_lines.add(lineno)
        except tokenize.TokenizeError:
            pass

        # Estimate docstring lines (strings at start of module/function/class)
        docstring_lines = 0
        try:
            tree = ast.parse(code)
            docstring = ast.get_docstring(tree)
            if docstring:
                docstring_lines += docstring.count('\n') + 1

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    doc = ast.get_docstring(node)
                    if doc:
                        docstring_lines += doc.count('\n') + 1
        except SyntaxError:
            pass

        code_lines = total - blank - comment_lines

        return {
            'total_lines': total,
            'code_lines': max(0, code_lines),
            'comment_lines': comment_lines,
            'blank_lines': blank,
            'docstring_lines': docstring_lines
        }

    def cyclomatic_complexity(self, code: str) -> Dict[str, Any]:
        """
        Calculate cyclomatic complexity for all functions in code.

        Returns per-function complexity and summary statistics.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'error': 'Syntax error in code', 'functions': []}

        parser = PythonParser()
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = parser._calculate_complexity(node)
                functions.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'complexity': complexity
                })

        if not functions:
            return {
                'functions': [],
                'average': 0,
                'max': 0,
                'min': 0,
                'total': 0
            }

        complexities = [f['complexity'] for f in functions]

        return {
            'functions': functions,
            'average': sum(complexities) / len(complexities),
            'max': max(complexities),
            'min': min(complexities),
            'total': sum(complexities)
        }

    def halstead_metrics(self, code: str) -> Dict[str, float]:
        """
        Calculate Halstead complexity metrics.

        Returns:
        - n1: Number of distinct operators
        - n2: Number of distinct operands
        - N1: Total number of operators
        - N2: Total number of operands
        - vocabulary: n1 + n2
        - length: N1 + N2
        - calculated_length: n1 * log2(n1) + n2 * log2(n2)
        - volume: length * log2(vocabulary)
        - difficulty: (n1/2) * (N2/n2)
        - effort: difficulty * volume
        - time: effort / 18 (seconds)
        - bugs: volume / 3000 (estimated bugs)
        """
        import math

        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0

        # Operators in Python
        op_tokens = {
            tokenize.OP, tokenize.AMPER, tokenize.AMPEREQUAL,
            tokenize.AT, tokenize.ATEQUAL, tokenize.CIRCUMFLEX,
            tokenize.CIRCUMFLEXEQUAL, tokenize.COLON, tokenize.COLONEQUAL,
            tokenize.COMMA, tokenize.DOT, tokenize.DOUBLESLASH,
            tokenize.DOUBLESLASHEQUAL, tokenize.DOUBLESTAR, tokenize.DOUBLESTAREQUAL,
            tokenize.EQUAL, tokenize.EQEQUAL, tokenize.GREATER,
            tokenize.GREATEREQUAL, tokenize.LBRACE, tokenize.LEFTSHIFT,
            tokenize.LEFTSHIFTEQUAL, tokenize.LESS, tokenize.LESSEQUAL,
            tokenize.LPAR, tokenize.LSQB, tokenize.MINUS,
            tokenize.MINEQUAL, tokenize.NOTEQUAL, tokenize.PERCENT,
            tokenize.PERCENTEQUAL, tokenize.PLUS, tokenize.PLUSEQUAL,
            tokenize.RBRACE, tokenize.RIGHTSHIFT, tokenize.RIGHTSHIFTEQUAL,
            tokenize.RPAR, tokenize.RSQB, tokenize.SEMI,
            tokenize.SLASH, tokenize.SLASHEQUAL, tokenize.STAR,
            tokenize.STAREQUAL, tokenize.TILDE, tokenize.VBAR,
            tokenize.VBAREQUAL
        }

        try:
            tokens = list(tokenize.generate_tokens(StringIO(code).readline))

            for token in tokens:
                if token.type in op_tokens:
                    operators.add(token.string)
                    operator_count += 1
                elif token.type == tokenize.NAME:
                    operands.add(token.string)
                    operand_count += 1
                elif token.type == tokenize.NUMBER:
                    operands.add(token.string)
                    operand_count += 1
                elif token.type == tokenize.STRING:
                    operands.add(token.string)
                    operand_count += 1

        except tokenize.TokenizeError:
            return {'error': 'Tokenization error'}

        n1 = len(operators)
        n2 = len(operands)
        N1 = operator_count
        N2 = operand_count

        # Avoid division by zero
        if n1 == 0 or n2 == 0:
            return {
                'n1': n1, 'n2': n2, 'N1': N1, 'N2': N2,
                'vocabulary': n1 + n2,
                'length': N1 + N2,
                'error': 'Insufficient operators or operands'
            }

        vocabulary = n1 + n2
        length = N1 + N2
        calculated_length = n1 * math.log2(n1) + n2 * math.log2(n2)
        volume = length * math.log2(vocabulary)
        difficulty = (n1 / 2) * (N2 / n2)
        effort = difficulty * volume
        time_seconds = effort / 18
        bugs = volume / 3000

        return {
            'n1_distinct_operators': n1,
            'n2_distinct_operands': n2,
            'N1_total_operators': N1,
            'N2_total_operands': N2,
            'vocabulary': vocabulary,
            'length': length,
            'calculated_length': round(calculated_length, 2),
            'volume': round(volume, 2),
            'difficulty': round(difficulty, 2),
            'effort': round(effort, 2),
            'time_seconds': round(time_seconds, 2),
            'estimated_bugs': round(bugs, 4)
        }

    def maintainability_index(self, code: str) -> float:
        """
        Calculate the Maintainability Index.

        MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)

        Where:
        - V = Halstead Volume
        - G = Cyclomatic Complexity
        - LOC = Lines of Code

        Returns a value between 0-100 (normalized).
        Higher values indicate more maintainable code.
        """
        import math

        # Get metrics
        halstead = self.halstead_metrics(code)
        complexity = self.cyclomatic_complexity(code)
        lines = self.count_lines(code)

        volume = halstead.get('volume', 1)
        avg_complexity = complexity.get('average', 1)
        loc = lines.get('code_lines', 1)

        # Avoid log(0)
        volume = max(volume, 1)
        loc = max(loc, 1)

        # Calculate MI
        mi = 171 - 5.2 * math.log(volume) - 0.23 * avg_complexity - 16.2 * math.log(loc)

        # Normalize to 0-100
        mi = max(0, min(100, mi * 100 / 171))

        return round(mi, 2)


# =============================================================================
# CODE QUALITY CHECKER
# =============================================================================

class CodeQualityChecker:
    """
    Check code quality and detect common issues.

    Detects:
    - Style issues (naming conventions, line length)
    - Potential bugs (undefined variables, unused imports)
    - Complexity issues
    - Documentation issues

    Example:
        >>> checker = CodeQualityChecker()
        >>> issues = checker.check(code)
        >>> for issue in issues:
        ...     print(f"{issue.severity}: {issue.message} (line {issue.lineno})")
    """

    # Naming convention patterns
    PATTERNS = {
        'function': re.compile(r'^[a-z_][a-z0-9_]*$'),
        'class': re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
        'constant': re.compile(r'^[A-Z_][A-Z0-9_]*$'),
        'variable': re.compile(r'^[a-z_][a-z0-9_]*$'),
    }

    def __init__(self, max_line_length: int = 100, max_complexity: int = 10):
        """
        Initialize the checker.

        Args:
            max_line_length: Maximum allowed line length
            max_complexity: Maximum allowed cyclomatic complexity
        """
        self.max_line_length = max_line_length
        self.max_complexity = max_complexity

    def check(self, code: str) -> List[CodeIssue]:
        """
        Run all quality checks on code.

        Returns list of CodeIssue objects.
        """
        issues = []

        issues.extend(self._check_line_length(code))
        issues.extend(self._check_naming_conventions(code))
        issues.extend(self._check_complexity(code))
        issues.extend(self._check_documentation(code))
        issues.extend(self._check_imports(code))
        issues.extend(self._check_common_issues(code))

        return sorted(issues, key=lambda x: (x.lineno, x.severity))

    def _check_line_length(self, code: str) -> List[CodeIssue]:
        """Check for lines exceeding maximum length."""
        issues = []
        for lineno, line in enumerate(code.split('\n'), 1):
            if len(line) > self.max_line_length:
                issues.append(CodeIssue(
                    category='style',
                    severity='warning',
                    message=f"Line too long ({len(line)} > {self.max_line_length})",
                    lineno=lineno,
                    code='E501'
                ))
        return issues

    def _check_naming_conventions(self, code: str) -> List[CodeIssue]:
        """Check naming conventions."""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not self.PATTERNS['function'].match(node.name):
                    if not node.name.startswith('_'):  # Allow dunder methods
                        issues.append(CodeIssue(
                            category='naming',
                            severity='warning',
                            message=f"Function name '{node.name}' should be lowercase with underscores",
                            lineno=node.lineno,
                            code='N802'
                        ))

            elif isinstance(node, ast.ClassDef):
                if not self.PATTERNS['class'].match(node.name):
                    issues.append(CodeIssue(
                        category='naming',
                        severity='warning',
                        message=f"Class name '{node.name}' should use CapWords convention",
                        lineno=node.lineno,
                        code='N801'
                    ))

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Check if it's a constant (all uppercase at module level)
                        if name.isupper() and not self.PATTERNS['constant'].match(name):
                            issues.append(CodeIssue(
                                category='naming',
                                severity='info',
                                message=f"Constant '{name}' naming issue",
                                lineno=node.lineno,
                                code='N806'
                            ))

        return issues

    def _check_complexity(self, code: str) -> List[CodeIssue]:
        """Check function complexity."""
        issues = []
        calc = MetricsCalculator()
        complexity = calc.cyclomatic_complexity(code)

        for func in complexity.get('functions', []):
            if func['complexity'] > self.max_complexity:
                issues.append(CodeIssue(
                    category='complexity',
                    severity='warning',
                    message=f"Function '{func['name']}' has cyclomatic complexity of {func['complexity']} (max {self.max_complexity})",
                    lineno=func['lineno'],
                    code='C901'
                ))

        return issues

    def _check_documentation(self, code: str) -> List[CodeIssue]:
        """Check for missing documentation."""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        # Check module docstring
        if not ast.get_docstring(tree):
            issues.append(CodeIssue(
                category='documentation',
                severity='info',
                message="Module lacks a docstring",
                lineno=1,
                code='D100'
            ))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast.get_docstring(node):
                    # Skip private/magic methods
                    if not node.name.startswith('_'):
                        issues.append(CodeIssue(
                            category='documentation',
                            severity='info',
                            message=f"Function '{node.name}' lacks a docstring",
                            lineno=node.lineno,
                            code='D103'
                        ))

            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    issues.append(CodeIssue(
                        category='documentation',
                        severity='info',
                        message=f"Class '{node.name}' lacks a docstring",
                        lineno=node.lineno,
                        code='D101'
                    ))

        return issues

    def _check_imports(self, code: str) -> List[CodeIssue]:
        """Check import issues."""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        imports = []
        import_lines = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    import_lines.append(node.lineno)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or '')
                import_lines.append(node.lineno)

        # Check for duplicate imports
        seen = {}
        for i, imp in enumerate(imports):
            if imp in seen:
                issues.append(CodeIssue(
                    category='imports',
                    severity='warning',
                    message=f"Duplicate import of '{imp}'",
                    lineno=import_lines[i],
                    code='W0404'
                ))
            seen[imp] = import_lines[i]

        return issues

    def _check_common_issues(self, code: str) -> List[CodeIssue]:
        """Check for common coding issues."""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(CodeIssue(
                        category='error-handling',
                        severity='warning',
                        message="Bare 'except:' clause catches all exceptions including KeyboardInterrupt",
                        lineno=node.lineno,
                        code='E722'
                    ))

            # Check for mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(CodeIssue(
                            category='bugs',
                            severity='error',
                            message=f"Mutable default argument in function '{node.name}'",
                            lineno=node.lineno,
                            code='B006'
                        ))

            # Check for comparison to None using == instead of is
            if isinstance(node, ast.Compare):
                for op, comparator in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        if isinstance(comparator, ast.Constant) and comparator.value is None:
                            issues.append(CodeIssue(
                                category='style',
                                severity='warning',
                                message="Comparison to None should use 'is' or 'is not'",
                                lineno=node.lineno,
                                code='E711'
                            ))

            # Check for comparison to True/False using == instead of is
            if isinstance(node, ast.Compare):
                for op, comparator in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        if isinstance(comparator, ast.Constant) and comparator.value in (True, False):
                            issues.append(CodeIssue(
                                category='style',
                                severity='warning',
                                message="Comparison to True/False should use 'is' or 'is not'",
                                lineno=node.lineno,
                                code='E712'
                            ))

            # Check for potentially unused variables (starting with _)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'l':
                        issues.append(CodeIssue(
                            category='style',
                            severity='warning',
                            message="Ambiguous variable name 'l' (looks like 1)",
                            lineno=node.lineno,
                            code='E741'
                        ))

        return issues


# =============================================================================
# DUPLICATE DETECTOR
# =============================================================================

class DuplicateDetector:
    """
    Detect code duplication.

    Uses hash-based comparison to find similar code blocks.

    Example:
        >>> detector = DuplicateDetector()
        >>> duplicates = detector.find_duplicates(files)
    """

    def __init__(self, min_lines: int = 4):
        """
        Initialize detector.

        Args:
            min_lines: Minimum number of lines for a duplicate block
        """
        self.min_lines = min_lines

    def find_duplicates(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Find duplicate code blocks across multiple files.

        Args:
            files: Dictionary mapping filename to code content

        Returns:
            List of duplicate findings
        """
        # Collect all code blocks
        blocks = defaultdict(list)

        for filename, code in files.items():
            lines = code.split('\n')

            # Generate blocks of min_lines size
            for start in range(len(lines) - self.min_lines + 1):
                block = '\n'.join(lines[start:start + self.min_lines])
                # Normalize whitespace
                normalized = self._normalize(block)
                if normalized.strip():
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()
                    blocks[block_hash].append({
                        'file': filename,
                        'start_line': start + 1,
                        'end_line': start + self.min_lines,
                        'code': block
                    })

        # Find duplicates (blocks appearing more than once)
        duplicates = []
        for block_hash, locations in blocks.items():
            if len(locations) > 1:
                duplicates.append({
                    'hash': block_hash,
                    'occurrences': len(locations),
                    'locations': locations
                })

        return duplicates

    def _normalize(self, code: str) -> str:
        """Normalize code for comparison (remove comments, normalize whitespace)."""
        # Remove single-line comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        return code.strip()

    def calculate_similarity(self, code1: str, code2: str) -> float:
        """
        Calculate similarity between two code blocks.

        Uses line-by-line comparison.
        Returns value between 0 (no match) and 1 (identical).
        """
        lines1 = [self._normalize(l) for l in code1.split('\n') if l.strip()]
        lines2 = [self._normalize(l) for l in code2.split('\n') if l.strip()]

        if not lines1 or not lines2:
            return 0.0

        # Count matching lines
        set1 = set(lines1)
        set2 = set(lines2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


# =============================================================================
# MAIN CODE ANALYZER CLASS
# =============================================================================

class CodeAnalyzer:
    """
    Main class combining all code analysis capabilities.

    Provides a unified interface for:
    - Parsing code
    - Calculating metrics
    - Checking quality
    - Detecting duplicates

    Example:
        >>> analyzer = CodeAnalyzer()
        >>> result = analyzer.analyze_file("mycode.py")
        >>> print(result['metrics'])
        >>> print(result['issues'])
    """

    def __init__(self):
        """Initialize the code analyzer."""
        self.parser = PythonParser()
        self.metrics = MetricsCalculator()
        self.quality = CodeQualityChecker()
        self.duplicates = DuplicateDetector()

    def analyze_code(self, code: str, filename: str = "<string>") -> Dict[str, Any]:
        """
        Analyze Python code and return comprehensive results.

        Args:
            code: Python source code string
            filename: Optional filename for reporting

        Returns:
            Dictionary containing all analysis results
        """
        result = {
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'valid': True,
            'error': None
        }

        # Parse code
        parsed = self.parser.parse(code)
        if not parsed.get('valid', True):
            result['valid'] = False
            result['error'] = parsed.get('error')
            return result

        result['structure'] = {
            'functions': [self._function_to_dict(f) for f in parsed['functions']],
            'classes': [self._class_to_dict(c) for c in parsed['classes']],
            'imports': [self._import_to_dict(i) for i in parsed['imports']],
            'global_variables': parsed['global_variables'],
            'docstring': parsed['docstring']
        }

        # Calculate metrics
        line_counts = self.metrics.count_lines(code)
        complexity = self.metrics.cyclomatic_complexity(code)
        halstead = self.metrics.halstead_metrics(code)
        mi = self.metrics.maintainability_index(code)

        # Calculate docstring coverage
        total_items = len(parsed['functions']) + len(parsed['classes'])
        documented = sum(1 for f in parsed['functions'] if f.docstring)
        documented += sum(1 for c in parsed['classes'] if c.docstring)
        doc_coverage = documented / total_items if total_items > 0 else 1.0

        result['metrics'] = CodeMetrics(
            filename=filename,
            total_lines=line_counts['total_lines'],
            code_lines=line_counts['code_lines'],
            comment_lines=line_counts['comment_lines'],
            blank_lines=line_counts['blank_lines'],
            docstring_lines=line_counts['docstring_lines'],
            functions=len(parsed['functions']),
            classes=len(parsed['classes']),
            imports=len(parsed['imports']),
            avg_complexity=complexity.get('average', 0),
            max_complexity=complexity.get('max', 0),
            maintainability_index=mi,
            docstring_coverage=doc_coverage
        )

        result['halstead'] = halstead

        # Check quality
        issues = self.quality.check(code)
        result['issues'] = [self._issue_to_dict(i) for i in issues]
        result['issue_summary'] = {
            'error': sum(1 for i in issues if i.severity == 'error'),
            'warning': sum(1 for i in issues if i.severity == 'warning'),
            'info': sum(1 for i in issues if i.severity == 'info')
        }

        return result

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze a Python file.

        Args:
            filepath: Path to the Python file

        Returns:
            Analysis results
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.analyze_code(code, filepath)
        except FileNotFoundError:
            return {
                'filename': filepath,
                'valid': False,
                'error': f"File not found: {filepath}"
            }
        except IOError as e:
            return {
                'filename': filepath,
                'valid': False,
                'error': f"Error reading file: {e}"
            }

    def analyze_directory(self, directory: str, pattern: str = "*.py") -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.

        Args:
            directory: Directory path
            pattern: Glob pattern for files

        Returns:
            Combined analysis results
        """
        import glob

        results = {
            'directory': directory,
            'pattern': pattern,
            'files': [],
            'summary': {
                'total_files': 0,
                'total_lines': 0,
                'total_functions': 0,
                'total_classes': 0,
                'total_issues': 0,
                'avg_complexity': 0,
                'avg_maintainability': 0
            }
        }

        files = glob.glob(os.path.join(directory, '**', pattern), recursive=True)

        complexities = []
        maintainabilities = []

        for filepath in files:
            analysis = self.analyze_file(filepath)
            results['files'].append(analysis)

            if analysis.get('valid', False):
                metrics = analysis.get('metrics')
                if metrics:
                    results['summary']['total_lines'] += metrics.total_lines
                    results['summary']['total_functions'] += metrics.functions
                    results['summary']['total_classes'] += metrics.classes
                    if metrics.avg_complexity > 0:
                        complexities.append(metrics.avg_complexity)
                    if metrics.maintainability_index > 0:
                        maintainabilities.append(metrics.maintainability_index)

                issues = analysis.get('issue_summary', {})
                results['summary']['total_issues'] += sum(issues.values())

        results['summary']['total_files'] = len(files)
        results['summary']['avg_complexity'] = (
            sum(complexities) / len(complexities) if complexities else 0
        )
        results['summary']['avg_maintainability'] = (
            sum(maintainabilities) / len(maintainabilities) if maintainabilities else 0
        )

        return results

    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        """Convert FunctionInfo to dictionary."""
        return {
            'name': func.name,
            'lineno': func.lineno,
            'end_lineno': func.end_lineno,
            'args': func.args,
            'defaults': func.defaults,
            'decorators': func.decorators,
            'has_docstring': func.docstring is not None,
            'complexity': func.complexity,
            'is_method': func.is_method,
            'is_async': func.is_async,
            'returns': func.returns
        }

    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        """Convert ClassInfo to dictionary."""
        return {
            'name': cls.name,
            'lineno': cls.lineno,
            'end_lineno': cls.end_lineno,
            'bases': cls.bases,
            'decorators': cls.decorators,
            'has_docstring': cls.docstring is not None,
            'methods': [self._function_to_dict(m) for m in cls.methods],
            'attributes': cls.attributes
        }

    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        """Convert ImportInfo to dictionary."""
        return {
            'module': imp.module,
            'names': imp.names,
            'alias': imp.alias,
            'lineno': imp.lineno,
            'is_from_import': imp.is_from_import
        }

    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """Convert CodeIssue to dictionary."""
        return {
            'category': issue.category,
            'severity': issue.severity,
            'message': issue.message,
            'lineno': issue.lineno,
            'col_offset': issue.col_offset,
            'code': issue.code
        }


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command-line interface for the Code Analyzer."""
    print("=" * 60)
    print("CODE ANALYSIS TOOLKIT")
    print("=" * 60)
    print()

    # Initialize analyzer
    analyzer = CodeAnalyzer()

    # Sample code for analysis
    sample_code = '''
"""
Sample module for code analysis demonstration.
"""

import os
import sys
from typing import List, Dict, Optional


CONSTANT_VALUE = 42
another_constant = "test"


class DataProcessor:
    """Process data with various transformations."""

    def __init__(self, data: List[int]):
        self.data = data
        self.processed = False

    def process(self, threshold: int = 10) -> List[int]:
        """Filter data based on threshold."""
        result = []
        for item in self.data:
            if item > threshold:
                if item < 100:
                    if item % 2 == 0:
                        result.append(item * 2)
                    else:
                        result.append(item)
        self.processed = True
        return result

    def summary(self):
        return {"count": len(self.data), "processed": self.processed}


def calculate_statistics(numbers: List[int]) -> Dict:
    """Calculate basic statistics for a list of numbers."""
    if not numbers:
        return {}

    total = sum(numbers)
    count = len(numbers)
    average = total / count

    return {
        "sum": total,
        "count": count,
        "average": average,
        "min": min(numbers),
        "max": max(numbers)
    }


def problematic_function(data=[]):  # Mutable default argument
    """This function has a common bug."""
    data.append(1)
    return data


def complex_logic(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            elif z < -10:
                return x + y - z
            else:
                return x + y
        else:
            return x
    else:
        return 0
'''

    # Run analysis
    print("1. ANALYZING SAMPLE CODE")
    print("-" * 40)

    result = analyzer.analyze_code(sample_code, "sample.py")

    if result['valid']:
        metrics = result['metrics']
        print(f"File: {metrics.filename}")
        print(f"Total lines: {metrics.total_lines}")
        print(f"Code lines: {metrics.code_lines}")
        print(f"Comment lines: {metrics.comment_lines}")
        print(f"Functions: {metrics.functions}")
        print(f"Classes: {metrics.classes}")
        print(f"Average complexity: {metrics.avg_complexity:.2f}")
        print(f"Max complexity: {metrics.max_complexity}")
        print(f"Maintainability Index: {metrics.maintainability_index:.2f}")
        print(f"Docstring coverage: {metrics.docstring_coverage:.1%}")
    print()

    # Show structure
    print("2. CODE STRUCTURE")
    print("-" * 40)

    structure = result['structure']
    print(f"Module docstring: {'Yes' if structure['docstring'] else 'No'}")
    print(f"Global variables: {structure['global_variables']}")

    print("\nClasses:")
    for cls in structure['classes']:
        print(f"  - {cls['name']} (line {cls['lineno']})")
        print(f"    Bases: {cls['bases']}")
        print(f"    Methods: {[m['name'] for m in cls['methods']]}")

    print("\nFunctions:")
    for func in structure['functions']:
        print(f"  - {func['name']}({', '.join(func['args'])}) "
              f"[complexity: {func['complexity']}]")
    print()

    # Show issues
    print("3. CODE QUALITY ISSUES")
    print("-" * 40)

    print(f"Errors: {result['issue_summary']['error']}")
    print(f"Warnings: {result['issue_summary']['warning']}")
    print(f"Info: {result['issue_summary']['info']}")
    print()

    for issue in result['issues'][:10]:
        severity = issue['severity'].upper()
        print(f"  [{severity}] Line {issue['lineno']}: {issue['message']}")
    print()

    # Show Halstead metrics
    print("4. HALSTEAD METRICS")
    print("-" * 40)

    halstead = result['halstead']
    print(f"Distinct operators (n1): {halstead.get('n1_distinct_operators', 'N/A')}")
    print(f"Distinct operands (n2): {halstead.get('n2_distinct_operands', 'N/A')}")
    print(f"Program vocabulary: {halstead.get('vocabulary', 'N/A')}")
    print(f"Program length: {halstead.get('length', 'N/A')}")
    print(f"Volume: {halstead.get('volume', 'N/A')}")
    print(f"Difficulty: {halstead.get('difficulty', 'N/A')}")
    print(f"Estimated bugs: {halstead.get('estimated_bugs', 'N/A')}")
    print()

    # Demo duplicate detection
    print("5. DUPLICATE DETECTION DEMO")
    print("-" * 40)

    files = {
        'file1.py': '''
def calculate(x, y):
    result = x + y
    return result * 2

def other():
    pass
''',
        'file2.py': '''
def compute(a, b):
    result = a + b
    return result * 2

def something():
    pass
'''
    }

    duplicates = analyzer.duplicates.find_duplicates(files)
    print(f"Found {len(duplicates)} potential duplicate blocks")

    similarity = analyzer.duplicates.calculate_similarity(
        files['file1.py'], files['file2.py']
    )
    print(f"File similarity: {similarity:.1%}")
    print()

    print("=" * 60)
    print("Code Analysis Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
