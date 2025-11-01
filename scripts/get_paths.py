from pathlib import Path

root = Path("../roms")
output = Path("../roms_paths.txt")

with output.open("w", encoding="utf-8") as f:
    for p in root.rglob("*"):
        resolution = p.resolve()
        print(resolution)
        f.write(str(resolution) + "\n")

print(f"✅ Full path tree saved to {output}")
