from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_CONFIG_KEYS = {
    "root": ["environment", "databases", "gateway", "security"],
    "databases": ["postgres", "redis", "object_storage"],
    "gateway": ["host", "port", "workers", "log_level"],
    "security": ["jwt_algorithm", "access_token_expire_minutes"],
    "postgres": ["enabled", "host", "port", "database"],
    "redis": ["enabled", "host", "port"],
    "object_storage": ["enabled", "provider", "bucket"],
}


def validate_config_file(path: Path) -> list[str]:
    issues = []
    try:
        with path.open() as fh:
            doc: dict[str, Any] = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        return [f"{path}: YAML parse error: {exc}"]

    for key in REQUIRED_CONFIG_KEYS["root"]:
        if key not in doc:
            issues.append(f"{path}: Missing required top-level key: '{key}'")

    for section in ("gateway", "security"):
        section_doc = doc.get(section, {}) or {}
        for key in REQUIRED_CONFIG_KEYS.get(section, []):
            if key not in section_doc:
                issues.append(f"{path}: Missing key '{key}' in section '{section}'")

    databases = doc.get("databases", {}) or {}
    for db_name in REQUIRED_CONFIG_KEYS["databases"]:
        db_cfg = databases.get(db_name, {}) or {}
        if not db_cfg:
            issues.append(f"{path}: Missing database section: '{db_name}'")
            continue
        for key in REQUIRED_CONFIG_KEYS.get(db_name, []):
            if key not in db_cfg:
                issues.append(f"{path}: Missing key '{key}' in databases.{db_name}")

    valid_environments = {"dev", "prod", "production", "enterprise"}
    env = doc.get("environment", "")
    if env not in valid_environments:
        issues.append(f"{path}: Unknown environment value: '{env}'. Expected one of {valid_environments}.")

    return issues


def validate_all_configs(root: Path) -> list[str]:
    issues = []
    config_dir = root / "configs"
    if not config_dir.is_dir():
        return [f"configs/ directory not found at {config_dir}"]
    for yaml_file in sorted(config_dir.glob("*.yaml")):
        issues.extend(validate_config_file(yaml_file))
    return issues
