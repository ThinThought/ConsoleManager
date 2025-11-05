#!/usr/bin/env python3
"""Command-line entry point for GamesDB helper utilities."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

import yaml
import gamesdb
from gamesdb.get_paths import get_paths
from gamesdb.get_games import iter_reindexed_games
from gamesdb.tree_to_csv_datasets import export_dataset
from gamesdb.backup_ops import run_sd_backup, restore_sd_backup, run_systems_backup
from gamesdb.thumbnailer import make_thumbnail
from gamesdb.push_games import push_games
from gamesdb.connect_gb import connect_to_device
from gamesdb.config_editor import set_config_value, ConfigUpdateResult, resolve_config_path
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()


def run_paths_command() -> None:
    """Generate a full path listing under TARGET_DIR."""
    output_txt = Path(gamesdb.GAMESDB_CONFIG["paths"]["artifacts_dir"]) / "paths.txt"
    gamesdb.OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Generating path index[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📂 Root:[/yellow] {gamesdb.OUTPUT_DIR}")
    console.print(f"[yellow]📝 Output:[/yellow] {output_txt}")

    target_dir = Path(gamesdb.GAMESDB_CONFIG["paths"]["output_dir"])
    get_paths(target_dir=target_dir, output=output_txt)
    console.print(f"[green]✅ Path index created at:[/green] {output_txt}")


def run_datasets_command(target: Path | None, dataset_dir: Path | None) -> None:
    """Export CSV datasets for each subdirectory."""
    target_dir = target or gamesdb.TARGET_DIR
    datasets_dir = dataset_dir or gamesdb.DATASETS_DIR
    datasets_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Exporting datasets[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📂 Target:[/yellow] {target_dir}")
    console.print(f"[yellow]💾 Dataset dir:[/yellow] {datasets_dir}")

    skip_names = {".venv", "__pycache__", "datasets", "output"}
    subdirs = [d for d in target_dir.iterdir() if d.is_dir() and d.name not in skip_names]

    for subdir in track(subdirs, description="[cyan]Processing directories...[/cyan]"):
        export_dataset(datasets_dir, subdir)

    console.print(Panel.fit(
        "[bold green]✅ Dataset export finished![/bold green]",
        border_style="green"
    ))


def run_ping_command(host_override: str | None, count: int) -> None:
    """Ping the configured server (or override) to validate connectivity."""
    server_cfg = gamesdb.GAMESDB_CONFIG["server"]
    host = host_override or server_cfg.get("ip") or server_cfg["name"]

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Testing server connectivity[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📡 Pinging host:[/yellow] {host} (count={count})")

    result = subprocess.run(
        ["ping", "-c", str(count), host],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        console.print(f"[red]❌ Ping failed[/red]\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        raise SystemExit(result.returncode)

    console.print(Panel.fit(
        "[bold green]✅ Host reachable![/bold green]",
        border_style="green"
    ))
    if result.stdout.strip():
        console.print(result.stdout)

def run_connect_command(host_override: str | None, user_override: str | None, port_override: int | None) -> None:
    """Open an SSH session against the configured device."""
    server_cfg = gamesdb.GAMESDB_CONFIG.get("server", {})
    if not isinstance(server_cfg, dict):
        console.print("[red]❌ Server configuration is missing.[/red]")
        raise SystemExit(1)

    host = host_override or server_cfg.get("ip") or server_cfg.get("name")
    user = user_override or server_cfg.get("user", "root")
    port = port_override or server_cfg.get("port")

    if not isinstance(host, str) or not host:
        console.print("[red]❌ No host configured for SSH connection.[/red]")
        raise SystemExit(1)
    if not isinstance(user, str) or not user:
        console.print("[red]❌ No user configured for SSH connection.[/red]")
        raise SystemExit(1)

    port_display = str(port) if port else "default"

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Opening SSH session[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]👤 User:[/yellow] {user}")
    console.print(f"[yellow]📡 Host:[/yellow] {host}")
    console.print(f"[yellow]🔌 Port:[/yellow] {port_display}")

    try:
        connect_to_device(host=host_override, user=user_override, port=port_override)
    except subprocess.CalledProcessError as exc:
        console.print(Panel.fit(
            f"[bold red]SSH session exited with code {exc.returncode}[/bold red]",
            border_style="red"
        ))
        raise SystemExit(exc.returncode) from exc

    console.print(Panel.fit(
        "[bold green]✅ SSH session closed[/bold green]",
        border_style="green"
    ))


def run_thumbnail_command(input_image: Path, output_image: Path) -> None:
    """Generate a thumbnail using the configured thumbnailer utility."""
    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Generating thumbnail[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]🖼️ Source:[/yellow] {input_image}")
    console.print(f"[yellow]💾 Output:[/yellow] {output_image}")

    make_thumbnail(input_image, output_image)

    console.print(Panel.fit(
        "[bold green]✅ Thumbnail created![/bold green]",
        border_style="green"
    ))


def run_get_games_command(roms_dir: Path | None, output_dir: Path | None, platforms: list[str] | None) -> None:
    """Reindex ROMs into per-game folders, copying paired artwork when available."""
    roms_root = roms_dir or Path(gamesdb.GAMESDB_CONFIG["paths"]["roms_dir"])
    destination_root = output_dir or Path(gamesdb.GAMESDB_CONFIG["paths"]["games_to_include_dir"])
    platform_filter = set(platforms) if platforms else None

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Reindexing games[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📂 ROM source:[/yellow] {roms_root}")
    console.print(f"[yellow]📂 Output root:[/yellow] {destination_root}")
    if platform_filter:
        console.print(f"[yellow]🎯 Platforms:[/yellow] {', '.join(sorted(platform_filter))}")

    created = list(track(
        iter_reindexed_games(roms_root, destination_root, platforms=platform_filter),
        description="[cyan]Copying assets[/cyan]",
    ))

    console.print(Panel.fit(
        f"[bold green]✅ Reindexed {len(created)} games[/bold green]",
        border_style="green"
    ))


def run_push_command() -> None:
    """Move staged games from games_to_include into the backup tree."""
    push_games(console=console)

def _format_value_for_display(value: object) -> str:
    return yaml.safe_dump(value, sort_keys=False, default_flow_style=False).strip()


def _sync_runtime_config(update_result: ConfigUpdateResult) -> None:
    gamesdb.CONFIG_PATH = Path(update_result.config_path)
    gamesdb.GAMESDB_CONFIG = update_result.config
    paths = update_result.config.get("paths", {})
    if isinstance(paths, dict):
        if "target_dir" in paths:
            gamesdb.TARGET_DIR = Path(paths["target_dir"])
        if "output_dir" in paths:
            gamesdb.OUTPUT_DIR = Path(paths["output_dir"])
        if "datasets_dir" in paths:
            gamesdb.DATASETS_DIR = Path(paths["datasets_dir"])
        local_paths = [
            Path(p) for key, p in paths.items() if "remote" not in key and isinstance(p, str)
        ]
        gamesdb.setup_dirs(local_paths)


def run_config_set_command(key: str, value: str, config_path: Path | None) -> None:
    """Update a YAML configuration value."""
    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Updating configuration[/green]",
        border_style="cyan"
    ))
    resolved_path = resolve_config_path(config_path)
    console.print(f"[yellow]📄 Config file:[/yellow] {resolved_path}")
    console.print(f"[yellow]🔑 Key:[/yellow] {key}")
    try:
        update_result = set_config_value(key, value, config_path=resolved_path)
    except (KeyError, ValueError) as exc:
        console.print(f"[red]❌ {exc}[/red]")
        raise SystemExit(1) from exc

    _sync_runtime_config(update_result)

    console.print(f"[yellow]🪄 Old:[/yellow] {_format_value_for_display(update_result.old_value)}")
    console.print(f"[yellow]✅ New:[/yellow] {_format_value_for_display(update_result.new_value)}")
    console.print(Panel.fit(
        "[bold green]Configuration saved[/bold green]",
        border_style="green"
    ))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GamesDB utility launcher.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("paths", help="Generate a paths.txt index.")

    datasets_parser = subparsers.add_parser("datasets", help="Export CSV datasets for each subdirectory.")
    datasets_parser.add_argument(
        "--target",
        "-t",
        type=Path,
        help="Root directory to scan (defaults to config TARGET_DIR).",
    )
    datasets_parser.add_argument(
        "--datasets-dir",
        "-d",
        type=Path,
        help="Destination directory for CSV files (defaults to config DATASETS_DIR).",
    )

    subparsers.add_parser("backup-sd", help="Create a dated backup snapshot.")
    subparsers.add_parser("backup-system", help="Create a dated backup snapshot.")

    ping_parser = subparsers.add_parser("ping", help="Ping the configured server.")
    ping_parser.add_argument(
        "--host",
        "-H",
        help="Override host/IP to ping (defaults to config).",
    )
    ping_parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=1,
        help="Number of ICMP echo requests to send (default: 1).",
    )
    connect_parser = subparsers.add_parser("connect", help="Open an SSH shell to the configured device.")
    connect_parser.add_argument(
        "--host",
        "-H",
        help="Override host/IP to connect (defaults to config).",
    )
    connect_parser.add_argument(
        "--user",
        "-u",
        help="Override SSH user (defaults to config).",
    )
    connect_parser.add_argument(
        "--port",
        "-p",
        type=int,
        help="Override SSH port (defaults to config).",
    )

    restore_parser = subparsers.add_parser("restore", help="Restore from a dated snapshot.")
    restore_parser.add_argument(
        "snapshot",
        help="Snapshot name to restore (e.g., 2024-11-01).",
    )

    thumbnail_parser = subparsers.add_parser(
        "thumbnailer",
        help="Generate a 256x160 transparent-background thumbnail.",
    )
    thumbnail_parser.add_argument(
        "input_image",
        type=Path,
        help="Path to the source image.",
    )
    thumbnail_parser.add_argument(
        "output_image",
        type=Path,
        help="Where to write the generated PNG thumbnail.",
    )

    get_games_parser = subparsers.add_parser(
        "get-games",
        help="Copy ROMs and associated PNG artwork into per-game folders.",
    )
    get_games_parser.add_argument(
        "--roms-dir",
        type=Path,
        help="Override the ROM source directory (defaults to config roms_dir).",
    )
    get_games_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Override the destination directory (defaults to config games_to_include_dir).",
    )
    get_games_parser.add_argument(
        "--platform",
        action="append",
        help="Limit processing to a specific platform (can be passed multiple times).",
    )

    subparsers.add_parser(
        "push",
        help="Insertar juegos pendientes de games_to_include en el backup.",
    )

    config_parser = subparsers.add_parser("config", help="Inspect or modify configuration.")
    config_parser.add_argument(
        "--config",
        type=Path,
        help="Override the config.yaml path (defaults to packaged config or env override).",
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_set_parser = config_subparsers.add_parser("set", help="Update a configuration value.")
    config_set_parser.add_argument(
        "key",
        help="Dot-separated path to the configuration key (e.g., paths.target_dir).",
    )
    config_set_parser.add_argument(
        "value",
        help="New value expressed as a YAML literal.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "paths":
        run_paths_command()
    elif args.command == "datasets":
        run_datasets_command(args.target, args.datasets_dir)
    elif args.command == "backup-sd":
        run_sd_backup()
    elif args.command == "backup-system":
        run_systems_backup()
    elif args.command == "ping":
        run_ping_command(args.host, args.count)
    elif args.command == "connect":
        run_connect_command(args.host, args.user, args.port)
    elif args.command == "restore":
        restore_sd_backup(args.snapshot)
    elif args.command == "thumbnailer":
        run_thumbnail_command(args.input_image, args.output_image)
    elif args.command == "get-games":
        run_get_games_command(args.roms_dir, args.output_dir, args.platform)
    elif args.command == "push":
        run_push_command()
    elif args.command == "config":
        if args.config_command == "set":
            run_config_set_command(args.key, args.value, args.config)
        else:
            parser.error(f"Unknown config subcommand {args.config_command}")
    else:
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
