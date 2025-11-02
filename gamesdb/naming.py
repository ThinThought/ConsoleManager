"""Utilities for normalizing game titles."""

from __future__ import annotations

import re


SEPARATOR_PATTERN = re.compile(r"[^A-Za-z0-9]+")


def slugify(name: str) -> str:
    """Return a filesystem-friendly slug with StudlyCaps tokens joined by underscores."""
    parts = [part for part in SEPARATOR_PATTERN.split(name) if part]
    if not parts:
        return "Game"
    return "_".join(part.capitalize() for part in parts)


def pretty_game_name(stem: str) -> str:
    """Return a human-friendly game title derived from a file stem."""
    parts = [part for part in SEPARATOR_PATTERN.split(stem) if part]
    if not parts:
        return "Game"
    return " ".join(part.capitalize() for part in parts)
