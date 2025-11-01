#!/usr/bin/env python3
"""
Crea un directorio 'datasets/' con un CSV por cada subcarpeta del árbol.
Cada CSV contiene:
fullpath, name, extension, parent, size_bytes, is_dir
"""

from pathlib import Path
import csv

ROOT_DIR = Path("../roms")     # directorio raíz del tree
DATASETS_DIR = Path("../datasets")  # salida

def collect_info(path: Path):
    """Extrae metadatos de un path."""
    try:
        stat = path.stat()
        return {
            "fullpath": str(path.resolve()),
            "name": path.name,
            "extension": path.suffix.lower(),
            "parent": str(path.parent),
            "size_bytes": stat.st_size if path.is_file() else 0,
            "is_dir": int(path.is_dir())
        }
    except Exception as e:
        print(f"⚠️ Error leyendo {path}: {e}")
        return None

def export_dataset(subdir: Path):
    """Crea un CSV con todos los elementos del subdirectorio."""
    dataset_path = DATASETS_DIR / f"{subdir.name}.csv"
    rows = []
    for p in subdir.rglob("*"):
        info = collect_info(p)
        if info:
            rows.append(info)

    if rows:
        with dataset_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"🧾 Dataset generado: {dataset_path}")
    else:
        print(f"⚠️ Sin datos en {subdir}")

def main():
    if not ROOT_DIR.exists():
        print(f"❌ No existe el directorio raíz: {ROOT_DIR}")
        return

    DATASETS_DIR.mkdir(exist_ok=True)
    print(f"🚀 Generando datasets en {DATASETS_DIR}...\n")

    for subdir in sorted(ROOT_DIR.iterdir()):
        if subdir.is_dir():
            export_dataset(subdir)

    print("\n✅ Datasets creados correctamente.")

if __name__ == "__main__":
    main()
