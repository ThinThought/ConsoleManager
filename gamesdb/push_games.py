"""Interactive helper to push staged games into the backup tree."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re
import shutil

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import gamesdb
from gamesdb.naming import slugify
from gamesdb.platforms import EXTENSION_PLATFORMS
from gamesdb.thumbnailer import make_thumbnail

PromptFn = Callable[[str], str]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
INDEXED_DIR_PATTERN = re.compile(r"^\d{3}_.+")
INDEXED_NAME_PATTERN = re.compile(r"^\d{3}_")


def _list_staged_directories(staging_dir: Path) -> list[Path]:
    if not staging_dir.exists():
        return []
    dirs = []
    for child in sorted(staging_dir.iterdir()):
        if child.is_dir() and not INDEXED_DIR_PATTERN.match(child.name):
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
        if not rom_path:
            console.print(f"[yellow]⚠️ Saltando {folder.name}; no se seleccionó ROM.[/yellow]")
            continue

        platform = _choose_platform(rom_path.suffix, console, prompt, interactive)
        if not platform:
            console.print(f"[yellow]⚠️ {rom_path.name}: no se pudo determinar plataforma.[/yellow]")
            continue

        platform_dir = roms_root / platform
        images_dir = platform_dir / "Imgs"
        platform_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        if platform_dir not in cleaned_platforms:
            _cleanup_platform_directory(platform_dir)
            cleaned_platforms.add(platform_dir)

        slug = slugify(folder.name)
        next_index = _next_index_for_platform(platform_dir)
        dest_rom = platform_dir / f"{next_index:03d}_{slug}{rom_path.suffix.lower()}"
        while dest_rom.exists():
            next_index += 1
            dest_rom = platform_dir / f"{next_index:03d}_{slug}{rom_path.suffix.lower()}"

        shutil.copy2(rom_path, dest_rom)

        cover_path = _select_cover(folder, console, prompt, interactive)
        if cover_path and cover_path.exists():
            dest_cover = images_dir / f"{dest_rom.stem}.png"
            try:
                make_thumbnail(cover_path, dest_cover)
            except Exception as exc:  # pragma: no cover
                console.print(f"[yellow]⚠️ No se generó miniatura para {cover_path}: {exc}[/yellow]")
                shutil.copy2(cover_path, dest_cover)

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
