#!/usr/bin/env python3
"""
Linting and formatting script for Pantainos

Usage:
    python scripts/lint.py        # Check only (like pre-commit)
    python scripts/lint.py --fix  # Auto-fix issues
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, exit_on_failure: bool = True) -> bool:
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        if exit_on_failure:
            sys.exit(1)
        return False


def main() -> None:
    fix_mode = "--fix" in sys.argv

    print("🚀 Running Pantainos linting and formatting...")
    print(f"Mode: {'Fix' if fix_mode else 'Check only'}")
    print()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    all_passed = True

    # Run tests first
    all_passed &= run_command(
        ["uv", "run", "python", "-m", "pytest", "tests/unit", "-q", "--tb=short"],
        "Running tests",
        exit_on_failure=not fix_mode,
    )

    # Linting (with or without fix)
    if fix_mode:
        all_passed &= run_command(
            ["uv", "run", "ruff", "check", "src/", "tests/", "examples/", "--fix"], "Running ruff linter (with fixes)"
        )
    else:
        all_passed &= run_command(
            ["uv", "run", "ruff", "check", "src/", "tests/", "examples/", "--no-fix"],
            "Running ruff linter (check only)",
            exit_on_failure=False,
        )

    # Formatting
    if fix_mode:
        all_passed &= run_command(
            ["uv", "run", "ruff", "format", "src/", "tests/", "examples/"], "Running ruff formatter"
        )
        all_passed &= run_command(["uv", "run", "isort", "src/", "tests/", "examples/"], "Running isort")
        all_passed &= run_command(["uv", "run", "black", "src/", "tests/", "examples/"], "Running black formatter")
    else:
        all_passed &= run_command(
            ["uv", "run", "ruff", "format", "--check", "src/", "tests/", "examples/"],
            "Checking ruff formatting",
            exit_on_failure=False,
        )
        all_passed &= run_command(
            ["uv", "run", "isort", "--check-only", "--diff", "src/", "tests/", "examples/"],
            "Checking isort",
            exit_on_failure=False,
        )
        all_passed &= run_command(
            ["uv", "run", "black", "--check", "--diff", "src/", "tests/", "examples/"],
            "Checking black formatting",
            exit_on_failure=False,
        )

    print()
    if all_passed:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("💥 Some checks failed!")
        if not fix_mode:
            print("💡 Try running with --fix to auto-fix issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
