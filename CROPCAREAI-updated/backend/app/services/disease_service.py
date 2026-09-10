"""
Disease information service.

Takes the (class_key, confidence, method_used) result out of the ML layer
and enriches it with human-readable disease info from diseases.json, or
builds the appropriate "please retake the photo" response when no confident
prediction was made. This is the only place that touches diseases.json —
neither model module knows this file exists.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.ml.hybrid_predictor import HybridResult
from app.schemas.prediction import PredictionResponse, TreatmentInfo

logger = logging.getLogger(__name__)


class DiseaseLookupError(RuntimeError):
    """Raised if diseases.json is missing or malformed — a real config error, not user error."""


@lru_cache(maxsize=1)
def _load_diseases() -> dict:
    path: Path = settings.DISEASES_JSON_PATH
    if not path.exists():
        raise DiseaseLookupError(f"diseases.json not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_response(result: HybridResult) -> PredictionResponse:
    """Turns a HybridResult into the full API response, including disease enrichment."""
    if result["method_used"] == "low_confidence" or result["class_key"] is None:
        return PredictionResponse(
            crop=None,
            disease=None,
            scientific_name=None,
            severity=None,
            confidence=result["confidence"],
            method_used="low_confidence",
            symptoms=None,
            prevention=None,
            treatment=None,
            safety_notes=None,
            message=(
                "Unable to confidently identify the disease from this image. "
                "Please retake the photo in good, even lighting with the leaf "
                "filling most of the frame, then try again."
            ),
        )

    diseases = _load_diseases()
    entry = diseases.get(result["class_key"])

    if entry is None:
        # The model returned a class_key with no matching diseases.json entry —
        # a real data/config mismatch, not a normal low-confidence case.
        logger.error("No diseases.json entry found for class_key '%s'", result["class_key"])
        return PredictionResponse(
            crop=None,
            disease=None,
            scientific_name=None,
            severity=None,
            confidence=result["confidence"],
            method_used=result["method_used"],
            symptoms=None,
            prevention=None,
            treatment=None,
            safety_notes=None,
            message=(
                "The model produced a result that could not be matched to known "
                "disease information. Please report this — it likely indicates a "
                "mismatch between the model's class list and diseases.json."
            ),
        )

    method_note = ""
    if result["method_used"] == "similarity_fallback":
        method_note = " (matched via reference image comparison, not the primary classifier)"

    return PredictionResponse(
        crop=entry["crop"],
        disease=entry["disease_name"],
        scientific_name=entry.get("scientific_name"),
        severity=entry.get("severity"),
        confidence=result["confidence"],
        method_used=result["method_used"],
        symptoms=entry.get("symptoms", []),
        prevention=entry.get("prevention", []),
        treatment=TreatmentInfo(**entry.get("treatment", {"organic": [], "chemical": []})),
        safety_notes=entry.get("safety_notes", []),
        message=f"Prediction successful{method_note}.",
    )
