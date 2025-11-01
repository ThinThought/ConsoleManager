"""Utilities to reindex ROMs and associated artwork into per-game folders."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import re
import shutil

import yaml

from gamesdb.thumbnailer import make_thumbnail


@dataclass(frozen=True, slots=True)
class GameAsset:
    """Represents a ROM and its optional artwork."""

    platform: str
    rom_path: Path
    base_name: str
    image_path: Path | None = None


PREFIX_RE = re.compile(r"^(?P<num>\d{3})[\s_-]+(?P<name>.+)$")
FOLDER_NAME_RE = re.compile(r"^\d{3}_.+")


def _load_extension_mapping() -> dict[str, str]:
    config_path = files("gamesdb.data.config").joinpath("emu_extensions.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for platform, extensions in data.get("emu_extensions", {}).items():
        for ext in extensions:
            mapping[ext.lower()] = platform
    return mapping


EXTENSION_TO_PLATFORM = _load_extension_mapping()


def _normalize_stem(stem: str) -> str:
    """Normalize a file stem to compare loosely."""
    return "".join(ch.lower() for ch in stem if ch.isalnum())


def _extract_base_name(stem: str) -> str:
    """Strip numeric prefixes like 001_ from the start of a ROM stem."""
    match = PREFIX_RE.match(stem)
    candidate = match.group("name") if match else stem
    return candidate.strip().strip("_- ")


def _slugify(name: str) -> str:
    """Convert base names to filesystem-friendly folder slugs."""
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", name) if p]
    if not parts:
        return "Game"
    return "_".join(part.capitalize() for part in parts)


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


def _next_index_for_platform(platform_dir: Path) -> int:
    """Return the next numeric prefix for ROM files inside platform_dir."""
    max_index = 0
    if not platform_dir.exists():
        return 1

    for item in platform_dir.iterdir():
        if not item.is_file():
            continue
        match = PREFIX_RE.match(item.stem)
        if match:
            try:
                max_index = max(max_index, int(match.group("num")))
            except ValueError:
                continue
    return max_index + 1


def _determine_platform(rom_file: Path) -> str | None:
    """Return the platform name for a ROM file based on extension mapping."""
    return EXTENSION_TO_PLATFORM.get(rom_file.suffix.lower())


def _copy_manual_image(manual_dir: Path, rom_dest: Path, platform_dir: Path) -> None:
    images_dir = platform_dir / "Imgs"
    images_dir.mkdir(parents=True, exist_ok=True)

    image_source = None
    for candidate in manual_dir.iterdir():
        if candidate.suffix.lower() in {".png", ".jpg", ".jpeg"} and candidate.is_file():
            image_source = candidate
            break

    if not image_source:
        return

    destination_image = images_dir / f"{rom_dest.stem}.png"
    try:
        make_thumbnail(image_source, destination_image)
    except Exception as exc:
        print(f"⚠️ Unable to convert {image_source} to PNG: {exc}")
        shutil.copy2(image_source, destination_image)


def _process_manual_insertions(destination_root: Path, roms_root: Path) -> None:
    """Handle manually added game folders inside the destination root."""
    for manual_dir in sorted(destination_root.iterdir()):
        if not manual_dir.is_dir():
            continue
        if FOLDER_NAME_RE.match(manual_dir.name):
            continue

        rom_candidates = [p for p in manual_dir.iterdir() if p.is_file()]
        rom_file = next((p for p in rom_candidates if _determine_platform(p)), None)
        if not rom_file:
            continue

        platform_name = _determine_platform(rom_file)
        if not platform_name:
            continue

        platform_dir = roms_root / platform_name
        platform_dir.mkdir(parents=True, exist_ok=True)

        next_index = _next_index_for_platform(platform_dir)
        slug = _slugify(_extract_base_name(rom_file.stem))
        extension = rom_file.suffix.lower()
        target_rom = platform_dir / f"{next_index:03d}_{slug}{extension}"
        while target_rom.exists():
            next_index += 1
            target_rom = platform_dir / f"{next_index:03d}_{slug}{extension}"

        shutil.copy2(rom_file, target_rom)
        _copy_manual_image(manual_dir, target_rom, platform_dir)
        shutil.rmtree(manual_dir)


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
    _process_manual_insertions(destination_root, roms_root)

    assets = gather_games(roms_root, platforms=platforms)
    assets.sort(key=lambda a: (a.base_name.lower(), a.platform.lower(), a.rom_path.name.lower()))

    planned: list[tuple[str, GameAsset]] = [
        (f"{index:03d}_{_slugify(asset.base_name)}", asset)
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

        shutil.copy2(asset.rom_path, target_dir / asset.rom_path.name)

        if asset.image_path and asset.image_path.exists():
            copied_image = target_dir / asset.image_path.name
            shutil.copy2(asset.image_path, copied_image)
            try:
                make_thumbnail(copied_image, copied_image)
            except Exception as exc:  # pragma: no cover - logged upstream if needed
                # If thumbnail creation fails, leave the original image in place.
                # Consumers can inspect/replace manually.
                print(f"⚠️ Unable to thumbnail {copied_image}: {exc}")

        yield target_dir


def get_games(
    roms_root: Path,
    destination_root: Path,
    *,
    platforms: set[str] | None = None,
) -> list[Path]:
    """Copy ROMs (and optional PNG artwork) into per-game folders and return created directories."""
    return list(iter_reindexed_games(roms_root, destination_root, platforms=platforms))
