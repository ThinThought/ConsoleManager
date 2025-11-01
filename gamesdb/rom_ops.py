#!/usr/bin/env python3
import argparse
import zipfile, py7zr, re
from pathlib import Path

# ─────────────────────────────
#  1. Descompresión .zip / .7z
# ─────────────────────────────
def extract_archives(base_dir: Path):
    for path in base_dir.rglob("*"):
        if path.suffix == ".zip":
            print(f"📦 Extracting ZIP: {path}")
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(path.parent)
        elif path.suffix == ".7z":
            print(f"📦 Extracting 7Z:  {path}")
            with py7zr.SevenZipFile(path, "r") as zf:
                zf.extractall(path.parent)

# ─────────────────────────────
#  2. Renombrado por regex
# ─────────────────────────────
def rename_files(base_dir: Path, prefix: str):
    pattern = re.compile(r"[\(\[].*?[\)\]]")  # quita ( ) y [ ]
    for file in base_dir.rglob("*"):
        if file.is_file():
            clean_name = pattern.sub("", file.stem)
            clean_name = re.sub(r"[^A-Za-z0-9_\- ]", "", clean_name).strip().replace(" ", "_")
            new_name = f"{prefix}_{clean_name}{file.suffix}"
            if file.name != new_name:
                new_path = file.with_name(new_name)
                print(f"🔤 {file.name} → {new_name}")
                file.rename(new_path)

# ─────────────────────────────
#  3. Listar full paths
# ─────────────────────────────
def list_full_paths(base_dir: Path):
    for p in base_dir.rglob("*"):
        if p.is_file():
            print(p.resolve())

# ─────────────────────────────
#  CLI
# ─────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ROM Tree Operations Tool")
    parser.add_argument("operation", choices=["extract", "rename", "list"])
    parser.add_argument("--path", default="roms/Roms", help="Root ROM directory")
    parser.add_argument("--prefix", help="Prefix for rename (e.g. GBA, N64)")
    args = parser.parse_args()

    base_dir = Path(args.path)
    if not base_dir.exists():
        raise SystemExit(f"❌ Directory not found: {base_dir}")

    if args.operation == "extract":
        extract_archives(base_dir)
    elif args.operation == "rename":
        if not args.prefix:
            raise SystemExit("❌ Missing --prefix for rename operation")
        rename_files(base_dir, args.prefix)
    elif args.operation == "list":
        list_full_paths(base_dir)

if __name__ == "__main__":
    main()
