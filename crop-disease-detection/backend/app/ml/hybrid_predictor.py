"""
Hybrid inference orchestration.

Decision flow:
  1. If the classifier is loaded, run it. If its confidence clears
     CLASSIFIER_CONFIDENCE_THRESHOLD, use its result.
  2. Otherwise (classifier not loaded, or not confident), try the
     similarity fallback if it's loaded. If its best match clears
     SIMILARITY_CONFIDENCE_THRESHOLD, use that result instead.
  3. If neither produced a confident result, return a low_confidence
     outcome. The system never guesses past this point.

This is the ONLY module the API layer should import ML logic from.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal, Optional, TypedDict

from app.core.config import settings
from app.ml.base import RawPrediction
from app.ml.mobilenet_model import MobileNetPredictor, ModelNotLoadedError
from app.ml.similarity_model import SimilarityModelNotLoadedError, SimilarityPredictor

logger = logging.getLogger(__name__)

MethodUsed = Literal["classifier", "similarity_fallback", "low_confidence"]


class HybridResult(TypedDict):
    class_key: Optional[str]
    confidence: float
    method_used: MethodUsed


class HybridPredictor:
    """
    Owns both underlying predictors as singletons (loaded once at process
    startup) and orchestrates the classifier -> fallback -> low-confidence
    decision chain on each request.
    """

    def __init__(self) -> None:
        self.classifier = MobileNetPredictor()
        self.similarity = SimilarityPredictor()

    @property
    def classifier_loaded(self) -> bool:
        return self.classifier.is_loaded

    @property
    def similarity_loaded(self) -> bool:
        return self.similarity.is_loaded

    def predict(self, image_bytes: bytes) -> HybridResult:
        classifier_result = self._try_classifier(image_bytes)
        if classifier_result is not None:
            return {
                "class_key": classifier_result["class_key"],
                "confidence": classifier_result["confidence"],
                "method_used": "classifier",
            }

        similarity_result = self._try_similarity(image_bytes)
        if similarity_result is not None:
            return {
                "class_key": similarity_result["class_key"],
                "confidence": similarity_result["confidence"],
                "method_used": "similarity_fallback",
            }

        return {
            "class_key": None,
            "confidence": 0.0,
            "method_used": "low_confidence",
        }

    def _try_classifier(self, image_bytes: bytes) -> Optional[RawPrediction]:
        if not self.classifier.is_loaded:
            return None
        try:
            result = self.classifier.predict(image_bytes)
        except ModelNotLoadedError:
            return None
        except Exception:
            logger.exception("Classifier inference failed unexpectedly.")
            return None

        if result["confidence"] >= settings.CLASSIFIER_CONFIDENCE_THRESHOLD:
            return result

        logger.info(
            "Classifier confidence %.3f below threshold %.2f — falling back.",
            result["confidence"],
            settings.CLASSIFIER_CONFIDENCE_THRESHOLD,
        )
        return None

    def _try_similarity(self, image_bytes: bytes) -> Optional[RawPrediction]:
        if not self.similarity.is_loaded:
            return None
        try:
            result = self.similarity.predict(image_bytes)
        except SimilarityModelNotLoadedError:
            return None
        except Exception:
            logger.exception("Similarity inference failed unexpectedly.")
            return None

        if result["confidence"] >= settings.SIMILARITY_CONFIDENCE_THRESHOLD:
            return result

        logger.info(
            "Similarity best match %.3f below threshold %.2f — no confident result.",
            result["confidence"],
            settings.SIMILARITY_CONFIDENCE_THRESHOLD,
        )
        return None


@lru_cache(maxsize=1)
def get_hybrid_predictor() -> HybridPredictor:
    """
    Returns the process-wide HybridPredictor singleton, constructing (and
    therefore loading both underlying models) on first call. FastAPI's
    startup event calls this once explicitly so model loading happens at
    server boot, not on the first incoming request.
    """
    return HybridPredictor()
