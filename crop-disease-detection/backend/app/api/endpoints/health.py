from fastapi import APIRouter, Depends

from app.core.config import settings
from app.ml.hybrid_predictor import HybridPredictor, get_hybrid_predictor
from app.schemas.prediction import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(predictor: HybridPredictor = Depends(get_hybrid_predictor)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        classifier_loaded=predictor.classifier_loaded,
        similarity_model_loaded=predictor.similarity_loaded,
        app_version=settings.APP_VERSION,
    )
