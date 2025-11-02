# test_gamesdb.py
import subprocess
from pathlib import Path

import cv2
import numpy as np
from rich.console import Console

import gamesdb
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from gamesdb.cli import build_parser
from gamesdb.get_games import get_games
from gamesdb.push_games import push_games


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
    manual_rom = manual_dir / "Mario Bros.gba"
    manual_png = manual_dir / "Mario Bros.png"
    success, data = cv2.imencode(".png", np.full((42, 42, 3), 180, dtype=np.uint8))
    assert success
    manual_png.write_bytes(data.tobytes())
    manual_rom.write_text("mario rom", encoding="utf-8")

    push_games(
        staging_dir=destination_root,
        roms_root=roms_root,
        interactive=False,
        console=Console(record=True),
    )

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

    assert (legend_dir / "001_Legend_Of_Zelda.nes").read_text(encoding="utf-8") == "legend rom"
    legend_img = cv2.imread(str(legend_dir / "001_Legend_Of_Zelda.png"), cv2.IMREAD_UNCHANGED)
    assert legend_img.shape[:2] == (160, 256)

    assert (mario_dir / "002_Mario_Bros.gba").read_text(encoding="utf-8") == "mario rom"
    mario_img = cv2.imread(str(mario_dir / "002_Mario_Bros.png"), cv2.IMREAD_UNCHANGED)
    assert mario_img.shape[:2] == (160, 256)

    assert (metroid_dir / "003_Metroid.nes").read_text(encoding="utf-8") == "metroid rom"
    metroid_img = cv2.imread(str(metroid_dir / "003_Metroid.png"), cv2.IMREAD_UNCHANGED)
    assert metroid_img.shape[:2] == (160, 256)

    assert (paradise_dir / "004_New_Rythm_Paradise.gba").read_text(encoding="utf-8") == "paradise rom"
    paradise_img = cv2.imread(str(paradise_dir / "004_New_Rythm_Paradise.png"), cv2.IMREAD_UNCHANGED)
    assert paradise_img.shape[:2] == (160, 256)
    assert not stale_dir.exists()
    assert not manual_dir.exists()

    gba_dir = roms_root / "GBA"
    assert (gba_dir / "001_Mario_Bros.gba").read_text(encoding="utf-8") == "mario rom"
    gba_image = cv2.imread(str(gba_dir / "Imgs" / "001_Mario_Bros.png"), cv2.IMREAD_UNCHANGED)
    assert gba_image.shape[:2] == (160, 256)


def test_push_games_inserts_staged_title(tmp_path):
    """Ensure push_games moves staged directories into the ROM backup tree."""
    staging_dir = tmp_path / "games_to_include"
    game_dir = staging_dir / "Mega Man Zero"
    game_dir.mkdir(parents=True)

    rom_path = game_dir / "Mega Man Zero.gba"
    rom_path.write_bytes(b"ROMDATA")

    cover_img = np.full((50, 40, 3), 120, dtype=np.uint8)
    success, data = cv2.imencode(".png", cover_img)
    assert success
    cover_path = game_dir / "Mega Man Zero.png"
    cover_path.write_bytes(data.tobytes())

    roms_root = tmp_path / "Roms"
    # Crear residuos previos que no cumplen el formato para la plataforma GBA
    residual_dir = roms_root / "GBA" / "custom"
    residual_dir.mkdir(parents=True, exist_ok=True)
    residual_file = roms_root / "GBA" / "mega_man_zero.gba"
    residual_file.parent.mkdir(parents=True, exist_ok=True)
    residual_file.write_bytes(b"OLD")

    inserted = push_games(
        staging_dir=staging_dir,
        roms_root=roms_root,
        interactive=False,
        console=Console(record=True),
    )

    assert not game_dir.exists()
    platform_dir = roms_root / "GBA"
    expected_rom = platform_dir / "001_Mega_Man_Zero.gba"
    expected_cover = platform_dir / "Imgs" / "001_Mega_Man_Zero.png"
    assert inserted == [expected_rom]
    assert expected_rom.exists()
    assert expected_cover.exists()

    # residuos eliminados
    assert not residual_dir.exists()
    assert not residual_file.exists()

    thumb = cv2.imread(str(expected_cover), cv2.IMREAD_UNCHANGED)
    assert thumb.shape[:2] == (160, 256)


def test_push_games_updates_cover_only(tmp_path):
    """Ensure push_games can update the artwork of an already indexed game."""
    roms_root = tmp_path / "Roms"
    platform_dir = roms_root / "NES"
    images_dir = platform_dir / "Imgs"
    images_dir.mkdir(parents=True, exist_ok=True)

    rom_file = platform_dir / "001_Legend_Of_Zelda.nes"
    rom_file.write_bytes(b"ROMDATA")

    existing_thumb = np.full((160, 256, 3), 10, dtype=np.uint8)
    success, data = cv2.imencode(".png", existing_thumb)
    assert success
    (images_dir / "001_Legend_Of_Zelda.png").write_bytes(data.tobytes())

    staging_dir = tmp_path / "games_to_include" / "Legend Of Zelda"
    staging_dir.mkdir(parents=True, exist_ok=True)

    new_cover = np.full((90, 90, 3), 200, dtype=np.uint8)
    success, data = cv2.imencode(".png", new_cover)
    assert success
    cover_path = staging_dir / "001_Legend_Of_Zelda.png"
    cover_path.write_bytes(data.tobytes())
    assert list(staging_dir.iterdir()), "Cover file was not created"

    inserted = push_games(
        staging_dir=staging_dir.parent,
        roms_root=roms_root,
        interactive=False,
    )

    expected_cover = images_dir / "001_Legend_Of_Zelda.png"
    assert inserted == [expected_cover]
    assert not staging_dir.exists()
    assert rom_file.exists()

    updated_thumb = cv2.imread(str(expected_cover), cv2.IMREAD_UNCHANGED)
    assert updated_thumb.shape[:2] == (160, 256)
    # Nueva miniatura refleja el valor alto del cover actualizado
    assert updated_thumb[..., :3].mean() > 50


def test_push_games_overwrites_numbered_rom(tmp_path):
    """Ensure push_games replaces existing numbered ROMs with staged content."""
    roms_root = tmp_path / "Roms"
    platform_dir = roms_root / "GBA"
    images_dir = platform_dir / "Imgs"
    images_dir.mkdir(parents=True, exist_ok=True)

    original_rom = platform_dir / "005_Pokemon.gba"
    original_rom.write_bytes(b"OLD")

    original_cover = images_dir / "005_Pokemon.png"
    cover_img = np.full((60, 40, 3), 20, dtype=np.uint8)
    success, data = cv2.imencode(".png", cover_img)
    assert success
    original_cover.write_bytes(data.tobytes())

    staging_root = tmp_path / "games_to_include"
    staged_dir = staging_root / "005_Pokemon"
    staged_dir.mkdir(parents=True, exist_ok=True)

    staged_rom = staged_dir / "005_Pokemon.gba"
    staged_rom.write_bytes(b"NEW")

    staged_cover = staged_dir / "005_Pokemon.png"
    new_cover_img = np.full((90, 90, 3), 220, dtype=np.uint8)
    success, data = cv2.imencode(".png", new_cover_img)
    assert success
    staged_cover.write_bytes(data.tobytes())

    inserted = push_games(
        staging_dir=staging_root,
        roms_root=roms_root,
        interactive=False,
        console=Console(record=True),
    )

    expected_rom = platform_dir / "005_Pokemon.gba"
    expected_cover = images_dir / "005_Pokemon.png"
    assert inserted == [expected_rom]
    assert expected_rom.read_bytes() == b"NEW"
    assert not staged_dir.exists()

    thumbnail = cv2.imread(str(expected_cover), cv2.IMREAD_UNCHANGED)
    assert thumbnail.shape[:2] == (160, 256)
    assert thumbnail[..., :3].mean() > 100
