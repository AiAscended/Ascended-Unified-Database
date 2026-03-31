"""
Configuration schema validator for Ascended Unified Database environment configs.
Ensures all environment YAML files contain required structure before deployment.
"""
from __future__ import annotations

from typing import Any

REQUIRED_TOP_LEVEL_KEYS = [
    "environment",
    "databases",
    "gateway",
    "security",
]

REQUIRED_DATABASE_KEYS = [
    "postgres",
    "redis",
    "object_storage",
    "qdrant",
    "graph",
    "analytics",
    "streaming",
]

VALID_ENVIRONMENTS = {"dev", "production", "enterprise"}


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate an environment config dict against the required schema.

    Returns a list of error strings. Empty list means valid.
    """
    errors: list[str] = []

    if not isinstance(config, dict):
        return ["Config must be a YAML mapping (dict)."]

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in config:
            errors.append(f"Missing required top-level key: '{key}'")

    env_name = config.get("environment")
    if env_name and env_name not in VALID_ENVIRONMENTS:
        errors.append(
            f"Invalid environment '{env_name}'. Must be one of: {sorted(VALID_ENVIRONMENTS)}"
        )

    databases = config.get("databases")
    if databases is None:
        errors.append("Missing 'databases' section.")
    elif not isinstance(databases, dict):
        errors.append("'databases' must be a YAML mapping.")
    else:
        for key in REQUIRED_DATABASE_KEYS:
            if key not in databases:
                errors.append(f"Missing database config block: 'databases.{key}'")

    gateway = config.get("gateway")
    if gateway is not None:
        if not isinstance(gateway, dict):
            errors.append("'gateway' must be a YAML mapping.")
        else:
            for field in ("host", "port", "workers"):
                if field not in gateway:
                    errors.append(f"Missing gateway field: 'gateway.{field}'")

    return errors
