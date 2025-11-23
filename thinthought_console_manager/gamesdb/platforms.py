"""Helpers for loading emulator platform mappings."""

from __future__ import annotations

from importlib.resources import files
from functools import lru_cache

import yaml


@lru_cache(maxsize=1)
def load_extension_mapping() -> dict[str, list[str]]:
    """Return a mapping from file extension to possible platform names."""
    config_path = files("thinthought_console_manager.gamesdb.data.config").joinpath("emu_extensions.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    mapping: dict[str, list[str]] = {}
    for platform, extensions in data.get("emu_extensions", {}).items():
        for ext in extensions:
            ext_key = ext.lower()
            mapping.setdefault(ext_key, [])
            if platform not in mapping[ext_key]:
                mapping[ext_key].append(platform)
    return mapping


# Expose a cached mapping for convenience.
EXTENSION_PLATFORMS = load_extension_mapping()
