# test_gamesdb.py
import rich.segment
from pathlib import Path
import subprocess

import gamesdb
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()

TARGET_DIR = gamesdb.TARGET_DIR
OUTPUT_DIR = gamesdb.OUTPUT_DIR
DATASETS_DIR = gamesdb.DATASETS_DIR


def test_generate_paths():
    """Test generation of path list file."""
    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Testing path list generation[/green]",
        border_style="cyan"
    ))

    output_file = OUTPUT_DIR / "paths.txt"
    console.print(f"[yellow]🚀 Generating path list in:[/yellow] {output_file}")
    get_paths(TARGET_DIR, output_file)

    assert output_file.exists(), "❌ paths.txt was not created"
    console.print(f"[green]✅ Created:[/green] {output_file}")

def test_export_datasets():
    """Test dataset export for all subdirectories."""
    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Testing dataset export[/green]",
        border_style="cyan"
    ))

    console.print(f"[yellow]📦 Exporting datasets to:[/yellow] {DATASETS_DIR}\n")
    subdirs = [d for d in TARGET_DIR.iterdir() if d.is_dir() and d.name not in {'.venv', '__pycache__', 'datasets', 'output'}]

    for subdir in track(subdirs, description="[cyan]Processing directories...[/cyan]"):
        export_dataset(DATASETS_DIR, subdir)

    console.print(Panel.fit(
        "[bold green]✅ Dataset export test completed successfully![/bold green]",
        border_style="green"
    ))


def test_server_ping():
    """Ensure the configured server responds to ICMP ping."""
    host_ip = gamesdb.GAMESDB_CONFIG["server"]["ip"]
    host_port = gamesdb.GAMESDB_CONFIG["server"]["port"]

    console.print(Panel.fit(
        "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Testing server connectivity[/green]",
        border_style="cyan"
    ))
    console.print(f"[yellow]📡 Pinging host:[/yellow] {host_ip} (port {host_port})")

    result = subprocess.run(
        ["ping", "-c", "2", host_ip],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"❌ Ping to {host_ip}:{host_port} failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    console.print(f"[green]✅ Host reachable:[/green] {host_ip}:{host_port}")


if __name__ == '__main__':
    console.print("-" * 125)
    test_server_ping()
    console.print("-" * 125)
    test_generate_paths()
    console.print("-"*125)
    test_export_datasets()
