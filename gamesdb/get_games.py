"""Utilities to reindex ROMs and associated artwork into per-game folders."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True, slots=True)
class GameAsset:
    """Represents a ROM and its optional artwork."""

    platform: str
    rom_path: Path
    image_path: Path | None = None


def _normalize_stem(stem: str) -> str:
    """Normalize a file stem to compare loosely."""
    return "".join(ch.lower() for ch in stem if ch.isalnum())


def _build_image_lookup(images_dir: Path) -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    if not images_dir.exists():
        return lookup

    for image_path in images_dir.glob("*.png"):
        lookup[image_path.stem.lower()] = image_path
    return lookup


def _match_image(rom_stem: str, lookup: dict[str, Path]) -> Path | None:
    """Find the best matching image for the ROM stem."""
    if not lookup:
        return None

    direct_key = rom_stem.lower()
    if direct_key in lookup:
        return lookup[direct_key]

    normalized = _normalize_stem(rom_stem)
    for stem, image_path in lookup.items():
        if _normalize_stem(stem) == normalized:
            return image_path

    return None


def gather_games(roms_root: Path, platforms: set[str] | None = None) -> list[GameAsset]:
    """Scan the ROM tree and collect ROM/artwork pairs."""
    assets: list[GameAsset] = []

    for platform_dir in sorted(p for p in roms_root.iterdir() if p.is_dir()):
        platform_name = platform_dir.name
        if platforms and platform_name not in platforms:
            continue

        images_lookup = _build_image_lookup(platform_dir / "Imgs")

        for item in sorted(platform_dir.iterdir()):
            if not item.is_file():
                continue

            suffix = item.suffix.lower()
            if suffix in {".png", ".jpg", ".jpeg"}:
                continue

            image_path = _match_image(item.stem, images_lookup)
            assets.append(GameAsset(platform=platform_name, rom_path=item, image_path=image_path))

    return assets


def iter_reindexed_games(
    roms_root: Path,
    destination_root: Path,
    *,
    platforms: set[str] | None = None,
) -> Iterator[Path]:
    """Yield the target directory for each reindexed game."""
    destination_root.mkdir(parents=True, exist_ok=True)

    for asset in gather_games(roms_root, platforms=platforms):
        target_dir = destination_root / asset.rom_path.stem
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(asset.rom_path, target_dir / asset.rom_path.name)

        if asset.image_path and asset.image_path.exists():
            shutil.copy2(asset.image_path, target_dir / asset.image_path.name)

        yield target_dir


def get_games(
    roms_root: Path,
    destination_root: Path,
    *,
    platforms: set[str] | None = None,
) -> list[Path]:
    """Copy ROMs (and optional PNG artwork) into per-game folders and return created directories."""
    return list(iter_reindexed_games(roms_root, destination_root, platforms=platforms))
