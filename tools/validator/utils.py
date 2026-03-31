from __future__ import annotations

import sys
from pathlib import Path


ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RESET = "\033[0m"


def supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def red(text: str) -> str:
    return f"{ANSI_RED}{text}{ANSI_RESET}" if supports_color() else text


def green(text: str) -> str:
    return f"{ANSI_GREEN}{text}{ANSI_RESET}" if supports_color() else text


def yellow(text: str) -> str:
    return f"{ANSI_YELLOW}{text}{ANSI_RESET}" if supports_color() else text


def find_files(root: Path, extensions: list[str], exclude_dirs: set[str] | None = None) -> list[Path]:
    exclude_dirs = exclude_dirs or {".git", "__pycache__", "node_modules", ".venv", "venv"}
    result: list[Path] = []
    for ext in extensions:
        for p in root.rglob(f"*{ext}"):
            if not any(part in exclude_dirs for part in p.parts):
                result.append(p)
    return sorted(result)


def read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def print_issues(issues: list[str], category: str) -> None:
    if issues:
        print(yellow(f"\n[{category}] {len(issues)} issue(s) found:"))
        for issue in issues:
            print(f"  {red('✗')} {issue}")
    else:
        print(green(f"[{category}] No issues found."))


def get_repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()
