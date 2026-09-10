"""
Upload validation and sanitization.

Every image that reaches the ML layer must pass through validate_upload()
first. This rejects oversized files, disallowed extensions/MIME types, and
corrupt or polyglot payloads (files that are technically valid as some other
format, e.g. an HTML/JS file with an image extension).
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation. Message is safe to show to the user."""


@dataclass
class ValidatedImage:
    bytes_data: bytes
    content_type: str
    filename: str


def _check_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file extension '{ext}'. "
            f"Allowed types: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}"
        )


def _check_mime(content_type: str | None) -> None:
    if content_type not in settings.ALLOWED_MIME_TYPES:
        raise UploadValidationError(
            f"Unsupported content type '{content_type}'. "
            f"Allowed types: {', '.join(sorted(settings.ALLOWED_MIME_TYPES))}"
        )


def _check_size(data: bytes) -> None:
    if len(data) == 0:
        raise UploadValidationError("Uploaded file is empty.")
    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise UploadValidationError(f"File too large. Maximum allowed size is {max_mb:.0f}MB.")


def _verify_is_real_image(data: bytes) -> None:
    """
    Defends against polyglot files (e.g. a valid GIF/HTML with a .jpg extension)
    and corrupt image data. PIL.Image.verify() parses the file structure without
    fully decoding pixel data, then we reopen and force a full load to catch
    truncated-data errors that verify() alone can miss.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        # verify() invalidates the file pointer/state; reopen for a real decode check.
        img2 = Image.open(io.BytesIO(data))
        img2.load()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise UploadValidationError(
            "The uploaded file is not a valid or is a corrupted image."
        ) from exc


async def validate_upload(file: UploadFile) -> ValidatedImage:
    """
    Full validation pipeline for an incoming multipart file upload.
    Raises UploadValidationError with a user-safe message on any failure.
    """
    if file.filename is None:
        raise UploadValidationError("No filename provided.")

    _check_extension(file.filename)
    _check_mime(file.content_type)

    data = await file.read()
    _check_size(data)
    _verify_is_real_image(data)

    return ValidatedImage(
        bytes_data=data,
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename,
    )
