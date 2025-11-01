#!/usr/bin/env python3
"""
Sanitize full ROM tree:
- Extract .zip / .7z
- Clean & rename files: <index>_<GameName>.<ext>
- Delete .zip, .7z, .txt
- Generate roms_list.txt with full paths
"""

import zipfile, py7zr, re
from pathlib import Path
from pathlib import Path
from PIL import Image

ROMS_ROOT = Path("./hot_copy/")
OUTPUT_LIST = Path("roms/roms_list.txt")

# ─────────────────────────────
#  Utilidades
# ─────────────────────────────
def extract_archives(base_dir: Path):
    """Extract all .zip and .7z archives in-place."""
    for path in base_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".zip":
            try:
                print(f"📦 Extracting ZIP → {path}")
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(path.parent)
            except Exception as e:
                print(f"⚠️ Error extracting {path}: {e}")
        elif path.suffix.lower() == ".7z":
            try:
                print(f"📦 Extracting 7Z  → {path}")
                with py7zr.SevenZipFile(path, "r") as zf:
                    zf.extractall(path.parent)
            except Exception as e:
                print(f"⚠️ Error extracting {path}: {e}")

def clean_filename(name: str) -> str:
    """Remove parentheses, brackets and symbols."""
    name = re.sub(r"[\(\[].*?[\)\]]", "", name)
    name = re.sub(r"[^A-Za-z0-9_\- ]", "", name)
    name = name.strip().replace(" ", "_")
    return name

def rename_with_index(base_dir: Path):
    """Rename all ROM files using alphabetical index per console."""
    for console_dir in sorted(base_dir.iterdir()):
        if not console_dir.is_dir():
            continue
        print(f"\n🎮 Processing {console_dir.name}")
        files = [f for f in console_dir.rglob("*") if f.is_file() and f.parent.name != "Imgs"]
        files.sort(key=lambda x: x.name.lower())
        for idx, file in enumerate(files, start=1):
            clean_name = clean_filename(file.stem)
            new_name = f"{idx:03d}_{clean_name}{file.suffix}"
            if file.name != new_name:
                try:
                    new_path = file.with_name(new_name)
                    file.rename(new_path)
                    print(f"🔤 {file.name} → {new_name}")
                except Exception as e:
                    print(f"⚠️ Rename error {file}: {e}")

def delete_unwanted_files(base_dir: Path):
    """Delete all .zip, .7z and .txt files."""
    for ext in [".zip", ".7z", ".txt"]:
        for f in base_dir.rglob(f"*{ext}"):
            try:
                print(f"🗑️ Deleting {f}")
                f.unlink()
            except Exception as e:
                print(f"⚠️ Delete error {f}: {e}")

def list_full_paths(base_dir: Path, output_file: Path):
    """Generate full path list."""
    with output_file.open("w", encoding="utf-8") as f:
        for p in base_dir.rglob("*"):
            if p.is_file():
                f.write(str(p.resolve()) + "\n")
    print(f"\n🗒️  File list saved to {output_file}")


def sanitize_imgs(base_dir: Path):
    """Convert all .jpg/.jpeg images in base_dir to 240x160 .png keeping same basename and delete original."""
    for ext in [".jpg", ".jpeg"]:
        for f in base_dir.rglob(f"*{ext}"):
            img = Image.open(f).convert("RGB")
            img = img.resize((240, 160))
            out_path = f.with_suffix(".png")
            img.save(out_path, "PNG")
            f.unlink()  # delete original
            print(f"✅ {f.name} → {out_path.name} (deleted original)")


# ─────────────────────────────
#  Ejecución principal
# ─────────────────────────────
def main():
    if not ROMS_ROOT.exists():
        print(f"❌ Root directory not found: {ROMS_ROOT}")
        return
    print("🚀 Starting ROM tree sanitation (final cleanup)...\n")

    sanitize_imgs(ROMS_ROOT)

    print("\n✅ ROM tree sanitized successfully.")

if __name__ == "__main__":
    main()
