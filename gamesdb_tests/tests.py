# test_gamesdb.py
import subprocess
from pathlib import Path

import cv2
import numpy as np

import gamesdb
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from gamesdb.cli import build_parser
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
    """Ensure get_games normalizes numbering, copies ROMs/artwork, and thumbnails images."""
    roms_root = tmp_path / "Roms"
    platform_dir = roms_root / "FC"
    images_dir = platform_dir / "Imgs"
    platform_dir.mkdir(parents=True)
    images_dir.mkdir()

    rom_prefixed = platform_dir / "002_Legend_of_Zelda.nes"
    rom_prefixed.write_text("legend rom", encoding="utf-8")
    legend_png = images_dir / "Legend_of_Zelda.png"

    rom_plain = platform_dir / "Metroid.nes"
    rom_plain.write_text("metroid rom", encoding="utf-8")
    metroid_png = images_dir / "Metroid.png"

    rom_new = platform_dir / "new_rythm_paradise.gba"
    rom_new.write_text("paradise rom", encoding="utf-8")
    paradise_png = images_dir / "New Rythm Paradise.png"

    for idx, target_png in enumerate([legend_png, metroid_png, paradise_png], start=1):
        image = np.full((40, 30, 3), idx * 50, dtype=np.uint8)
        success, data = cv2.imencode(".png", image)
        assert success
        target_png.write_bytes(data.tobytes())

    destination_root = tmp_path / "output"
    stale_dir = destination_root / "999_OldGame"
    stale_dir.mkdir(parents=True)
    (stale_dir / "stale.txt").write_text("stale", encoding="utf-8")

    manual_dir = destination_root / "Mario Bros"
    manual_dir.mkdir(parents=True)
    manual_rom = manual_dir / "mario_bros.gba"
    manual_rom.write_text("mario rom", encoding="utf-8")
    manual_png = manual_dir / "Mario Bros.png"
    success, data = cv2.imencode(".png", np.full((42, 42, 3), 180, dtype=np.uint8))
    assert success
    manual_png.write_bytes(data.tobytes())

    created_dirs = get_games(roms_root, destination_root)

    folder_names = [p.name for p in created_dirs]
    assert folder_names == [
        "001_Legend_Of_Zelda",
        "002_Mario_Bros",
        "003_Metroid",
        "004_New_Rythm_Paradise",
    ]

    legend_dir = destination_root / "001_Legend_Of_Zelda"
    mario_dir = destination_root / "002_Mario_Bros"
    metroid_dir = destination_root / "003_Metroid"
    paradise_dir = destination_root / "004_New_Rythm_Paradise"

    assert (legend_dir / "002_Legend_of_Zelda.nes").read_text(encoding="utf-8") == "legend rom"
    legend_img = cv2.imread(str(legend_dir / "Legend_of_Zelda.png"), cv2.IMREAD_UNCHANGED)
    assert legend_img.shape[:2] == (160, 256)

    assert (mario_dir / "001_Mario_Bros.gba").read_text(encoding="utf-8") == "mario rom"
    mario_img = cv2.imread(str(mario_dir / "001_Mario_Bros.png"), cv2.IMREAD_UNCHANGED)
    assert mario_img.shape[:2] == (160, 256)

    assert (metroid_dir / "Metroid.nes").read_text(encoding="utf-8") == "metroid rom"
    metroid_img = cv2.imread(str(metroid_dir / "Metroid.png"), cv2.IMREAD_UNCHANGED)
    assert metroid_img.shape[:2] == (160, 256)

    assert (paradise_dir / "new_rythm_paradise.gba").read_text(encoding="utf-8") == "paradise rom"
    paradise_img = cv2.imread(str(paradise_dir / "New Rythm Paradise.png"), cv2.IMREAD_UNCHANGED)
    assert paradise_img.shape[:2] == (160, 256)
    assert not stale_dir.exists()
    assert not manual_dir.exists()

    gba_dir = roms_root / "GBA"
    assert (gba_dir / "001_Mario_Bros.gba").read_text(encoding="utf-8") == "mario rom"
    gba_image = cv2.imread(str(gba_dir / "Imgs" / "001_Mario_Bros.png"), cv2.IMREAD_UNCHANGED)
    assert gba_image.shape[:2] == (160, 256)
