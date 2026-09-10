import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.core.config import settings
from app.ml.hybrid_predictor import get_hybrid_predictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Force model loading at server boot rather than on the first request,
    so /health reflects true readiness immediately and the first real
    prediction request isn't slowed down by a cold model load.
    """
    predictor = get_hybrid_predictor()
    logger.info(
        "Startup complete — classifier_loaded=%s, similarity_model_loaded=%s",
        predictor.classifier_loaded,
        predictor.similarity_loaded,
    )
    if not predictor.classifier_loaded and not predictor.similarity_loaded:
        logger.warning(
            "Both models are in standby mode. /predict will report standby "
            "status until at least one model's artifacts are present."
        )
    yield
    logger.info("Shutting down.")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
