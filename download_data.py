"""
Dataset acquisition helper.

This script does NOT fabricate or auto-download PlantVillage for you silently
(the Kaggle/GitHub mirrors require accepting terms and, in most cases, an API
key) — it walks you through it and then verifies + reports what you have.

Usage:
    1. Manually download the PlantVillage dataset (color images) from either:
       - Kaggle: https://www.kaggle.com/datasets/emmarex/plantdisease
       - Or the original GitHub mirror: https://github.com/spMohanty/PlantVillage-Dataset
    2. Extract it so you have a folder of subfolders named like
       "Tomato___Early_blight", "Potato___Late_blight", etc.
    3. Run:  python download_data.py --source /path/to/extracted/PlantVillage
       This will re-organize/rename folders to match our diseases.json keys
       (see CLASS_KEY_MAP below) and copy them into ./dataset/raw/.

Do NOT skip step 3's mapping step — training on raw PlantVillage folder names
directly will produce a model whose class_indices.json won't match the keys
used in backend/app/data/diseases.json.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Maps PlantVillage's raw folder naming -> our diseases.json class keys.
# Extend this as you add more crops/diseases to diseases.json.
CLASS_KEY_MAP = {
    "Tomato___Early_blight": "tomato_early_blight",
    "Tomato___Late_blight": "tomato_late_blight",
    "Potato___Early_blight": "potato_early_blight",
    "Potato___Late_blight": "potato_late_blight",
    # PlantVillage's rice/blast data isn't in the original set — if you add a
    # separate rice blast dataset, map its folder name here, e.g.:
    # "Rice___Leaf_blast": "rice_leaf_blast",
    "Tomato___healthy": "healthy",
    "Potato___healthy": "healthy",
}


def organize(source: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    found, skipped = [], []

    for child in sorted(source.iterdir()):
        if not child.is_dir():
            continue
        mapped_key = CLASS_KEY_MAP.get(child.name)
        if mapped_key is None:
            skipped.append(child.name)
            continue

        dest_dir = output / mapped_key
        dest_dir.mkdir(parents=True, exist_ok=True)

        images = [
            p for p in child.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]
        for img_path in images:
            shutil.copy2(img_path, dest_dir / f"{child.name}_{img_path.name}")

        found.append((mapped_key, len(images)))

    print("\n--- Organized classes ---")
    for key, count in found:
        print(f"  {key}: {count} images")

    if skipped:
        print("\n--- Skipped (no mapping in CLASS_KEY_MAP) ---")
        for name in skipped:
            print(f"  {name}  <-- add this to CLASS_KEY_MAP if you want it included")

    print(f"\nOutput written to: {output.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", required=True, type=Path,
        help="Path to the extracted PlantVillage folder (containing per-class subfolders)",
    )
    parser.add_argument(
        "--output", default=Path("dataset/raw"), type=Path,
        help="Where to write the re-organized dataset (default: ./dataset/raw)",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source path does not exist: {args.source}")

    organize(args.source, args.output)
