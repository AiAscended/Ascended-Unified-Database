#!/usr/bin/env python3
"""Ascended Unified Database — validation CLI tool."""
from __future__ import annotations

import sys
from pathlib import Path

from .config_schema import validate_all_configs
from .rules import (
    check_placeholders,
    check_secrets,
    validate_dockerfile,
    validate_k8s_manifest,
    validate_yaml_file,
)
from .utils import (
    find_files,
    get_repo_root,
    green,
    print_issues,
    read_file,
    red,
)


def run_placeholder_checks(root: Path) -> list[str]:
    issues: list[str] = []
    for path in find_files(root, [".py", ".sh", ".yaml", ".yml"]):
        content = read_file(path)
        if content is not None:
            issues.extend(check_placeholders(path, content))
    return issues


def run_secret_checks(root: Path) -> list[str]:
    issues: list[str] = []
    for path in find_files(root, [".py", ".sh", ".yaml", ".yml", ".env", ".json"]):
        content = read_file(path)
        if content is not None:
            issues.extend(check_secrets(path, content))
    return issues


def run_yaml_checks(root: Path) -> list[str]:
    issues: list[str] = []
    for path in find_files(root, [".yaml", ".yml"]):
        issues.extend(validate_yaml_file(path))
    return issues


def run_dockerfile_checks(root: Path) -> list[str]:
    issues: list[str] = []
    for path in find_files(root, ["Dockerfile", ""]):
        if path.name == "Dockerfile" or path.name.startswith("Dockerfile."):
            content = read_file(path)
            if content is not None:
                issues.extend(validate_dockerfile(path, content))
    return issues


def run_k8s_checks(root: Path) -> list[str]:
    issues: list[str] = []
    k8s_dir = root / "k8s"
    if not k8s_dir.is_dir():
        return []
    for path in find_files(k8s_dir, [".yaml", ".yml"]):
        content = read_file(path)
        if content is not None:
            issues.extend(validate_k8s_manifest(path, content))
    return issues


def run_config_checks(root: Path) -> list[str]:
    return validate_all_configs(root)


def main(argv: list[str] | None = None) -> int:
    root = get_repo_root()
    print(f"Validating repository at: {root}\n")

    all_issues: list[str] = []
    checks = [
        ("Config Schema", run_config_checks),
        ("YAML Syntax", run_yaml_checks),
        ("Placeholders", run_placeholder_checks),
        ("Secrets", run_secret_checks),
        ("Dockerfiles", run_dockerfile_checks),
        ("Kubernetes Manifests", run_k8s_checks),
    ]

    for name, check_fn in checks:
        issues = check_fn(root)
        print_issues(issues, name)
        all_issues.extend(issues)

    print()
    if all_issues:
        print(red(f"Validation FAILED — {len(all_issues)} total issue(s) found."))
        return 1
    print(green("Validation PASSED — all checks clean."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
