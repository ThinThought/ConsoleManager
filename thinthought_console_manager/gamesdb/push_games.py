"""Interactive helper to push staged games into the backup tree."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re
import shutil

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import thinthought_console_manager.gamesdb as gamesdb
from thinthought_console_manager.gamesdb.naming import slugify
from thinthought_console_manager.gamesdb.platforms import EXTENSION_PLATFORMS
from thinthought_console_manager.gamesdb.thumbnailer import make_thumbnail

PromptFn = Callable[[str], str]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ROM_EXTENSIONS = {ext.lower() for ext in EXTENSION_PLATFORMS.keys()}
INDEXED_DIR_PATTERN = re.compile(r"^\d{3}_.+")
INDEXED_NAME_PATTERN = re.compile(r"^\d{3}_")
INDEX_PREFIX_RE = re.compile(r"^(?P<index>\d{3})[\s_-]+(?P<name>.+)$")


def _normalize_token(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _strip_index_prefix(name: str) -> str:
    match = INDEX_PREFIX_RE.match(name)
    return match.group("name") if match else name


def _extract_index_components(value: str) -> tuple[int | None, str]:
    match = INDEX_PREFIX_RE.match(value)
    if not match:
        return None, value
    try:
        return int(match.group("index")), match.group("name")
    except ValueError:  # pragma: no cover - defensive, regex guards digits
        return None, match.group("name")


def _list_staged_directories(staging_dir: Path) -> list[Path]:
    if not staging_dir.exists():
        return []
    dirs = []
    for child in sorted(staging_dir.iterdir()):
        if not child.is_dir():
            continue

        if INDEXED_DIR_PATTERN.match(child.name):
            has_cover = False
            has_rom = False
            for inner in child.iterdir():
                if not inner.is_file():
                    continue
                suffix = inner.suffix.lower()
                if suffix in IMAGE_EXTENSIONS:
                    has_cover = True
                elif suffix in ROM_EXTENSIONS:
                    has_rom = True
                if has_cover and has_rom:
                    break
            if has_cover or has_rom:
                dirs.append(child)
        else:
            dirs.append(child)
    return dirs


def _next_index_for_platform(platform_dir: Path) -> int:
    max_index = 0
    if platform_dir.exists():
        for item in platform_dir.iterdir():
            if not item.is_file():
                continue
            match = re.match(r"^(\d{3})_", item.stem)
            if match:
                try:
                    value = int(match.group(1))
                except ValueError:
                    continue
                max_index = max(max_index, value)
    return max_index + 1


def _choose_platform(ext: str, console: Console, prompt: PromptFn, interactive: bool) -> str | None:
    options = EXTENSION_PLATFORMS.get(ext.lower(), [])
    if not options:
        return None
    if len(options) == 1 or not interactive:
        return options[0]

    table = Table(title=f"Plataformas para {ext}", header_style="bold cyan")
    table.add_column("#")
    table.add_column("Plataforma")
    for index, platform in enumerate(options, start=1):
        table.add_row(str(index), platform)
    console.print(table)

    while True:
        answer = prompt(f"Selecciona plataforma [1-{len(options)}] (q para omitir): ").strip()
        if not answer or answer.lower() == "q":
            return None
        if answer.isdigit():
            pos = int(answer)
            if 1 <= pos <= len(options):
                return options[pos - 1]
        console.print("[red]Entrada inválida[/red]")


def _choose_rom(path: Path, console: Console, prompt: PromptFn, interactive: bool) -> Path | None:
    rom_candidates = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in EXTENSION_PLATFORMS]
    if not rom_candidates:
        return None
    if len(rom_candidates) == 1 or not interactive:
        return rom_candidates[0]

    table = Table(title=f"ROMs detectados en {path.name}", header_style="bold cyan")
    table.add_column("#")
    table.add_column("Archivo")
    for index, rom_path in enumerate(rom_candidates, start=1):
        table.add_row(str(index), rom_path.name)
    console.print(table)

    while True:
        answer = prompt(f"Selecciona ROM [1-{len(rom_candidates)}] (q para omitir): ").strip()
        if not answer or answer.lower() == "q":
            return None
        if answer.isdigit():
            pos = int(answer)
            if 1 <= pos <= len(rom_candidates):
                return rom_candidates[pos - 1]
        console.print("[red]Entrada inválida[/red]")


def _select_cover(directory: Path, console: Console, prompt: PromptFn, interactive: bool) -> Path | None:
    candidates = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    if not candidates:
        if not interactive:
            return None
        answer = prompt("Ruta de carátula (enter para omitir): ").strip()
        if not answer:
            return None
        cover_path = Path(answer).expanduser()
        return cover_path if cover_path.exists() else None

    if len(candidates) == 1 or not interactive:
        return candidates[0]

    table = Table(title="Carátulas detectadas", header_style="bold cyan")
    table.add_column("#")
    table.add_column("Archivo")
    for index, cover in enumerate(candidates, start=1):
        table.add_row(str(index), cover.name)
    console.print(table)

    while True:
        answer = prompt(f"Selecciona carátula [1-{len(candidates)}] (q para omitir): ").strip()
        if not answer or answer.lower() == "q":
            return None
        if answer.isdigit():
            pos = int(answer)
            if 1 <= pos <= len(candidates):
                return candidates[pos - 1]
        console.print("[red]Entrada inválida[/red]")


def _update_existing_game_cover(
    folder: Path,
    cover_path: Path,
    roms_root: Path,
    console: Console,
) -> tuple[Path, Path] | None:
    if not cover_path.exists():
        return None

    candidate_tokens = {
        folder.name,
        cover_path.stem,
        _strip_index_prefix(folder.name),
        _strip_index_prefix(cover_path.stem),
        slugify(folder.name),
        slugify(_strip_index_prefix(folder.name)),
        slugify(cover_path.stem),
        slugify(_strip_index_prefix(cover_path.stem)),
    }
    candidate_tokens = {token for token in candidate_tokens if token}
    lower_tokens = {token.lower() for token in candidate_tokens}
    normalized_tokens = {_normalize_token(token) for token in candidate_tokens}

    best_match: Path | None = None
    best_score = 0

    for platform_dir in sorted(p for p in roms_root.iterdir() if p.is_dir()):
        for rom_file in sorted(platform_dir.iterdir()):
            if not rom_file.is_file():
                continue
            suffix = rom_file.suffix.lower()
            if suffix not in ROM_EXTENSIONS:
                continue

            rom_stem = rom_file.stem
            stripped_rom = _strip_index_prefix(rom_stem)
            slug_rom = slugify(stripped_rom)
            normalized_rom = _normalize_token(rom_stem)
            normalized_stripped = _normalize_token(stripped_rom)

            score = 0
            if rom_stem in candidate_tokens or rom_stem.lower() in lower_tokens:
                score = max(score, 4)
            if slug_rom in candidate_tokens or slug_rom.lower() in lower_tokens:
                score = max(score, 3)
            if normalized_rom in normalized_tokens:
                score = max(score, 2)
            if normalized_stripped in normalized_tokens:
                score = max(score, 1)

            if score > best_score:
                best_score = score
                best_match = rom_file

    if best_match is None or best_score == 0:
        return None

    images_dir = best_match.parent / "Imgs"
    images_dir.mkdir(parents=True, exist_ok=True)
    dest_cover = images_dir / f"{best_match.stem}.png"

    try:
        make_thumbnail(cover_path, dest_cover)
    except Exception as exc:  # pragma: no cover
        console.print(f"[yellow]⚠️ No se generó miniatura para {cover_path}: {exc}[/yellow]")
        shutil.copy2(cover_path, dest_cover)

    return dest_cover, best_match


def push_games(
    staging_dir: Path | None = None,
    roms_root: Path | None = None,
    *,
    interactive: bool = True,
    console: Console | None = None,
    prompt: PromptFn | None = None,
) -> list[Path]:
    """Move staged games from games_to_include into the ROM backup tree."""

    console = console or Console()
    prompt = prompt or console.input

    staging_dir = staging_dir or Path(gamesdb.GAMESDB_CONFIG["paths"]["games_to_include_dir"])
    roms_root = roms_root or Path(gamesdb.GAMESDB_CONFIG["paths"]["roms_dir"])
    roms_root.mkdir(parents=True, exist_ok=True)

    staged_dirs = _list_staged_directories(staging_dir)
    if not staged_dirs:
        console.print("[yellow]No se encontraron juegos pendientes en games_to_include.[/yellow]")
        return []

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Insertando juegos en el backup[/green]",
        border_style="cyan",
    ))

    inserted: list[Path] = []
    cleaned_platforms: set[Path] = set()

    for folder in staged_dirs:
        rom_path = _choose_rom(folder, console, prompt, interactive)
        cover_path = _select_cover(folder, console, prompt, interactive)

        if not rom_path:
            if cover_path:
                updated = _update_existing_game_cover(folder, cover_path, roms_root, console)
                if updated:
                    dest_cover, rom_file = updated
                    shutil.rmtree(folder)
                    console.print(
                        f"[green]🎨 {folder.name} → {rom_file.parent.name}/{dest_cover.name}[/green]"
                    )
                    inserted.append(dest_cover)
                    continue
                console.print(
                    f"[yellow]⚠️ {folder.name}: no se encontró juego coincidiente para actualizar portada.[/yellow]"
                )
            else:
                console.print(f"[yellow]⚠️ Saltando {folder.name}; no se seleccionó ROM.[/yellow]")
            continue

        platform = _choose_platform(rom_path.suffix, console, prompt, interactive)
        if not platform:
            console.print(f"[yellow]⚠️ {rom_path.name}: no se pudo determinar plataforma.[/yellow]")
            continue

        folder_index, folder_base = _extract_index_components(folder.name)
        rom_index, rom_base = _extract_index_components(rom_path.stem)
        if rom_index is not None:
            explicit_index = rom_index
            slug_source = rom_base
        elif folder_index is not None:
            explicit_index = folder_index
            slug_source = folder_base
        else:
            explicit_index = None
            slug_source = folder.name

        slug = slugify(slug_source)

        platform_dir = roms_root / platform
        images_dir = platform_dir / "Imgs"
        platform_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        if platform_dir not in cleaned_platforms:
            _cleanup_platform_directory(platform_dir)
            cleaned_platforms.add(platform_dir)

        cover_matches = _remove_existing_slug(
            platform_dir,
            images_dir,
            slug,
            preserve_index=explicit_index,
        )

        suffix = rom_path.suffix.lower()
        if explicit_index is not None:
            dest_index = explicit_index
            dest_basename = f"{dest_index:03d}_{slug}"
            existing_covers = _remove_existing_index(platform_dir, images_dir, dest_index)
            existing_covers.extend(cover_matches)
            dest_rom = platform_dir / f"{dest_basename}{suffix}"
        else:
            dest_index = _next_index_for_platform(platform_dir)
            dest_basename = f"{dest_index:03d}_{slug}"
            dest_rom = platform_dir / f"{dest_basename}{suffix}"
            while dest_rom.exists():
                dest_index += 1
                dest_basename = f"{dest_index:03d}_{slug}"
                dest_rom = platform_dir / f"{dest_basename}{suffix}"
            existing_covers = cover_matches

        shutil.copy2(rom_path, dest_rom)

        if cover_path and cover_path.exists():
            dest_cover = images_dir / f"{dest_basename}.png"
            try:
                make_thumbnail(cover_path, dest_cover)
            except Exception as exc:  # pragma: no cover
                console.print(f"[yellow]⚠️ No se generó miniatura para {cover_path}: {exc}[/yellow]")
                shutil.copy2(cover_path, dest_cover)
            for cover in existing_covers:
                if cover.exists() and cover != dest_cover:
                    cover.unlink()
        else:
            dest_cover = images_dir / f"{dest_basename}.png"
            if dest_cover.exists():
                retained_cover = dest_cover
            elif existing_covers:
                source_cover = existing_covers[0]
                if source_cover.exists():
                    try:
                        make_thumbnail(source_cover, dest_cover)
                    except Exception as exc:  # pragma: no cover
                        console.print(f"[yellow]⚠️ No se generó miniatura para {source_cover}: {exc}[/yellow]")
                        shutil.copy2(source_cover, dest_cover)
                    retained_cover = dest_cover
                else:
                    retained_cover = None
            else:
                retained_cover = None
            for cover in existing_covers:
                if cover.exists() and cover != retained_cover:
                    cover.unlink()

        shutil.rmtree(folder)
        console.print(f"[green]✅ {folder.name} → {platform}/{dest_rom.name}[/green]")
        inserted.append(dest_rom)

    if inserted:
        console.print(Panel.fit(
            f"[bold green]👍 Se insertaron {len(inserted)} juegos al backup.[/bold green]",
            border_style="green",
        ))
    else:
        console.print("[yellow]No se insertaron juegos.[/yellow]")

    return inserted


def _cleanup_platform_directory(platform_dir: Path) -> None:
    if not platform_dir.exists():
        return

    for entry in list(platform_dir.iterdir()):
        if entry.name == "Imgs":
            continue
        if entry.is_dir():
            if not INDEXED_NAME_PATTERN.match(entry.name):
                shutil.rmtree(entry)
        elif entry.is_file():
            if not INDEXED_NAME_PATTERN.match(entry.stem):
                entry.unlink()


def _remove_existing_index(platform_dir: Path, images_dir: Path, index: int) -> list[Path]:
    prefix = f"{index:03d}_"
    existing_covers: list[Path] = []
    for entry in list(platform_dir.iterdir()):
        if entry == images_dir:
            continue
        if entry.name.startswith(prefix):
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

    if images_dir.exists():
        existing_covers = list(images_dir.glob(f"{prefix}*.png"))
    return existing_covers


def _remove_existing_slug(
    platform_dir: Path,
    images_dir: Path,
    slug: str,
    preserve_index: int | None,
) -> list[Path]:
    """Remove ROM entries that share the same slug but different index.

    Returns any matching cover paths so callers can decide whether to reuse or delete
    them after reindexing.
    """

    matched_covers: list[Path] = []

    for entry in list(platform_dir.iterdir()):
        if entry == images_dir:
            continue

        name = entry.stem if entry.is_file() else entry.name
        index, base_name = _extract_index_components(name)
        if slugify(base_name) != slug:
            continue
        if preserve_index is not None and index == preserve_index:
            continue

        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()

    if images_dir.exists():
        for cover in images_dir.glob("*.png"):
            index, base_name = _extract_index_components(cover.stem)
            if slugify(base_name) != slug:
                continue
            if preserve_index is not None and index == preserve_index:
                continue
            matched_covers.append(cover)

    return matched_covers
