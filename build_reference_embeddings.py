"""
Builds the reference embedding set used by the similarity-search fallback
(backend/app/ml/similarity_model.py).

For each class folder in your clean dataset, this extracts ResNet50 features
for a representative sample of images and saves them to a single .npz file
that similarity_model.py loads at startup.

You do NOT need your whole dataset here — a curated set of maybe 10-30 clear,
representative images per class is enough for a similarity-search safety net
(this is a fallback for uncertain cases, not the primary classifier).

Usage:
    python build_reference_embeddings.py --dataset dataset/clean --per-class 20
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

IMAGE_SIZE = (224, 224)
BACKEND_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml" / "weights"

TRANSFORM = transforms.Compose(
    [
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_feature_extractor(device: torch.device) -> nn.Module:
    resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    resnet.fc = nn.Identity()
    resnet.eval()
    return resnet.to(device)


def extract_features(model: nn.Module, image_path: Path, device: torch.device) -> np.ndarray:
    img = Image.open(image_path).convert("RGB")
    tensor = TRANSFORM(img).unsqueeze(0).to(device)
    with torch.no_grad():
        features = model(tensor)
    return features.cpu().numpy()[0]  # shape (2048,)


def main(dataset_dir: Path, per_class: int, seed: int) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = load_feature_extractor(device)

    all_embeddings: list[np.ndarray] = []
    all_labels: list[str] = []

    random.seed(seed)

    for class_dir in sorted(dataset_dir.iterdir()):
        if not class_dir.is_dir():
            continue

        images = [p for p in class_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
        if not images:
            print(f"  {class_dir.name}: no images found, skipping")
            continue

        sample = random.sample(images, min(per_class, len(images)))
        print(f"  {class_dir.name}: embedding {len(sample)} reference images...")

        for img_path in sample:
            try:
                emb = extract_features(model, img_path, device)
                all_embeddings.append(emb)
                all_labels.append(class_dir.name)
            except Exception as exc:
                print(f"    skipped {img_path.name}: {exc}")

    if not all_embeddings:
        raise SystemExit("No embeddings were produced — check your dataset path.")

    embeddings_array = np.vstack(all_embeddings)  # shape (N, 2048)
    labels_array = np.array(all_labels)

    BACKEND_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BACKEND_WEIGHTS_DIR / "reference_embeddings.npz"
    np.savez(output_path, embeddings=embeddings_array, labels=labels_array)

    print(f"\nSaved {len(all_labels)} reference embeddings to: {output_path}")
    print(
        "IMPORTANT: verify every label here exists as a key in "
        "backend/app/data/diseases.json before serving predictions."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=Path("dataset/clean"), type=Path)
    parser.add_argument("--per-class", default=20, type=int)
    parser.add_argument("--seed", default=42, type=int)
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset path does not exist: {args.dataset}")

    main(args.dataset, args.per_class, args.seed)
