"""
Shared image preprocessing utilities.

Both the MobileNetV3Small classifier and the ResNet50 similarity fallback
need a 224x224 RGB image, but each framework (TF vs. PyTorch) wants a
different tensor format, so this module provides a common PIL-level entry
point plus framework-specific conversion helpers.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

from app.core.config import settings


def bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Decode raw bytes into a PIL Image, forced to RGB (drops alpha/palette issues)."""
    img = Image.open(io.BytesIO(image_bytes))
    return img.convert("RGB")


def pil_to_resized(img: Image.Image, size: tuple[int, int] | None = None) -> Image.Image:
    size = size or settings.IMAGE_SIZE
    return img.resize(size, Image.BILINEAR)


def to_keras_array(img: Image.Image) -> np.ndarray:
    """
    Produces a (1, H, W, 3) float32 array scaled to [0, 1], the format
    Keras' ImageDataGenerator-trained models expect at inference time.
    """
    resized = pil_to_resized(img)
    arr = np.array(resized, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)
