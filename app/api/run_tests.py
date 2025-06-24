#!/usr/bin/env python3
"""
Custom test runner for the Strava Running Analytics application.

This script provides multiple ways to run tests with different configurations:
- Run all tests
- Run specific test categories using markers
- Run tests with or without coverage
- Skip slow tests for faster development cycles
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors gracefully."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def check_pytest_plugins():
    """Check if required pytest plugins are installed."""
    try:
        import importlib.util

        coverage_available = importlib.util.find_spec("pytest_cov") is not None
    except ImportError:
        coverage_available = False

    try:
        import importlib.util

        flask_available = importlib.util.find_spec("pytest_flask") is not None
    except ImportError:
        flask_available = False

    try:
        import importlib.util

        mock_available = importlib.util.find_spec("pytest_mock") is not None
    except ImportError:
        mock_available = False

    return {
        "coverage": coverage_available,
        "flask": flask_available,
        "mock": mock_available,
    }


def install_missing_plugins():
    """Install missing pytest plugins."""
    plugins = check_pytest_plugins()
    missing_plugins = []

    if not plugins["coverage"]:
        missing_plugins.append("pytest-cov")
    if not plugins["flask"]:
        missing_plugins.append("pytest-flask")
    if not plugins["mock"]:
        missing_plugins.append("pytest-mock")

    if missing_plugins:
        print(f"\nMissing pytest plugins: {', '.join(missing_plugins)}")
        print("Installing missing plugins...")

        cmd = [sys.executable, "-m", "pip", "install"] + missing_plugins
        success = run_command(cmd, "Installing missing pytest plugins")

        if success:
            print("✅ Successfully installed missing plugins")
            return True
        else:
            print("❌ Failed to install missing plugins")
            print("You can install them manually with:")
            print(f"pip install {' '.join(missing_plugins)}")
            return False

    return True


def run_tests(test_type="all", coverage=True, install_deps=False):
    """Run tests with specified configuration."""

    # Check and optionally install missing plugins
    if install_deps:
        if not install_missing_plugins():
            print("Continuing without some plugins...")

    plugins = check_pytest_plugins()

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add coverage if available and requested
    if coverage and plugins["coverage"]:
        cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
    elif coverage and not plugins["coverage"]:
        print("⚠️  Coverage requested but pytest-cov not available")
        print("Run with --install-deps to install missing plugins")

    # Add test selection based on type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "database":
        cmd.extend(["-m", "database"])
    elif test_type == "strava":
        cmd.extend(["-m", "strava"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "simple":
        cmd.append("tests/test_simple.py")
    elif test_type != "all":
        print(f"Unknown test type: {test_type}")
        return False

    # Add verbose output
    cmd.append("-v")

    # Run the tests
    description = f"Running {test_type} tests" + (
        " with coverage" if coverage and plugins["coverage"] else ""
    )
    return run_command(cmd, description)


def main():
    """Main entry point for the test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests for Strava Running Analytics"
    )
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=[
            "all",
            "unit",
            "integration",
            "api",
            "database",
            "strava",
            "fast",
            "slow",
            "simple",
        ],
        help="Type of tests to run",
    )
    parser.add_argument("--no-cov", action="store_true", help="Skip coverage reporting")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install missing pytest plugins automatically",
    )
    parser.add_argument(
        "--check-setup", action="store_true", help="Check test setup and dependencies"
    )

    args = parser.parse_args()

    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    if args.check_setup:
        print("Checking test setup...")
        plugins = check_pytest_plugins()

        print("\nPytest plugins status:")
        print(f"  pytest-cov: {'✅' if plugins['coverage'] else '❌'}")
        print(f"  pytest-flask: {'✅' if plugins['flask'] else '❌'}")
        print(f"  pytest-mock: {'✅' if plugins['mock'] else '❌'}")

        # Check if test files exist
        test_files = list(Path("tests").glob("test_*.py"))
        print(f"\nFound {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  {test_file}")

        return

    # Run the tests
    success = run_tests(
        test_type=args.test_type,
        coverage=not args.no_cov,
        install_deps=args.install_deps,
    )

    if success:
        print("\n✅ Tests completed successfully!")
    else:
        print("\n❌ Tests failed or encountered errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
