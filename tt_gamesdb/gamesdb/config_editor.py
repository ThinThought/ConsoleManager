"""Utilities to mutate the GamesDB YAML configuration file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import yaml


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "data" / "config" / "config.yaml"


@dataclass(slots=True)
class ConfigUpdateResult:
    key_path: str
    old_value: Any
    new_value: Any
    config_path: Path
    config: dict[str, Any]


def resolve_config_path(config_path: Path | str | None = None) -> Path:
    """Resolve the configuration file path honoring environment overrides."""
    if config_path:
        return Path(config_path).expanduser()
    env_override = os.environ.get("GAMESDB_CONFIG_PATH")
    if env_override:
        return Path(env_override).expanduser()
    return DEFAULT_CONFIG_PATH


def _read_config_text(config_path: Path) -> str:
    return config_path.read_text(encoding="utf-8")


def _write_config_text(config_path: Path, text: str) -> None:
    config_path.write_text(text, encoding="utf-8")


def _extract_leading_prelude(text: str) -> tuple[str, str]:
    """Split leading comments/blank lines from the rest of the YAML."""
    lines = text.splitlines(keepends=True)
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("#") or stripped == "":
            idx += 1
            continue
        break
    prelude = "".join(lines[:idx])
    remainder = "".join(lines[idx:])
    return prelude, remainder


def _ensure_nested_dict(container: dict[str, Any], path_parts: Iterable[str]) -> dict[str, Any]:
    node: Any = container
    traversed: list[str] = []
    for part in path_parts:
        traversed.append(part)
        if not isinstance(node, dict) or part not in node:
            joined = ".".join(traversed)
            raise KeyError(f"Missing config path segment: {joined}")
        node = node[part]
    if not isinstance(node, dict):
        joined = ".".join(traversed)
        raise KeyError(f"Config path {joined} does not lead to a mapping")
    return node


def _yaml_dump(data: Any) -> str:
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def _yaml_value(value_expr: str) -> Any:
    try:
        return yaml.safe_load(value_expr)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML literal: {value_expr}") from exc


def load_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load the GamesDB config YAML into a dictionary."""
    path = resolve_config_path(config_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def set_config_value(
    key_path: str,
    value_expr: str,
    *,
    config_path: Path | str | None = None,
) -> ConfigUpdateResult:
    """Set a configuration value located at the provided dotted path."""
    if not key_path:
        raise ValueError("key_path must not be empty")

    path = resolve_config_path(config_path)
    original_text = _read_config_text(path)
    prelude, _ = _extract_leading_prelude(original_text)

    config_data = load_config(path)
    parts = key_path.split(".")
    if len(parts) == 1:
        container = config_data
        leaf_key = parts[0]
    else:
        container = _ensure_nested_dict(config_data, parts[:-1])
        leaf_key = parts[-1]

    if leaf_key not in container:
        raise KeyError(f"Unknown config key: {key_path}")

    old_value = container[leaf_key]
    new_value = _yaml_value(value_expr)
    container[leaf_key] = new_value

    updated_yaml = _yaml_dump(config_data)
    _write_config_text(path, f"{prelude}{updated_yaml}")

    return ConfigUpdateResult(
        key_path=key_path,
        old_value=old_value,
        new_value=new_value,
        config_path=path,
        config=config_data,
    )


__all__ = [
    "ConfigUpdateResult",
    "DEFAULT_CONFIG_PATH",
    "resolve_config_path",
    "load_config",
    "set_config_value",
]
