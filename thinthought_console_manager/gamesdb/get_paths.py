from pathlib import Path
from tqdm import tqdm

def get_paths(target_dir: Path, output: Path):
    with output.open("w", encoding="utf-8") as f:
        for p in tqdm(target_dir.rglob("*"), desc="Generating paths", unit=" paths"):
            resolution = p.resolve()
            f.write(str(resolution) + "\n")