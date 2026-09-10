"""
Common predictor interface.

Both the primary classifier and the similarity-search fallback implement
this interface. The API/orchestration layer (hybrid_predictor.py) only ever
talks to this interface, never to TensorFlow or PyTorch directly — this is
what lets either model be swapped, retrained, or temporarily disabled
without touching the FastAPI endpoints.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict


class RawPrediction(TypedDict):
    """The minimal, framework-agnostic result every predictor must return."""
    class_key: str        # matches a key in diseases.json (e.g. "tomato_early_blight")
    confidence: float     # 0.0 - 1.0
    raw_label: str        # whatever label the model itself produced, for debugging/logs


class BasePredictor(ABC):
    """Abstract base for any model that can turn an image into a disease-class guess."""

    #: Set to True by subclasses once their weights/artifacts are actually loaded.
    is_loaded: bool = False

    @abstractmethod
    def predict(self, image_bytes: bytes) -> RawPrediction:
        """
        Run inference on raw image bytes and return a RawPrediction.
        Implementations must NOT raise on a low-confidence result — that's
        a valid outcome, not an error. Only raise for genuine failures
        (e.g. the model truly cannot be loaded/run).
        """
        raise NotImplementedError
