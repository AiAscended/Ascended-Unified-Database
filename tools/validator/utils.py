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


# ---------------------------------------------------------------------------
# Compatibility helpers used by validator.py
# ---------------------------------------------------------------------------

ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RESET = "\033[0m"


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def red(text: str) -> str:
    return f"{ANSI_RED}{text}{ANSI_RESET}" if _supports_color() else text


def green(text: str) -> str:
    return f"{ANSI_GREEN}{text}{ANSI_RESET}" if _supports_color() else text


def yellow(text: str) -> str:
    return f"{ANSI_YELLOW}{text}{ANSI_RESET}" if _supports_color() else text


def find_files(root: Path, extensions: list[str]) -> list[Path]:
    """Wrapper around collect_files that accepts a list of extensions."""
    return collect_files(root, tuple(extensions))


def get_repo_root() -> Path:
    """Return the repository root by walking up from this file's location."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def read_file(path: Path) -> str | None:
    """Read a text file and return its contents, or None on error."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def print_issues(issues: list[str], check_name: str) -> None:
    """Print a named set of validation issues."""
    if issues:
        print_section(f"{check_name} — {len(issues)} issue(s)")
        for issue in issues:
            print_fail(issue)
    else:
        print_section(check_name)
        print_pass("No issues found.")
