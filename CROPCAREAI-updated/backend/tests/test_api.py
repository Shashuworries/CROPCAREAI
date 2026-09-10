"""
API test suite.

Covers: /health, valid image upload, invalid file type, oversized file,
corrupt image, the model-not-loaded/standby path, and the disease lookup
service directly (low-confidence path + successful enrichment path).

Since no trained weights exist in this environment yet, both the classifier
and similarity model will be in standby mode — the "standby" and "low
confidence" tests reflect real, current behavior rather than mocked
behavior. Once you train the classifier and build reference embeddings,
add a second test class that mocks HybridPredictor.predict() to exercise
the "classifier" and "similarity_fallback" method_used paths explicitly.
"""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.ml.hybrid_predictor import HybridResult
from app.services.disease_service import build_response

client = TestClient(app)


def make_test_jpeg(size=(64, 64), color=(34, 139, 34)) -> bytes:
    """Produces a tiny in-memory valid JPEG for upload tests."""
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="JPEG")
    return buf.getvalue()


class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "classifier_loaded" in body
        assert "similarity_model_loaded" in body


class TestPredictValidation:
    def test_valid_image_is_accepted_and_processed(self):
        jpeg_bytes = make_test_jpeg()
        response = client.post(
            "/predict",
            files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
        )
        # No weights are loaded in this environment, so we expect a clean
        # "standby" response, NOT an error — this proves the upload itself
        # passed validation and reached the inference layer.
        assert response.status_code == 200
        body = response.json()
        assert body["method_used"] == "low_confidence"
        assert "standby" in body["message"].lower() or "low confidence" in body["message"].lower()

    def test_invalid_extension_is_rejected(self):
        response = client.post(
            "/predict",
            files={"file": ("leaf.txt", b"not an image", "text/plain")},
        )
        assert response.status_code == 400
        assert "extension" in response.json()["detail"].lower() or \
               "content type" in response.json()["detail"].lower()

    def test_oversized_file_is_rejected(self):
        # 11 MB of dummy bytes, disguised with a valid-looking name/type but
        # will fail the size check before PIL even opens it.
        oversized = b"\x00" * (11 * 1024 * 1024)
        response = client.post(
            "/predict",
            files={"file": ("leaf.jpg", oversized, "image/jpeg")},
        )
        assert response.status_code == 400
        assert "large" in response.json()["detail"].lower()

    def test_corrupt_image_is_rejected(self):
        # Valid extension/MIME claim, but garbage bytes that aren't a real image.
        corrupt_bytes = b"\xff\xd8\xff\xe0" + b"garbage_not_a_real_jpeg" * 20
        response = client.post(
            "/predict",
            files={"file": ("leaf.jpg", corrupt_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        assert "corrupt" in response.json()["detail"].lower() or \
               "not a valid" in response.json()["detail"].lower()

    def test_empty_file_is_rejected(self):
        response = client.post(
            "/predict",
            files={"file": ("leaf.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400


class TestStandbyMode:
    def test_predict_reports_standby_when_no_models_loaded(self):
        """
        With no model.keras and no reference_embeddings.npz on disk (the
        default state of a fresh clone before ml_pipeline scripts are run),
        /predict must clearly report standby rather than fabricate a result.
        """
        jpeg_bytes = make_test_jpeg()
        response = client.post(
            "/predict",
            files={"file": ("leaf.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["crop"] is None
        assert body["disease"] is None
        assert body["confidence"] == 0.0


class TestDiseaseService:
    """Exercises disease_service.build_response() directly, independent of the API."""

    def test_low_confidence_result_produces_retake_photo_message(self):
        result: HybridResult = {
            "class_key": None,
            "confidence": 0.0,
            "method_used": "low_confidence",
        }
        response = build_response(result)
        assert response.method_used == "low_confidence"
        assert response.disease is None
        assert "retake" in response.message.lower()

    def test_known_class_key_is_enriched_from_diseases_json(self):
        result: HybridResult = {
            "class_key": "tomato_early_blight",
            "confidence": 0.87,
            "method_used": "classifier",
        }
        response = build_response(result)
        assert response.crop == "Tomato"
        assert response.disease == "Early Blight"
        assert response.method_used == "classifier"
        assert len(response.symptoms) > 0
        assert len(response.treatment.organic) > 0

    def test_similarity_fallback_result_includes_method_note(self):
        result: HybridResult = {
            "class_key": "potato_late_blight",
            "confidence": 0.81,
            "method_used": "similarity_fallback",
        }
        response = build_response(result)
        assert response.method_used == "similarity_fallback"
        assert "reference image comparison" in response.message

    def test_healthy_class_key_returns_empty_treatment_lists(self):
        result: HybridResult = {
            "class_key": "tomato_healthy",
            "confidence": 0.95,
            "method_used": "classifier",
        }
        response = build_response(result)
        assert response.disease == "Healthy"
        assert response.severity == "None"
        assert response.treatment.organic == []
        assert response.treatment.chemical == []

    def test_unknown_class_key_returns_safe_error_message(self):
        result: HybridResult = {
            "class_key": "some_disease_not_in_json",
            "confidence": 0.90,
            "method_used": "classifier",
        }
        response = build_response(result)
        assert response.crop is None
        assert "mismatch" in response.message.lower()
