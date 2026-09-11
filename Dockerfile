# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# System deps needed by Pillow for JPEG/PNG/WEBP handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# IMPORTANT: --extra-index-url pulls CPU-only torch/torchvision wheels.
# Without this line, pip defaults to CUDA-enabled wheels that are several
# GB larger and unnecessary for CPU-only inference.
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

COPY app ./app

# Model weights are NOT copied here by default (see .dockerignore) — mount
# them as a volume, bake them into a second build stage once trained, or
# copy them in manually before building if you want them baked into the image.
# COPY app/ml/weights ./app/ml/weights

EXPOSE 8000

# Render/Railway/Fly all inject $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
