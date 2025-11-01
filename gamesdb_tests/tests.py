# test_gamesdb.py
import subprocess
from pathlib import Path

import gamesdb
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from main import build_parser
from gamesdb.get_games import get_games


TARGET_DIR = gamesdb.TARGET_DIR
OUTPUT_DIR = gamesdb.OUTPUT_DIR
DATASETS_DIR = gamesdb.DATASETS_DIR


def test_generate_paths():
    """Test generation of path list file."""
    output_file = OUTPUT_DIR / "paths.txt"
    get_paths(TARGET_DIR, output_file)
    assert output_file.exists(), "❌ paths.txt was not created"

def test_export_datasets():
    """Test dataset export for all subdirectories."""
    subdirs = [d for d in TARGET_DIR.iterdir() if d.is_dir() and d.name not in {'.venv', '__pycache__', 'datasets', 'output'}]
    for subdir in subdirs:
        export_dataset(DATASETS_DIR, subdir)


def test_server_ping():
    """Ensure the configured server responds to ICMP ping."""
    host_ip = gamesdb.GAMESDB_CONFIG["server"]["ip"]
    host_port = gamesdb.GAMESDB_CONFIG["server"]["port"]
    result = subprocess.run(
        ["ping", "-c", "2", host_ip],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"❌ Ping to {host_ip}:{host_port} failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_thumbnailer_parser_handles_paths():
    """Verify the main CLI parses thumbnailer arguments into Paths."""
    parser = build_parser()
    args = parser.parse_args(["thumbnailer", "cover.jpg", "out.png"])
    assert args.command == "thumbnailer"
    assert args.input_image == Path("cover.jpg")
    assert args.output_image == Path("out.png")


def test_get_games_reindexes_rom_and_png(tmp_path):
    """Ensure get_games creates per-game directories with ROM and artwork."""
    roms_root = tmp_path / "Roms"
    platform_dir = roms_root / "FC"
    images_dir = platform_dir / "Imgs"
    platform_dir.mkdir(parents=True)
    images_dir.mkdir()

    rom_path = platform_dir / "001_Ghostn_Goblins.nes"
    rom_path.write_text("dummy rom data", encoding="utf-8")
    png_path = images_dir / "001_Ghostn_Goblins.png"
    png_path.write_bytes(b"PNGDATA")

    destination_root = tmp_path / "output"
    created_dirs = get_games(roms_root, destination_root)

    expected_game_dir = destination_root / "001_Ghostn_Goblins"
    assert expected_game_dir in created_dirs
    assert (expected_game_dir / "001_Ghostn_Goblins.nes").read_text(encoding="utf-8") == "dummy rom data"
    assert (expected_game_dir / "001_Ghostn_Goblins.png").read_bytes() == b"PNGDATA"
