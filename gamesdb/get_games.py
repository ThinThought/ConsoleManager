"""Utilities to reindex ROMs and associated artwork into per-game folders."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
import re
import shutil

from gamesdb.thumbnailer import make_thumbnail
from gamesdb.naming import slugify


@dataclass(frozen=True, slots=True)
class GameAsset:
    """Represents a ROM and its optional artwork."""

    platform: str
    rom_path: Path
    base_name: str
    image_path: Path | None = None


PREFIX_RE = re.compile(r"^(?P<num>\d{3})[\s_-]+(?P<name>.+)$")
FOLDER_NAME_RE = re.compile(r"^\d{3}_.+")


def _normalize_stem(stem: str) -> str:
    """Normalize a file stem to compare loosely."""
    return "".join(ch.lower() for ch in stem if ch.isalnum())


def _extract_base_name(stem: str) -> str:
    """Strip numeric prefixes like 001_ from the start of a ROM stem."""
    match = PREFIX_RE.match(stem)
    candidate = match.group("name") if match else stem
    return candidate.strip().strip("_- ")


def _build_image_lookup(images_dir: Path) -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    if not images_dir.exists():
        return lookup

    for image_path in images_dir.glob("*.png"):
        lookup[image_path.stem.lower()] = image_path
    return lookup


def _match_image(rom_stem: str, base_name: str, lookup: dict[str, Path]) -> Path | None:
    """Find the best matching image for the ROM stem."""
    if not lookup:
        return None

    direct_key = rom_stem.lower()
    if direct_key in lookup:
        return lookup[direct_key]

    base_key = base_name.lower()
    if base_key in lookup:
        return lookup[base_key]

    normalized = _normalize_stem(rom_stem)
    for stem, image_path in lookup.items():
        if _normalize_stem(stem) == normalized:
            return image_path

    base_normalized = _normalize_stem(base_name)
    for stem, image_path in lookup.items():
        if _normalize_stem(stem) == base_normalized:
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

            base_name = _extract_base_name(item.stem)
            image_path = _match_image(item.stem, base_name, images_lookup)
            assets.append(
                GameAsset(
                    platform=platform_name,
                    rom_path=item,
                    base_name=base_name,
                    image_path=image_path,
                )
            )

    return assets


def iter_reindexed_games(
    roms_root: Path,
    destination_root: Path,
    *,
    platforms: set[str] | None = None,
) -> Iterator[Path]:
    """Yield the target directory for each reindexed game."""
    destination_root.mkdir(parents=True, exist_ok=True)

    assets = gather_games(roms_root, platforms=platforms)
    assets.sort(key=lambda a: (a.base_name.lower(), a.platform.lower(), a.rom_path.name.lower()))

    planned: list[tuple[str, GameAsset]] = [
        (f"{index:03d}_{slugify(asset.base_name)}", asset)
        for index, asset in enumerate(assets, start=1)
    ]
    planned_names = {folder for folder, _ in planned}

    if platforms is None:
        for child in destination_root.iterdir():
            if child.is_dir() and FOLDER_NAME_RE.match(child.name) and child.name not in planned_names:
                shutil.rmtree(child)

    for folder_name, asset in planned:
        target_dir = destination_root / folder_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        rom_extension = asset.rom_path.suffix
        destination_rom = target_dir / f"{folder_name}{rom_extension}"
        shutil.copy2(asset.rom_path, destination_rom)

        if asset.image_path and asset.image_path.exists():
            destination_image = target_dir / f"{folder_name}.png"
            try:
                make_thumbnail(asset.image_path, destination_image)
            except Exception as exc:  # pragma: no cover - logged upstream if needed
                print(f"⚠️ Unable to thumbnail {asset.image_path}: {exc}")
                shutil.copy2(asset.image_path, destination_image)

        yield target_dir


def get_games(
    roms_root: Path,
    destination_root: Path,
    *,
    platforms: set[str] | None = None,
) -> list[Path]:
    """Copy ROMs (and optional PNG artwork) into per-game folders and return created directories."""
    return list(iter_reindexed_games(roms_root, destination_root, platforms=platforms))
