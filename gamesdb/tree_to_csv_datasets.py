#!/usr/bin/env python3
"""
Crea un directorio 'datasets/' con un CSV por cada subcarpeta del árbol.
Cada CSV contiene:
fullpath, name, extension, parent, size_bytes, is_dir
"""

from pathlib import Path
import csv

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

def export_dataset(dataset_dir, subdir: Path):
    """Crea un CSV con todos los elementos del subdirectorio."""
    dataset_path = dataset_dir / f"{subdir.name}.csv"
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
    else:
        print(f"⚠️ Sin datos en {subdir}")