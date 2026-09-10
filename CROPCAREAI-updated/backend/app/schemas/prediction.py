"""Pydantic schemas for the /predict and /health endpoints."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

MethodUsed = Literal["classifier", "similarity_fallback", "low_confidence"]


class TreatmentInfo(BaseModel):
    organic: list[str] = Field(default_factory=list)
    chemical: list[str] = Field(default_factory=list)


class PredictionResponse(BaseModel):
    crop: Optional[str] = None
    disease: Optional[str] = None
    scientific_name: Optional[str] = None
    severity: Optional[str] = None
    confidence: float
    method_used: MethodUsed
    symptoms: Optional[list[str]] = None
    prevention: Optional[list[str]] = None
    treatment: Optional[TreatmentInfo] = None
    safety_notes: Optional[list[str]] = None
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "crop": "Tomato",
                    "disease": "Early Blight",
                    "scientific_name": "Alternaria solani",
                    "severity": "Moderate",
                    "confidence": 0.87,
                    "method_used": "classifier",
                    "symptoms": ["Dark brown spots with concentric rings on lower leaves"],
                    "prevention": ["Rotate crops for 2-3 years"],
                    "treatment": {
                        "organic": ["Copper-based fungicides"],
                        "chemical": ["Chlorothalonil-based fungicides"],
                    },
                    "safety_notes": ["Follow product label instructions"],
                    "message": "Prediction successful.",
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    status: Literal["ok"]
    classifier_loaded: bool
    similarity_model_loaded: bool
    app_version: str
