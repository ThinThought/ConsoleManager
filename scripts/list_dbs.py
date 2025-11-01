#!/usr/bin/env python3
"""
Genera un índice global de todos los datasets en ./datasets/
Salida: list_dbs.csv con columnas [dataset, rom_name]
"""

import csv
from pathlib import Path

DATASETS_DIR = Path("../datasets")
OUTPUT_FILE = DATASETS_DIR / "list_dbs.csv"

def generate_index():
    rows = []
    for csv_file in sorted(DATASETS_DIR.glob("*.csv")):
        dataset_name = csv_file.stem
        with csv_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["is_dir"]) == 0:  # solo archivos
                    rom_name = row["name"]
                    rows.append({"dataset": dataset_name, "rom_name": rom_name})

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "rom_name"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Índice global generado en {OUTPUT_FILE}")

def main():
    if not DATASETS_DIR.exists():
        print(f"❌ No existe el directorio {DATASETS_DIR}")
        return
    generate_index()

if __name__ == "__main__":
    main()
