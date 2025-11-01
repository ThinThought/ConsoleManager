#!/usr/bin/env python3
"""Command-line entry point for GamesDB helper utilities."""

import argparse
from pathlib import Path
import subprocess

import gamesdb
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from gamesdb.backup_ops import run_backup, restore_backup
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()


def run_paths_command():
    """Generate a full path listing under TARGET_DIR."""
    output_txt = Path(gamesdb.GAMESDB_CONFIG['paths']['artifacts_dir']) / "paths.txt"
    gamesdb.OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Generating path index[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📂 Root:[/yellow] {gamesdb.OUTPUT_DIR}")
    console.print(f"[yellow]📝 Output:[/yellow] {output_txt}")

    target_dir = Path(gamesdb.GAMESDB_CONFIG['paths']['output_dir'])
    get_paths(target_dir=target_dir, output=output_txt)
    console.print(f"[green]✅ Path index created at:[/green] {output_txt}")


def run_datasets_command(target: Path | None, dataset_dir: Path | None):
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


def run_ping_command(host_override: str | None, count: int):
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GamesDB utility launcher.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    paths_parser = subparsers.add_parser("paths", help="Generate a paths.txt index.")

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

    subparsers.add_parser("backup", help="Create a dated backup snapshot.")

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

    restore_parser = subparsers.add_parser("restore", help="Restore from a dated snapshot.")
    restore_parser.add_argument(
        "snapshot",
        help="Snapshot name to restore (e.g., 2024-11-01).",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "paths":
        run_paths_command()
    elif args.command == "datasets":
        run_datasets_command(args.target, args.datasets_dir)
    elif args.command == "backup":
        run_backup()
    elif args.command == "ping":
        run_ping_command(args.host, args.count)
    elif args.command == "restore":
        restore_backup(args.snapshot)
    else:
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
