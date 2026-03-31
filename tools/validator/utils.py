"""
Utility helpers for the Ascended Validator CLI.
"""
from __future__ import annotations

import sys
from pathlib import Path


def print_section(title: str) -> None:
    """Print a formatted section header to stdout."""
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def print_pass(message: str) -> None:
    """Print a pass (success) line."""
    print(f"  ✅  {message}")


def print_fail(message: str) -> None:
    """Print a failure line."""
    print(f"  ❌  {message}", file=sys.stderr)


def collect_files(root: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Recursively collect files under root matching the given extensions.

    Skips .git, __pycache__, node_modules, .venv, and dist directories.
    """
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "dist", ".mypy_cache"}
    results: list[Path] = []
    for path in root.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_file() and path.suffix in extensions:
            results.append(path)
    return results


def relative(path: Path, root: Path) -> str:
    """Return path relative to root as a string."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
