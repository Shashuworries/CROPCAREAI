import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.security import UploadValidationError, validate_upload
from app.ml.hybrid_predictor import HybridPredictor, get_hybrid_predictor
from app.schemas.prediction import PredictionResponse
from app.services.disease_service import DiseaseLookupError, build_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    predictor: HybridPredictor = Depends(get_hybrid_predictor),
) -> PredictionResponse:
    # --- Validation ---
    try:
        validated = await validate_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # --- Standby check: be explicit, never fake a result ---
    if not predictor.classifier_loaded and not predictor.similarity_loaded:
        return PredictionResponse(
            confidence=0.0,
            method_used="low_confidence",
            message=(
                "ML engine is in standby mode — no trained model or reference "
                "embeddings are loaded yet. Train the classifier "
                "(ml_pipeline/train_mobilenet.py) or build reference embeddings "
                "(ml_pipeline/build_reference_embeddings.py) to activate inference."
            ),
        )

    # --- Inference ---
    try:
        result = predictor.predict(validated.bytes_data)
    except Exception as exc:
        logger.exception("Unexpected error during inference.")
        raise HTTPException(
            status_code=500, detail="Prediction failed due to an internal error."
        ) from exc

    # --- Enrichment ---
    try:
        return build_response(result)
    except DiseaseLookupError as exc:
        logger.exception("Disease lookup failed.")
        raise HTTPException(
            status_code=500, detail="Server configuration error: disease data unavailable."
        ) from exc
