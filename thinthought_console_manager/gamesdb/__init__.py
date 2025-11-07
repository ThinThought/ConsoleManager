from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path
import yaml

from .config_editor import resolve_config_path

def setup_dirs(path_list: list[Path] | None = None):
    """Ensure required directories exist."""
    for d in path_list or []:
        d.mkdir(parents=True, exist_ok=True)

def _resolve_local_path(path_value: str) -> Path:
    """Turn a config path into an absolute location under the current HOME."""
    resolved = Path(path_value).expanduser()
    if not resolved.is_absolute():
        resolved = Path.home() / resolved
    return resolved.resolve()

console = Console()

CONFIG_PATH = resolve_config_path()
GAMESDB_CONFIG = yaml.safe_load(Path(CONFIG_PATH).read_text(encoding="utf-8"))

local_path_keys = [k for k in GAMESDB_CONFIG["paths"] if "remote" not in k]

for key in local_path_keys:
    absolute_path = _resolve_local_path(GAMESDB_CONFIG["paths"][key])
    GAMESDB_CONFIG["paths"][key] = str(absolute_path)

TARGET_DIR = Path(GAMESDB_CONFIG["paths"]["target_dir"])
OUTPUT_DIR = Path(GAMESDB_CONFIG["paths"]["output_dir"])
DATASETS_DIR = Path(GAMESDB_CONFIG["paths"]["datasets_dir"])

text = GAMESDB_CONFIG['server']
yaml_text = yaml.dump(text, sort_keys=False, default_flow_style=False)
syntax = Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False)
paths = [Path(p) for k, p in GAMESDB_CONFIG["paths"].items() if "remote" not in k]
setup_dirs(paths)

console.print(Panel.fit(
    "[cyan]     loaded successfully! [cyan]",
    title="[bold green]ThinThought Console Manager[/bold green]",
    border_style="green"
))
console.print(Panel.fit(
    syntax,
    title="[bold yellow]Server[/bold yellow]",
    border_style="yellow"
))
