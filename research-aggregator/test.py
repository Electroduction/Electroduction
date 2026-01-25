#!/usr/bin/env python3
"""
Research Aggregator - Test Script
=================================
Tests the complete research aggregator system for:
1. File structure integrity
2. HTML validity
3. CSS syntax
4. JavaScript syntax (basic)
5. JSON configuration files
6. Portal completeness

Run: python3 test.py
"""

import os
import json
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"  {Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    print(f"  {Colors.RED}✗{Colors.END} {text}")

def print_warning(text):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text):
    print(f"  {Colors.BLUE}ℹ{Colors.END} {text}")

# Base directory
BASE_DIR = Path(__file__).parent

# Expected structure
EXPECTED_STRUCTURE = {
    'index.html': 'Main dashboard',
    'css/main.css': 'Main stylesheet',
    'js/core.js': 'Core JavaScript engine',
    'portals/computer-science.html': 'Computer Science portal',
    'portals/cybersecurity.html': 'Cybersecurity portal',
    'portals/finance.html': 'Finance portal',
    'portals/legal.html': 'Legal portal',
    'portals/hr.html': 'Human Resources portal',
    'portals/electrical.html': 'Electrical Trade portal',
    'data/feeds-cs.json': 'CS feed configuration',
    'data/feeds-cybersecurity.json': 'Cybersecurity feed configuration',
}

def test_file_structure():
    """Test that all required files exist"""
    print_header("Testing File Structure")

    passed = 0
    failed = 0

    for file_path, description in EXPECTED_STRUCTURE.items():
        full_path = BASE_DIR / file_path
        if full_path.exists():
            print_success(f"{file_path} - {description}")
            passed += 1
        else:
            print_error(f"MISSING: {file_path} - {description}")
            failed += 1

    return passed, failed

def test_html_files():
    """Basic HTML validation"""
    print_header("Testing HTML Files")

    passed = 0
    failed = 0
    warnings = 0

    html_files = list(BASE_DIR.glob('**/*.html'))

    for html_file in html_files:
        try:
            content = html_file.read_text(encoding='utf-8')
            errors = []

            # Check for DOCTYPE
            if '<!DOCTYPE html>' not in content and '<!doctype html>' not in content:
                errors.append("Missing DOCTYPE declaration")

            # Check for basic structure
            if '<html' not in content:
                errors.append("Missing <html> tag")
            if '<head>' not in content:
                errors.append("Missing <head> tag")
            if '<body' not in content:
                errors.append("Missing <body> tag")

            # Check for charset
            if 'charset' not in content.lower():
                errors.append("Missing charset declaration")

            # Check for viewport
            if 'viewport' not in content:
                errors.append("Missing viewport meta tag")

            # Check for CSS link
            if 'main.css' not in content and html_file.name != 'index.html':
                errors.append("Missing CSS stylesheet link")

            # Check for JS script
            if 'core.js' not in content and html_file.name != 'index.html':
                errors.append("Missing core.js script")

            if errors:
                print_warning(f"{html_file.relative_to(BASE_DIR)}")
                for error in errors:
                    print_error(f"  └─ {error}")
                warnings += 1
            else:
                print_success(f"{html_file.relative_to(BASE_DIR)}")
                passed += 1

        except Exception as e:
            print_error(f"{html_file.relative_to(BASE_DIR)}: {str(e)}")
            failed += 1

    return passed, failed, warnings

def test_css_file():
    """Basic CSS validation"""
    print_header("Testing CSS Files")

    passed = 0
    failed = 0

    css_file = BASE_DIR / 'css' / 'main.css'

    if not css_file.exists():
        print_error("main.css not found")
        return 0, 1

    try:
        content = css_file.read_text(encoding='utf-8')

        # Check for CSS variables
        if ':root' in content:
            print_success("CSS variables defined in :root")
            passed += 1
        else:
            print_warning("No CSS variables found in :root")

        # Check for portal themes
        if '[data-portal=' in content:
            print_success("Portal-specific themes defined")
            passed += 1
        else:
            print_warning("No portal themes found")

        # Check for glossary/definition styles
        if '.glossary-term' in content:
            print_success("Glossary term styles defined")
            passed += 1
        else:
            print_error("Missing .glossary-term styles")
            failed += 1

        if '#definition-window' in content:
            print_success("Definition window styles defined")
            passed += 1
        else:
            print_error("Missing #definition-window styles")
            failed += 1

        # Check for responsive design
        if '@media' in content:
            print_success("Responsive media queries present")
            passed += 1
        else:
            print_warning("No responsive media queries found")

        # Check brace balance (basic)
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces == close_braces:
            print_success(f"CSS braces balanced ({open_braces} pairs)")
            passed += 1
        else:
            print_error(f"CSS braces unbalanced: {open_braces} open, {close_braces} close")
            failed += 1

    except Exception as e:
        print_error(f"Error reading CSS: {str(e)}")
        failed += 1

    return passed, failed

def test_javascript():
    """Basic JavaScript validation"""
    print_header("Testing JavaScript")

    passed = 0
    failed = 0

    js_file = BASE_DIR / 'js' / 'core.js'

    if not js_file.exists():
        print_error("core.js not found")
        return 0, 1

    try:
        content = js_file.read_text(encoding='utf-8')

        # Check for main classes
        required_classes = [
            'RSSAggregator',
            'GlossarySystem',
            'ContentLengthManager',
            'GuideIndexSystem',
            'SearchSystem',
            'ResearchAggregator'
        ]

        for cls in required_classes:
            if f'class {cls}' in content:
                print_success(f"Class {cls} defined")
                passed += 1
            else:
                print_error(f"Missing class: {cls}")
                failed += 1

        # Check for initialization
        if 'DOMContentLoaded' in content:
            print_success("DOM ready handler present")
            passed += 1
        else:
            print_warning("No DOMContentLoaded handler found")

        # Check brace balance
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces == close_braces:
            print_success(f"JavaScript braces balanced ({open_braces} pairs)")
            passed += 1
        else:
            print_error(f"JavaScript braces unbalanced: {open_braces} open, {close_braces} close")
            failed += 1

    except Exception as e:
        print_error(f"Error reading JavaScript: {str(e)}")
        failed += 1

    return passed, failed

def test_json_configs():
    """Test JSON configuration files"""
    print_header("Testing JSON Configuration Files")

    passed = 0
    failed = 0

    json_files = list((BASE_DIR / 'data').glob('*.json'))

    if not json_files:
        print_warning("No JSON configuration files found")
        return 0, 0

    for json_file in json_files:
        try:
            content = json_file.read_text(encoding='utf-8')
            data = json.loads(content)

            # Check for required fields
            if 'feeds' in data:
                feed_count = len(data['feeds'])
                print_success(f"{json_file.name}: Valid JSON with {feed_count} feeds")
                passed += 1
            else:
                print_warning(f"{json_file.name}: Valid JSON but missing 'feeds' array")
                passed += 1

        except json.JSONDecodeError as e:
            print_error(f"{json_file.name}: Invalid JSON - {str(e)}")
            failed += 1
        except Exception as e:
            print_error(f"{json_file.name}: Error - {str(e)}")
            failed += 1

    return passed, failed

def test_glossary_terms():
    """Test that portals have glossary terms"""
    print_header("Testing Glossary Terms in Portals")

    passed = 0
    failed = 0

    portal_files = list((BASE_DIR / 'portals').glob('*.html'))

    for portal in portal_files:
        try:
            content = portal.read_text(encoding='utf-8')

            # Count glossary terms
            term_count = content.count('glossary-term')

            # Count glossary definitions in script
            if 'Glossary' in content or 'glossary' in content.lower():
                definition_count = content.count("term:")
                print_success(f"{portal.name}: {term_count} terms in content, ~{definition_count//2} definitions")
                passed += 1
            else:
                print_warning(f"{portal.name}: {term_count} terms but no glossary script found")

        except Exception as e:
            print_error(f"{portal.name}: Error - {str(e)}")
            failed += 1

    return passed, failed

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")

    total_passed = sum(r[0] for r in results)
    total_failed = sum(r[1] for r in results)
    total_warnings = sum(r[2] if len(r) > 2 else 0 for r in results)

    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.END}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.END}")
    if total_warnings:
        print(f"  {Colors.YELLOW}Warnings: {total_warnings}{Colors.END}")

    print()

    if total_failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}All critical tests passed!{Colors.END}")
        print(f"\n{Colors.BLUE}To view the website, run:{Colors.END}")
        print(f"  cd {BASE_DIR}")
        print(f"  python3 -m http.server 8080")
        print(f"\nThen open: http://localhost:8080")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}Some tests failed. Please review the errors above.{Colors.END}")
        return 1

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}Research Aggregator - System Test{Colors.END}")
    print(f"Testing directory: {BASE_DIR}\n")

    results = []

    # Run tests
    results.append(test_file_structure())
    results.append(test_html_files())
    results.append(test_css_file())
    results.append(test_javascript())
    results.append(test_json_configs())
    results.append(test_glossary_terms())

    # Print summary
    exit_code = print_summary(results)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
