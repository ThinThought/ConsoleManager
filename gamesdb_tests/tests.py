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
    """Ensure get_games normalizes numbering and copies ROMs/artwork."""
    roms_root = tmp_path / "Roms"
    platform_dir = roms_root / "FC"
    images_dir = platform_dir / "Imgs"
    platform_dir.mkdir(parents=True)
    images_dir.mkdir()

    rom_prefixed = platform_dir / "002_Legend_of_Zelda.nes"
    rom_prefixed.write_text("legend rom", encoding="utf-8")
    (images_dir / "Legend_of_Zelda.png").write_bytes(b"PNG1")

    rom_plain = platform_dir / "Metroid.nes"
    rom_plain.write_text("metroid rom", encoding="utf-8")
    (images_dir / "Metroid.png").write_bytes(b"PNG2")

    rom_new = platform_dir / "rythm_tengoku.gba"
    rom_new.write_text("paradise rom", encoding="utf-8")
    (images_dir / "New Rythm Paradise.png").write_bytes(b"PNG3")

    destination_root = tmp_path / "output"
    stale_dir = destination_root / "999_OldGame"
    stale_dir.mkdir(parents=True)
    (stale_dir / "stale.txt").write_text("stale", encoding="utf-8")

    created_dirs = get_games(roms_root, destination_root)

    folder_names = [p.name for p in created_dirs]
    assert folder_names == ["001_Legend_Of_Zelda", "002_Metroid", "003_New_Rythm_Paradise"]

    legend_dir = destination_root / "001_Legend_Of_Zelda"
    metroid_dir = destination_root / "002_Metroid"
    paradise_dir = destination_root / "003_New_Rythm_Paradise"

    assert (legend_dir / "002_Legend_of_Zelda.nes").read_text(encoding="utf-8") == "legend rom"
    assert (legend_dir / "Legend_of_Zelda.png").read_bytes() == b"PNG1"

    assert (metroid_dir / "Metroid.nes").read_text(encoding="utf-8") == "metroid rom"
    assert (metroid_dir / "Metroid.png").read_bytes() == b"PNG2"
    assert (paradise_dir / "rythm_tengoku.gba").read_text(encoding="utf-8") == "paradise rom"
    assert (paradise_dir / "New Rythm Paradise.png").read_bytes() == b"PNG3"
    assert not stale_dir.exists()
