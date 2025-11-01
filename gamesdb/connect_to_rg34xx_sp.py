from importlib.resources import files
from pathlib import Path
import subprocess
import yaml

CONFIG_PATH = files("gamesdb.data.config").joinpath("config.yaml")

def connect_to_device():
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    host = cfg["server"]["name"]
    user = cfg["server"]["user"]
    subprocess.run(
        [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{user}@{host}",
        ],
        check=True,
    )


if __name__ == "__main__":
    connect_to_device()