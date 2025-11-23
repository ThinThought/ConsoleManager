"""Utilities for building 256x160 PNG thumbnails centered on a transparent canvas."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

TARGET_WIDTH = 256
TARGET_HEIGHT = 160


def make_thumbnail(input_path: Path, output_path: Path) -> None:
    """Create a 256x160 thumbnail centered on a transparent background."""
    image = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Could not open image: {input_path}")

    src_height, src_width = image.shape[:2]
    if src_height == 0 or src_width == 0:
        raise ValueError(f"Image has invalid dimensions: {input_path}")

    scale = TARGET_HEIGHT / src_height
    resized_width = int(round(src_width * scale))
    resized_height = TARGET_HEIGHT

    if resized_width > TARGET_WIDTH:
        scale = TARGET_WIDTH / src_width
        resized_width = TARGET_WIDTH
        resized_height = int(round(src_height * scale))

    resized = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)

    if resized.ndim == 2:
        resized_rgba = cv2.cvtColor(resized, cv2.COLOR_GRAY2BGRA)
    elif resized.shape[2] == 3:
        resized_rgba = cv2.cvtColor(resized, cv2.COLOR_BGR2BGRA)
    elif resized.shape[2] == 4:
        resized_rgba = resized.copy()
    else:
        raise ValueError(f"Unsupported channel count for image: {input_path}")

    resized_rgba[..., 3] = 255

    canvas = np.zeros((TARGET_HEIGHT, TARGET_WIDTH, 4), dtype=np.uint8)

    x_offset = (TARGET_WIDTH - resized_width) // 2
    y_offset = (TARGET_HEIGHT - resized_height) // 2

    canvas[
        y_offset : y_offset + resized_height,
        x_offset : x_offset + resized_width,
    ] = resized_rgba

    output_path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(output_path), canvas)

    if not success:
        raise RuntimeError(f"Failed to save thumbnail to {output_path}")


def _build_parser() -> "argparse.ArgumentParser":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a 256x160 PNG thumbnail centered on a transparent background."
    )
    parser.add_argument("input_image", type=Path, help="Path to the source image.")
    parser.add_argument("output_image", type=Path, help="Path for the generated PNG thumbnail.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    make_thumbnail(args.input_image, args.output_image)
    print(f"Thumbnail saved to {args.output_image}")


if __name__ == "__main__":
    main()
