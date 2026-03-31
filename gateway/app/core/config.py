import os
import re
from pathlib import Path
from typing import Any

import yaml


_config_cache: dict[str, Any] | None = None


def _interpolate(value: Any) -> Any:
    """Recursively interpolate ${VAR:default} syntax in config values."""
    if isinstance(value, str):
        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default if default is not None else "")

        return re.sub(r"\$\{([^}:]+)(?::([^}]*))?\}", replacer, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(item) for item in value]
    return value


def load_config() -> dict[str, Any]:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    environment = os.environ.get("ENVIRONMENT", "dev").lower()
    config_path = Path(__file__).parents[3] / "configs" / f"{environment}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. "
            f"Valid environments: dev, prod, enterprise."
        )

    with config_path.open("r") as fh:
        raw = yaml.safe_load(fh)

    _config_cache = _interpolate(raw)
    return _config_cache


def get_db_config(name: str) -> dict[str, Any]:
    cfg = load_config()
    return cfg.get("databases", {}).get(name, {})


def get_gateway_config() -> dict[str, Any]:
    return load_config().get("gateway", {})


def get_security_config() -> dict[str, Any]:
    return load_config().get("security", {})
