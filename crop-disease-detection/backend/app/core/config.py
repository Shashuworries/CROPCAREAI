"""
Central application configuration.

All tunable thresholds and limits live here so they can be adjusted without
touching model or API logic, and can be overridden via environment variables
(e.g. in a .env file or container env) without code changes.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent  # -> backend/app


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- App metadata ---
    APP_NAME: str = "Crop Disease Detection API"
    APP_VERSION: str = "0.1.0"

    # --- CORS ---
    # Comma-separated list of allowed origins; "*" allowed for local dev only.
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
    ]

    # --- Upload validation ---
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

    # --- Inference thresholds ---
    # Below this, the primary classifier's result is not trusted.
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = 0.60
    # Below this cosine similarity score, the fallback match is not trusted either.
    SIMILARITY_CONFIDENCE_THRESHOLD: float = 0.75

    # --- Model paths ---
    MODEL_DIR: Path = BASE_DIR / "ml" / "weights"
    CLASSIFIER_MODEL_PATH: Path = MODEL_DIR / "model.keras"
    CLASS_INDICES_PATH: Path = MODEL_DIR / "class_indices.json"
    REFERENCE_EMBEDDINGS_PATH: Path = MODEL_DIR / "reference_embeddings.npz"

    # --- Data paths ---
    DISEASES_JSON_PATH: Path = BASE_DIR / "data" / "diseases.json"

    # --- Image preprocessing ---
    IMAGE_SIZE: tuple[int, int] = (224, 224)


settings = Settings()
