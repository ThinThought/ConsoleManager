#!/usr/bin/env python3
"""Backup CLI utilities for syncing the RG34XX SD card."""

import argparse
from datetime import datetime
from pathlib import Path
import subprocess

import gamesdb
from rich.console import Console
from rich.panel import Panel

console = Console()

remote_sd_dir = gamesdb.GAMESDB_CONFIG["paths"]["backup_remote_sd_dir"]
remote_mmc_dir = gamesdb.GAMESDB_CONFIG["paths"]["backup_remote_mmc_dir"]
user = gamesdb.GAMESDB_CONFIG["server"]["user"]
host = gamesdb.GAMESDB_CONFIG["server"]["ip"]


BACKUP_SD_SOURCE = f"{user}@{host}:{remote_sd_dir}/"
BACKUP_MMC_SOURCE = f"{user}@{host}:{remote_mmc_dir}/"

BACKUP_DIR = Path(gamesdb.GAMESDB_CONFIG["paths"]["sdcard_backup_dir"])

def run_sd_backup():
    """Sync /mnt/sdcard into a dated snapshot under sdcard_backup_dir."""
    snapshot_dir = BACKUP_DIR / datetime.now().strftime("%Y-%m-%d")
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Starting SD card backup[/green]",
        border_style="cyan"
    ))

    try:
        console.print(f"[yellow]📂 Source:[/yellow] {BACKUP_SD_SOURCE}")
        console.print(f"[yellow]💾 Destination:[/yellow] {snapshot_dir}")
        cmd = [
            "rsync",
            "-avz",
            "--delete",
            BACKUP_SD_SOURCE,
            str(snapshot_dir),
        ]
        console.print(f"[blue]$ {' '.join(cmd)}[/blue]")
        snapshot_dir = BACKUP_DIR / "latest"
        subprocess.run(cmd, check=True, text=True)
        cmd = [
            "rsync",
            "-avz",
            "--delete",
            BACKUP_SD_SOURCE,
            str(snapshot_dir),
        ]
        console.print(f"[blue]$ {' '.join(cmd)}[/blue]")
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as proc_err:
        console.print(f"[red]{proc_err}[/red]")
        raise SystemExit(1)

    console.print(Panel.fit(
        "[bold green]✅ Backup completed successfully![/bold green]",
        border_style="green"
    ))

def run_systems_backup():
    snapshot_dir = BACKUP_DIR / f"mmc"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Starting System backup[/green]",
        border_style="cyan"
    ))
    try:
        console.print(f"[yellow]📂 Source:[/yellow] {BACKUP_MMC_SOURCE}")
        console.print(f"[yellow]💾 Destination:[/yellow] {snapshot_dir}")
        cmd = [
            "rsync",
            "-avz",
            "--delete",
            BACKUP_MMC_SOURCE,
            str(snapshot_dir),
        ]
        console.print(f"[blue]$ {' '.join(cmd)}[/blue]")
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as proc_err:
        console.print(f"[red]{proc_err}[/red]")
        raise SystemExit(1)


def restore_sd_backup(snapshot_name: str):
    """Restore a dated snapshot back into /mnt/sdcard."""
    backup_root = Path(
        gamesdb.GAMESDB_CONFIG["paths"]["sdcard_backup_dir"]
    ).expanduser().resolve()

    snapshot_dir = (backup_root / snapshot_name).resolve()
    if not snapshot_dir.exists():
        raise FileNotFoundError(f"Snapshot '{snapshot_name}' not found at {snapshot_dir}")

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Restoring SD card snapshot[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📂 Snapshot:[/yellow] {snapshot_dir}")
    console.print(f"[yellow]💾 Destination:[/yellow] {BACKUP_SD_SOURCE}")

    cmd = [
        "rsync",
        "-a",
        "--delete",
        "--info=progress2",
        f"{snapshot_dir}/",
        str(BACKUP_SD_SOURCE),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"❌ Restore failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    console.print(Panel.fit(
        "[bold green]✅ Restore completed successfully![/bold green]",
        border_style="green"
    ))
    if result.stdout.strip():
        console.print(result.stdout)

