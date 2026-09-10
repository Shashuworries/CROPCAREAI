"""
Standalone utility to (re)generate class_indices.json from a dataset
directory's folder names, and validate every class against diseases.json.

train_mobilenet.py already writes class_indices.json as part of training,
so you don't normally need to run this separately — it's here for when you
want to regenerate/verify the mapping without retraining (e.g. after editing
diseases.json, or after manually reordering dataset folders).

Usage:
    python export_class_indices.py --dataset dataset/clean
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BACKEND_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml" / "weights"
DISEASES_JSON_PATH = Path(__file__).resolve().parent.parent / "backend" / "app" / "data" / "diseases.json"


def main(dataset_dir: Path) -> None:
    class_names = sorted(p.name for p in dataset_dir.iterdir() if p.is_dir())
    if not class_names:
        raise SystemExit(f"No class subfolders found under {dataset_dir}")

    index_to_class = {str(i): name for i, name in enumerate(class_names)}

    BACKEND_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BACKEND_WEIGHTS_DIR / "class_indices.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index_to_class, f, indent=2)
    print(f"Wrote {len(class_names)} classes to {output_path}")

    # Cross-check against diseases.json
    if DISEASES_JSON_PATH.exists():
        with open(DISEASES_JSON_PATH, "r", encoding="utf-8") as f:
            diseases = json.load(f)

        missing = [c for c in class_names if c not in diseases]
        if missing:
            print(
                "\nWARNING: these classes have no matching entry in diseases.json "
                "and will fail lookup at inference time:"
            )
            for m in missing:
                print(f"  - {m}")
        else:
            print("\nAll classes have a matching diseases.json entry. Good to go.")
    else:
        print(f"\nNote: diseases.json not found at {DISEASES_JSON_PATH}, skipping cross-check.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset path does not exist: {args.dataset}")

    main(args.dataset)
