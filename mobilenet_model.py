"""
Primary predictor: a MobileNetV3Small classifier trained via transfer learning.

This module never fabricates a result. If backend/app/ml/weights/model.keras
does not exist on disk (e.g. because ml_pipeline/train_mobilenet.py hasn't
been run yet), `is_loaded` stays False and predict() raises ModelNotLoadedError,
which the orchestrator (hybrid_predictor.py) catches to fall through to the
similarity-search backup instead of crashing the request.
"""
from __future__ import annotations

import json
import logging

import numpy as np

from app.core.config import settings
from app.ml.base import BasePredictor, RawPrediction
from app.ml.preprocessor import bytes_to_pil, to_keras_array

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    """Raised when predict() is called but no trained weights are available."""


class MobileNetPredictor(BasePredictor):
    def __init__(self) -> None:
        self.is_loaded = False
        self._model = None
        self._class_names: list[str] = []
        self._load()

    def _load(self) -> None:
        model_path = settings.CLASSIFIER_MODEL_PATH
        class_indices_path = settings.CLASS_INDICES_PATH

        if not model_path.exists():
            logger.warning(
                "Classifier weights not found at %s — classifier running in "
                "standby mode. Run ml_pipeline/train_mobilenet.py to produce it.",
                model_path,
            )
            return

        if not class_indices_path.exists():
            logger.warning(
                "class_indices.json not found at %s — cannot map classifier "
                "output indices to disease keys. Classifier staying in standby.",
                class_indices_path,
            )
            return

        try:
            # Imported lazily so the whole API doesn't fail to start if
            # TensorFlow isn't installed yet in a given dev environment.
            import tensorflow as tf

            self._model = tf.keras.models.load_model(model_path)

            with open(class_indices_path, "r", encoding="utf-8") as f:
                # Expected format: {"0": "tomato_early_blight", "1": "healthy", ...}
                index_map = json.load(f)
            # Sort by integer index so list position == model output index.
            self._class_names = [index_map[str(i)] for i in range(len(index_map))]

            self.is_loaded = True
            logger.info("MobileNetV3Small classifier loaded (%d classes).", len(self._class_names))
        except Exception:
            logger.exception("Failed to load classifier — staying in standby mode.")
            self._model = None
            self.is_loaded = False

    def predict(self, image_bytes: bytes) -> RawPrediction:
        if not self.is_loaded or self._model is None:
            raise ModelNotLoadedError(
                "Classifier weights are not loaded. Train the model via "
                "ml_pipeline/train_mobilenet.py first."
            )

        img = bytes_to_pil(image_bytes)
        batch = to_keras_array(img)

        predictions = self._model.predict(batch, verbose=0)[0]
        top_idx = int(np.argmax(predictions))
        confidence = float(predictions[top_idx])

        class_key = self._class_names[top_idx]

        return RawPrediction(
            class_key=class_key,
            confidence=confidence,
            raw_label=class_key,
        )
