from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path
import yaml
from importlib.resources import files

def setup_dirs(path_list: list[Path] = None):
    """Ensure required directories exist."""
    for d in path_list:
        d.mkdir(parents=True, exist_ok=True)


console = Console()

console.print(Panel.fit(
    "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Config has been loaded[/green]",
    border_style="cyan"
))

config_path = files("gamesdb.data.config").joinpath("config.yaml")

GAMESDB_CONFIG = yaml.safe_load(config_path.read_text())

TARGET_DIR = Path(GAMESDB_CONFIG["paths"]["target_dir"])
OUTPUT_DIR = Path(GAMESDB_CONFIG["paths"]["output_dir"])
DATASETS_DIR = Path(GAMESDB_CONFIG["paths"]["datasets_dir"])

yaml_text = yaml.dump(GAMESDB_CONFIG, sort_keys=False, default_flow_style=False)
syntax = Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False)
console.print(Panel.fit(
    syntax,
    title="[bold yellow]Current Configuration[/bold yellow]",
    border_style="yellow"
))
paths = [Path(p) for k, p in GAMESDB_CONFIG["paths"].items() if "remote" not in k]
setup_dirs(paths)