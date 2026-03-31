from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Any

import yaml


PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*pass\s*$"),
    re.compile(r"\bNotImplemented\b"),
    re.compile(r"<YOUR[_\s].*?>", re.IGNORECASE),
]

SECRET_PATTERNS = [
    re.compile(r'(?i)(password|secret|token|api_key|private_key)\s*[:=]\s*["\'](?!.*\$\{)[^"\']{8,}'),
    re.compile(r'(?i)sk-[A-Za-z0-9]{32,}'),
    re.compile(r'(?i)AKIA[0-9A-Z]{16}'),
    re.compile(r'(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
]

SKIP_SECRET_DIRS = {".git", "__pycache__", "node_modules", ".env.example"}
SKIP_SECRET_FILES = {".env.example", ".gitignore"}
# The validator's own source files define detection patterns; exclude them from self-checks
SKIP_PLACEHOLDER_FILES = {"rules.py", "validator.py", "config_schema.py", "utils.py"}


def check_placeholders(path: Path, content: str) -> list[str]:
    if path.name in SKIP_PLACEHOLDER_FILES:
        return []
    issues = []
    for pattern in PLACEHOLDER_PATTERNS:
        for m in pattern.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            issues.append(f"{path}:{line_no}: placeholder detected: {m.group()!r}")
    return issues


def check_secrets(path: Path, content: str) -> list[str]:
    if path.name in SKIP_SECRET_FILES:
        return []
    if any(part in SKIP_SECRET_DIRS for part in path.parts):
        return []

    issues = []
    for pattern in SECRET_PATTERNS:
        for m in pattern.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            issues.append(f"{path}:{line_no}: potential hardcoded secret: {m.group()[:40]!r}...")
    return issues


def _is_helm_template(path: Path) -> bool:
    """Helm templates contain Go template syntax and are not pure YAML."""
    parts = path.parts
    return "templates" in parts and any(p.endswith("-chart") for p in parts)


def validate_yaml_file(path: Path) -> list[str]:
    if _is_helm_template(path):
        return []
    issues = []
    try:
        with path.open() as fh:
            list(yaml.safe_load_all(fh))
    except yaml.YAMLError as exc:
        issues.append(f"{path}: YAML parse error: {exc}")
    return issues


def validate_dockerfile(path: Path, content: str) -> list[str]:
    issues = []
    lines = content.splitlines()
    has_healthcheck = any("HEALTHCHECK" in ln for ln in lines)
    has_user = any(ln.strip().startswith("USER") for ln in lines)
    if not has_healthcheck:
        issues.append(f"{path}: Dockerfile missing HEALTHCHECK instruction.")
    if not has_user:
        issues.append(f"{path}: Dockerfile missing USER instruction (should not run as root).")
    return issues


def validate_k8s_manifest(path: Path, content: str) -> list[str]:
    issues = []
    try:
        docs = list(yaml.safe_load_all(content))
    except yaml.YAMLError:
        return issues

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        if kind in ("Deployment", "StatefulSet", "DaemonSet"):
            spec = doc.get("spec", {}) or {}
            template = spec.get("template", {}) or {}
            pod_spec = template.get("spec", {}) or {}
            containers = pod_spec.get("containers", []) or []
            for c in containers:
                if not c.get("resources"):
                    issues.append(
                        f"{path}: Container '{c.get('name')}' in {kind} '{doc.get('metadata', {}).get('name')}' "
                        f"is missing resource limits."
                    )
                if not c.get("livenessProbe"):
                    issues.append(
                        f"{path}: Container '{c.get('name')}' in {kind} is missing livenessProbe."
                    )
    return issues
