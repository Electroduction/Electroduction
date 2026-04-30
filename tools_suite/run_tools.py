#!/usr/bin/env python3
"""
Tools Suite Master Runner
=========================

Central script to run and demonstrate all tools in the suite.

Usage:
------
    python3 run_tools.py --list              # List all available tools
    python3 run_tools.py --tool statistics   # Run specific tool demo
    python3 run_tools.py --all               # Run all tool demos
    python3 run_tools.py --help              # Show help

Author: Electroduction Security Team
Version: 1.0.0
"""

import os
import sys
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime


# =============================================================================
# TOOL REGISTRY
# =============================================================================

TOOLS = {
    # Data Science
    'statistics': {
        'name': 'Statistics Toolkit',
        'module': 'data_science.statistics_toolkit',
        'description': 'Statistical analysis, DataFrame operations, regression',
        'category': 'Data Science'
    },

    # Finance
    'finance': {
        'name': 'Financial Toolkit',
        'module': 'finance.financial_toolkit',
        'description': 'NPV, IRR, Black-Scholes, risk metrics, TVM calculations',
        'category': 'Finance'
    },

    # Research
    'research': {
        'name': 'Research Toolkit',
        'module': 'research.research_toolkit',
        'description': 'Text analysis, citations, data extraction, document comparison',
        'category': 'Research'
    },

    # Network
    'network': {
        'name': 'Network Analyzer',
        'module': 'network.network_analyzer',
        'description': 'Packet parsing, traffic analysis, network scanning',
        'category': 'Network'
    },

    # Code Analysis
    'code': {
        'name': 'Code Analyzer',
        'module': 'code_analysis.code_analyzer',
        'description': 'Code metrics, complexity analysis, quality checking',
        'category': 'Development'
    },

    # Data Gathering
    'scraper': {
        'name': 'Data Collector',
        'module': 'data_gathering.data_collector',
        'description': 'Web scraping, HTML parsing, data extraction',
        'category': 'Data Collection'
    },

    # Database
    'database': {
        'name': 'Database Toolkit',
        'module': 'database.database_toolkit',
        'description': 'SQLite ORM, query builder, migrations',
        'category': 'Database'
    },

    # API
    'api': {
        'name': 'API Toolkit',
        'module': 'api.api_toolkit',
        'description': 'REST client, request builder, mocking, validation',
        'category': 'API'
    },

    # System Admin
    'sysadmin': {
        'name': 'System Admin Toolkit',
        'module': 'sysadmin.sysadmin_toolkit',
        'description': 'Process management, disk monitoring, service control',
        'category': 'System Administration'
    },

    # Cryptography
    'crypto': {
        'name': 'Cryptography Toolkit',
        'module': 'crypto.crypto_toolkit',
        'description': 'Hashing, encryption, password generation',
        'category': 'Security'
    },

    # Automation
    'automation': {
        'name': 'Automation Toolkit',
        'module': 'automation.automation_toolkit',
        'description': 'Task scheduling, file watching, batch processing',
        'category': 'Automation'
    },

    # File Processing
    'files': {
        'name': 'File Processing Toolkit',
        'module': 'file_processing.file_toolkit',
        'description': 'File conversion, comparison, batch operations',
        'category': 'File Processing'
    },
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_tools_dir() -> Path:
    """Get the tools suite directory."""
    return Path(__file__).parent.absolute()


def print_header(title: str):
    """Print a formatted header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_section(title: str):
    """Print a section header."""
    print()
    print(f"--- {title} ---")
    print()


def list_tools():
    """List all available tools."""
    print_header("TOOLS SUITE - Available Tools")

    # Group by category
    categories = {}
    for key, info in TOOLS.items():
        cat = info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, info))

    for category in sorted(categories.keys()):
        print(f"\n{category}:")
        print("-" * 40)
        for key, info in sorted(categories[category]):
            # Check if module exists
            module_path = get_tools_dir() / info['module'].replace('.', '/')
            module_file = str(module_path) + '.py'
            exists = os.path.exists(module_file)
            status = "✓" if exists else "○"

            print(f"  {status} {key:12} - {info['name']}")
            print(f"                   {info['description']}")

    print()
    print("Legend: ✓ = Available, ○ = Planned")
    print()
    print("Usage:")
    print("  python3 run_tools.py --tool <name>   Run specific tool demo")
    print("  python3 run_tools.py --all           Run all available tool demos")
    print()


def run_tool(tool_key: str) -> bool:
    """
    Run a specific tool's demo.

    Returns True if successful, False otherwise.
    """
    if tool_key not in TOOLS:
        print(f"Error: Unknown tool '{tool_key}'")
        print(f"Use --list to see available tools")
        return False

    info = TOOLS[tool_key]
    module_path = get_tools_dir() / info['module'].replace('.', '/')
    module_file = str(module_path) + '.py'

    if not os.path.exists(module_file):
        print(f"Tool '{tool_key}' ({info['name']}) is not yet implemented.")
        return False

    print_header(f"Running: {info['name']}")
    print(f"Module: {info['module']}")
    print(f"Category: {info['category']}")
    print(f"Description: {info['description']}")
    print()

    try:
        # Load and run the module
        spec = importlib.util.spec_from_file_location(info['module'], module_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[info['module']] = module
        spec.loader.exec_module(module)

        # Run main if it exists
        if hasattr(module, 'main'):
            result = module.main()
            return result == 0 if result is not None else True
        else:
            print("(No demo available - module loaded successfully)")
            return True

    except Exception as e:
        print(f"Error running {tool_key}: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tools():
    """Run demos for all available tools."""
    print_header("TOOLS SUITE - Running All Demos")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    for tool_key in sorted(TOOLS.keys()):
        info = TOOLS[tool_key]
        module_path = get_tools_dir() / info['module'].replace('.', '/')
        module_file = str(module_path) + '.py'

        if os.path.exists(module_file):
            print()
            print(f"{'='*70}")
            success = run_tool(tool_key)
            results[tool_key] = 'PASSED' if success else 'FAILED'
        else:
            results[tool_key] = 'NOT IMPLEMENTED'

    # Summary
    print_header("Summary")

    passed = sum(1 for r in results.values() if r == 'PASSED')
    failed = sum(1 for r in results.values() if r == 'FAILED')
    not_impl = sum(1 for r in results.values() if r == 'NOT IMPLEMENTED')

    print(f"Total Tools: {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Not Implemented: {not_impl}")
    print()

    for tool_key, result in sorted(results.items()):
        status_icon = {'PASSED': '✓', 'FAILED': '✗', 'NOT IMPLEMENTED': '○'}[result]
        print(f"  {status_icon} {tool_key}: {result}")

    print()
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return failed == 0


def quick_test():
    """Run quick tests on all available tools."""
    print_header("TOOLS SUITE - Quick Test")

    results = {}
    tools_dir = get_tools_dir()

    for tool_key, info in sorted(TOOLS.items()):
        module_path = tools_dir / info['module'].replace('.', '/')
        module_file = str(module_path) + '.py'

        if not os.path.exists(module_file):
            results[tool_key] = ('SKIP', 'Not implemented')
            continue

        try:
            # Just import the module to test syntax
            spec = importlib.util.spec_from_file_location(info['module'], module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            results[tool_key] = ('OK', 'Imported successfully')
        except Exception as e:
            results[tool_key] = ('ERROR', str(e)[:50])

    # Print results
    print(f"{'Tool':<15} {'Status':<8} {'Details'}")
    print("-" * 70)

    for tool_key, (status, details) in sorted(results.items()):
        status_icon = {'OK': '✓', 'ERROR': '✗', 'SKIP': '○'}[status]
        print(f"{tool_key:<15} {status_icon} {status:<6} {details}")

    print()

    ok_count = sum(1 for s, _ in results.values() if s == 'OK')
    print(f"Result: {ok_count}/{len(results)} tools loaded successfully")

    return all(s != 'ERROR' for s, _ in results.values())


def interactive_menu():
    """Show interactive menu."""
    while True:
        print_header("TOOLS SUITE - Interactive Menu")

        print("Options:")
        print("  1. List all tools")
        print("  2. Run a specific tool")
        print("  3. Run all tool demos")
        print("  4. Quick test all tools")
        print("  5. Exit")
        print()

        choice = input("Enter choice (1-5): ").strip()

        if choice == '1':
            list_tools()
        elif choice == '2':
            list_tools()
            tool = input("Enter tool name: ").strip().lower()
            if tool:
                run_tool(tool)
        elif choice == '3':
            run_all_tools()
        elif choice == '4':
            quick_test()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

        input("\nPress Enter to continue...")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Tools Suite Master Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 run_tools.py --list              List all available tools
  python3 run_tools.py --tool statistics   Run statistics toolkit demo
  python3 run_tools.py --tool finance      Run finance toolkit demo
  python3 run_tools.py --all               Run all tool demos
  python3 run_tools.py --test              Quick test all tools
  python3 run_tools.py                     Interactive menu
        '''
    )

    parser.add_argument('--list', '-l', action='store_true',
                        help='List all available tools')
    parser.add_argument('--tool', '-t', metavar='NAME',
                        help='Run specific tool demo')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Run all tool demos')
    parser.add_argument('--test', action='store_true',
                        help='Quick test all tools')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive menu mode')

    args = parser.parse_args()

    # Change to tools directory
    os.chdir(get_tools_dir().parent)

    if args.list:
        list_tools()
    elif args.tool:
        success = run_tool(args.tool.lower())
        return 0 if success else 1
    elif args.all:
        success = run_all_tools()
        return 0 if success else 1
    elif args.test:
        success = quick_test()
        return 0 if success else 1
    elif args.interactive:
        interactive_menu()
    else:
        # Default to interactive if no args
        if len(sys.argv) == 1:
            interactive_menu()
        else:
            parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
