# test_gamesdb.py
from pathlib import Path
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()

TARGET_DIR = Path(".")
OUTPUT_DIR = Path("./gamesdb_localdata")
DATASETS_DIR = OUTPUT_DIR / "datasets"

def setup_dirs():
    """Ensure required directories exist."""
    for d in [OUTPUT_DIR, DATASETS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def test_generate_paths():
    """Test generation of path list file."""
    setup_dirs()
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
    setup_dirs()
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


if __name__ == '__main__':
    test_generate_paths()
    test_export_datasets()