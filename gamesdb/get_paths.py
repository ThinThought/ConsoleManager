from pathlib import Path
from tqdm import tqdm

def get_paths(root: Path, output: Path):
    with output.open("w", encoding="utf-8") as f:
        for p in tqdm(root.rglob("*")):
            resolution = p.resolve()
            f.write(str(resolution) + "\n")
    print(f"✅ Full path tree saved to {output}")
