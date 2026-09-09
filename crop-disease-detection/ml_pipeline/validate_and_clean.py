"""
Dataset validation and cleaning.

Run this AFTER download_data.py and BEFORE train_mobilenet.py. It:
  1. Detects and removes corrupt/unreadable images.
  2. Detects and removes exact duplicates (MD5) and near-duplicates
     (perceptual hash, if `imagehash` is installed — optional).
  3. Prints a class-balance report so you know if any class is badly
     underrepresented before you start training.

Usage:
    python validate_and_clean.py --dataset dataset/raw --output dataset/clean
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def is_valid_image(path: Path) -> bool:
    try:
        img = Image.open(path)
        img.verify()
        img2 = Image.open(path)
        img2.load()
        return True
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        return False


def clean_class_folder(class_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "corrupt": 0, "exact_dupes": 0, "near_dupes": 0, "kept": 0}
    seen_md5: set[str] = set()
    seen_phash: dict = {}

    images = [p for p in class_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    stats["total"] = len(images)

    for img_path in images:
        if not is_valid_image(img_path):
            stats["corrupt"] += 1
            continue

        h = md5_of(img_path)
        if h in seen_md5:
            stats["exact_dupes"] += 1
            continue
        seen_md5.add(h)

        if HAS_IMAGEHASH:
            try:
                phash = imagehash.phash(Image.open(img_path))
                # Treat hashes within distance 3 as near-duplicates.
                is_near_dupe = any(phash - existing <= 3 for existing in seen_phash)
                if is_near_dupe:
                    stats["near_dupes"] += 1
                    continue
                seen_phash[phash] = img_path
            except Exception:
                pass  # if phash fails for any reason, don't block on it

        shutil.copy2(img_path, out_dir / img_path.name)
        stats["kept"] += 1

    return stats


def main(dataset_dir: Path, output_dir: Path) -> None:
    if not HAS_IMAGEHASH:
        print(
            "Note: 'imagehash' not installed — skipping near-duplicate detection. "
            "Install with `pip install imagehash` for that check.\n"
        )

    report = {}
    for class_dir in sorted(dataset_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        out_dir = output_dir / class_dir.name
        report[class_dir.name] = clean_class_folder(class_dir, out_dir)

    print("--- Class balance / cleaning report ---")
    kept_counts = []
    for class_name, stats in report.items():
        print(
            f"{class_name:30s} total={stats['total']:4d}  "
            f"corrupt={stats['corrupt']:3d}  exact_dupes={stats['exact_dupes']:3d}  "
            f"near_dupes={stats['near_dupes']:3d}  kept={stats['kept']:4d}"
        )
        kept_counts.append(stats["kept"])

    if kept_counts:
        min_c, max_c = min(kept_counts), max(kept_counts)
        if min_c > 0 and max_c / min_c > 3:
            print(
                f"\nWARNING: class imbalance detected (largest class is "
                f"{max_c / min_c:.1f}x the smallest). Consider class weighting "
                f"or augmenting the smaller classes before training."
            )
        elif min_c == 0:
            print("\nWARNING: at least one class has zero usable images after cleaning.")

    print(f"\nClean dataset written to: {output_dir.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=Path("dataset/raw"), type=Path)
    parser.add_argument("--output", default=Path("dataset/clean"), type=Path)
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset path does not exist: {args.dataset}")

    main(args.dataset, args.output)
