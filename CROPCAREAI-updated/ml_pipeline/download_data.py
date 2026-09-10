"""
Dataset acquisition helper.

This script does NOT fabricate or auto-download PlantVillage for you silently
(Kaggle requires an account/API key and accepting terms) — it walks you
through it and then verifies + reports what you have.

Usage:
    1. Download the "PlantVillage" dataset (15-class color subset) from
       Kaggle: https://www.kaggle.com/datasets/emmarex/plantdisease
       Either download it manually from the site, or via the Kaggle CLI:
           pip install kaggle
           kaggle datasets download -d emmarex/plantdisease
           unzip plantdisease.zip -d plantvillage_raw
    2. Find the folder that directly contains the 15 class subfolders (it's
       usually nested one level deep, e.g. plantvillage_raw/PlantVillage/).
       You should see folder names exactly like "Tomato_healthy",
       "Potato___Early_blight", "Pepper__bell___Bacterial_spot", etc. —
       this specific Kaggle mirror mixes single and triple underscores
       inconsistently between crops, which is normal, not a corrupted
       download.
    3. Run:
           python download_data.py --source /path/to/PlantVillage
       This re-organizes/renames folders to match our diseases.json keys
       (see CLASS_KEY_MAP below) and copies them into ./dataset/raw/.

Do NOT skip step 3's mapping step — training on the raw Kaggle folder names
directly will produce a model whose class_indices.json won't match the keys
used in backend/app/data/diseases.json, and every prediction will fail the
disease lookup at inference time.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Maps the emmarex/plantdisease Kaggle dataset's raw folder naming (15
# classes total) -> our diseases.json class keys. This is the dataset's
# ACTUAL folder naming — note it is NOT consistent (some crops use triple
# underscores, Tomato mostly uses single/double) because that's how the
# original PlantVillage authors named them. If your extracted copy has
# slightly different folder names, adjust the left-hand side below to match
# — run this script once, check the "Skipped" list it prints, and fix any
# mismatches there rather than guessing.
CLASS_KEY_MAP = {
    # --- Pepper (bell) ---
    "Pepper__bell___Bacterial_spot": "pepper_bell_bacterial_spot",
    "Pepper__bell___healthy": "pepper_bell_healthy",
    # --- Potato ---
    "Potato___Early_blight": "potato_early_blight",
    "Potato___Late_blight": "potato_late_blight",
    "Potato___healthy": "potato_healthy",
    # --- Tomato (10 classes) ---
    "Tomato_Bacterial_spot": "tomato_bacterial_spot",
    "Tomato_Early_blight": "tomato_early_blight",
    "Tomato_Late_blight": "tomato_late_blight",
    "Tomato_Leaf_Mold": "tomato_leaf_mold",
    "Tomato_Septoria_leaf_spot": "tomato_septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "tomato_spider_mites_two_spotted_spider_mite",
    "Tomato__Target_Spot": "tomato_target_spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "tomato_yellow_leaf_curl_virus",
    "Tomato__Tomato_mosaic_virus": "tomato_mosaic_virus",
    "Tomato_healthy": "tomato_healthy",
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
