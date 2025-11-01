from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import yaml
from importlib.resources import files

console = Console()

console.print(Panel.fit(
    "[bold cyan]🎮 GamesDB[/bold cyan]\n[green]Config has been loaded[/green]",
    border_style="cyan"
))

config_path = files("gamesdb.data.config").joinpath("config.yaml")
GAMESDB_CONFIG = yaml.safe_load(config_path.read_text())

yaml_text = yaml.dump(GAMESDB_CONFIG, sort_keys=False, default_flow_style=False)
syntax = Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False)

console.print(syntax)
