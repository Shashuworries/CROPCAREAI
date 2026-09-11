"""
Fallback predictor: ResNet50 feature extraction + cosine similarity.

This is the safety net used when the primary classifier either isn't loaded
or isn't confident. It extracts a feature embedding from the input image
using a frozen, ImageNet-pretrained ResNet50 (final classification layer
removed) and compares it via cosine similarity against a small set of
reference embeddings built ahead of time by
ml_pipeline/build_reference_embeddings.py.

This mirrors the approach already validated in the project report (ResNet50
feature extraction + sklearn cosine_similarity), just wrapped behind the
same BasePredictor interface as the classifier so the orchestrator doesn't
need to know which model answered.
"""
from __future__ import annotations

import logging

import numpy as np

from app.core.config import settings
from app.ml.base import BasePredictor, RawPrediction
from app.ml.preprocessor import bytes_to_pil

logger = logging.getLogger(__name__)


class SimilarityModelNotLoadedError(RuntimeError):
    """Raised when predict() is called but reference embeddings aren't available."""


class SimilarityPredictor(BasePredictor):
    def __init__(self) -> None:
        self.is_loaded = False
        self._feature_extractor = None
        self._transform = None
        self._device = None
        self._reference_embeddings: np.ndarray | None = None
        self._reference_labels: list[str] = []
        self._load()

    def _load(self) -> None:
        embeddings_path = settings.REFERENCE_EMBEDDINGS_PATH

        if not embeddings_path.exists():
            logger.warning(
                "Reference embeddings not found at %s — similarity fallback "
                "running in standby mode. Run "
                "ml_pipeline/build_reference_embeddings.py to produce it.",
                embeddings_path,
            )
            return

        try:
            # Imported lazily so the API can still start if torch isn't
            # installed yet in a given dev environment.
            import torch
            import torch.nn as nn
            from torchvision import models, transforms

            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
            resnet.fc = nn.Identity()  # strip final classification layer -> raw features
            resnet.eval()
            self._feature_extractor = resnet.to(self._device)

            self._transform = transforms.Compose(
                [
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

            data = np.load(embeddings_path, allow_pickle=True)
            self._reference_embeddings = data["embeddings"]  # shape (N, 2048)
            self._reference_labels = list(data["labels"])  # length N, disease keys

            self.is_loaded = True
            logger.info(
                "Similarity fallback loaded (%d reference embeddings).",
                len(self._reference_labels),
            )
        except Exception:
            logger.exception("Failed to load similarity model — staying in standby mode.")
            self._feature_extractor = None
            self.is_loaded = False

    def _extract_features(self, image_bytes: bytes) -> np.ndarray:
        import torch

        img = bytes_to_pil(image_bytes)
        tensor = self._transform(img).unsqueeze(0).to(self._device)

        with torch.no_grad():
            features = self._feature_extractor(tensor)

        return features.cpu().numpy()  # shape (1, 2048)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        from sklearn.metrics.pairwise import cosine_similarity

        return cosine_similarity(a, b)[0]  # shape (N,)

    def predict(self, image_bytes: bytes) -> RawPrediction:
        if not self.is_loaded or self._reference_embeddings is None:
            raise SimilarityModelNotLoadedError(
                "Reference embeddings are not loaded. Run "
                "ml_pipeline/build_reference_embeddings.py first."
            )

        query_features = self._extract_features(image_bytes)
        similarities = self._cosine_similarity(query_features, self._reference_embeddings)

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])
        class_key = self._reference_labels[best_idx]

        return RawPrediction(
            class_key=class_key,
            confidence=best_score,
            raw_label=f"similarity_match:{class_key}",
        )
