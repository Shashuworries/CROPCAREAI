# Crop Disease Detection — Hybrid System

**VIT Bhopal Capstone (DSN4096)** — MobileNetV3Small classifier (primary) +
ResNet50 feature extraction & cosine similarity (fallback for low-confidence
cases), served via FastAPI, with a vanilla HTML/CSS/JS frontend.

This repo is buildable and testable **right now**, before any model is
trained — both models start in "standby mode" and the API reports that
honestly instead of faking a prediction. Train the classifier and build the
reference embeddings whenever your dataset is ready; the API and frontend
don't need any code changes when you do.

```
crop-disease-detection/
├── backend/            FastAPI app — see backend/app/
├── frontend/            Static HTML/CSS/JS — see frontend/public/
├── ml_pipeline/          Dataset prep + training scripts (run independently)
└── README.md            This file
```

---

## 1. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Heads up:** `tensorflow` and `torch` are large installs. If you only
> want to test the API skeleton without them (both models will stay in
> standby mode, which the API handles gracefully), install everything
> except those two lines from requirements.txt first, and add them back
> before training.

Run the test suite:

```bash
cd backend
python -m pytest tests/ -v
```

All 12 tests should pass even before any model is trained — several of them
specifically verify the "standby mode" behavior is honest rather than faked.

Start the dev server:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check it's alive:

```bash
curl http://127.0.0.1:8000/health
```

Interactive API docs (Swagger UI) are auto-generated at
`http://127.0.0.1:8000/docs`.

---

## 2. Frontend setup

No build step — it's plain HTML/CSS/JS. Serve it with any static server:

```bash
cd frontend/public
python3 -m http.server 5500
```

Then open `http://127.0.0.1:5500/index.html` in a browser. The backend's
CORS config in `backend/app/core/config.py` already allows
`http://127.0.0.1:5500` — if you serve from a different port, add it to
`CORS_ORIGINS` there.

The API base URL is set at the top of `frontend/public/js/app.js`:

```js
const API_BASE_URL = "http://127.0.0.1:8000";
```

Change this if your backend runs somewhere else.

---

## 3. Training the classifier (once your dataset is ready)

```bash
cd ml_pipeline

# 1. Organize a downloaded PlantVillage-style dataset into our class keys
python download_data.py --source /path/to/extracted/PlantVillage --output dataset/raw

# 2. Clean it: drop corrupt/duplicate images, check class balance
python validate_and_clean.py --dataset dataset/raw --output dataset/clean

# 3. Train MobileNetV3Small (writes to backend/app/ml/weights/model.keras
#    and class_indices.json automatically)
python train_mobilenet.py --dataset dataset/clean --epochs 30

# 4. Build the ResNet50 reference embeddings for the similarity fallback
#    (writes to backend/app/ml/weights/reference_embeddings.npz)
python build_reference_embeddings.py --dataset dataset/clean --per-class 20
```

Restart the backend after either artifact changes — models are loaded once
at server startup, not per-request.

```bash
curl http://127.0.0.1:8000/health
# classifier_loaded and/or similarity_model_loaded should now be true
```

---

## 4. Adding more diseases

1. Add a new entry to `backend/app/data/diseases.json`, keyed by a snake_case
   class name (e.g. `"wheat_rust"`).
2. Add real, correctly-labeled training images for that class under
   `dataset/raw/wheat_rust/` (or map an existing PlantVillage folder to it
   in `ml_pipeline/download_data.py`'s `CLASS_KEY_MAP`).
3. Re-run the cleaning, training, and embedding-building steps above.
4. Run `python ml_pipeline/export_class_indices.py --dataset dataset/clean`
   to double check every class in your dataset has a matching `diseases.json`
   entry before you retrain.

---

## 5. What "hybrid" actually means here

```
Image → validate → PRIMARY: MobileNetV3Small classifier
                        │
              confidence ≥ 0.60? ──yes──► use this result
                        │no
                        ▼
              FALLBACK: ResNet50 + cosine similarity
                        │
              similarity ≥ 0.75? ──yes──► use this result
                        │no
                        ▼
              "low confidence — please retake the photo"
```

Both thresholds live in `backend/app/core/config.py` — tune them once you
have real held-out validation data, don't leave them at the defaults for
your final report numbers.

---

## 6. Deploying (not required for a local viva demo — see note below)

**Do not deploy the backend to Vercel.** Vercel's Python support runs as
serverless functions with a hard **500MB** bundle cap. TensorFlow + PyTorch +
torchvision blow way past that (often 4-7GB with default CUDA wheels) —
this isn't a config problem to fix, it's the wrong hosting model for this
stack. Split the deployment instead:

**Frontend → GitHub Pages** (via `.github/workflows/deploy-pages.yml`, already in this repo):
1. Push this repo to GitHub (or push these new files to your existing
   `Shashuworries/CROPCAREAI` repo).
2. On GitHub: **Settings → Pages → Build and deployment → Source**, select
   **"GitHub Actions"** (not "Deploy from a branch" — that's almost
   certainly why `shashuworries.github.io/CROPCAREAI/` was timing out:
   nothing was actually configured to publish anything).
3. Push to `main` (or go to the **Actions** tab and run the "Deploy frontend
   to GitHub Pages" workflow manually). It uploads `frontend/public/` as the
   Pages artifact — the workflow exists specifically because your
   `index.html` isn't at the repo root, which is where Pages looks by
   default.
4. Once the workflow finishes (check the Actions tab for a green check),
   `https://shashuworries.github.io/CROPCAREAI/` should serve
   `frontend/public/index.html`.
5. Edit `PRODUCTION_API_URL` near the top of `frontend/public/js/app.js`
   before this is useful — GitHub Pages only hosts the frontend; the
   backend still needs to be deployed separately (see below) and this file
   is how the frontend finds it.

**Frontend → Vercel** (alternative to GitHub Pages — pick one, not both):
1. Import the repo in Vercel, set **Root Directory** to `frontend`.
2. `frontend/vercel.json` is already configured to serve `public/` directly
   — no build command needed.
3. Before deploying, edit `PRODUCTION_API_URL` near the top of
   `frontend/public/js/app.js` to point at your deployed backend URL.

**Backend → Render (or Railway / Fly.io / Cloud Run — anything container-based)**:
1. `backend/Dockerfile` is ready to build. It installs CPU-only PyTorch
   wheels explicitly (`--extra-index-url https://download.pytorch.org/whl/cpu`)
   — the default PyPI `torch`/`torchvision` wheels are CUDA-enabled and
   several GB larger than needed for CPU inference.
2. On Render: New → Blueprint → point at this repo; `render.yaml` at the
   repo root is pre-configured with `dockerfilePath`/`dockerContext`
   pointing at `backend/`.
3. **Read the RAM warning inside `render.yaml` before picking a plan** —
   loading both TensorFlow and PyTorch models at once realistically needs
   1-2GB RAM. Render's free tier (512MB) will very likely crash on startup
   once both `model.keras` and `reference_embeddings.npz` exist. Either pay
   for a bigger instance, or deploy classifier-only (skip building the
   embeddings) to roughly halve memory use.
4. After deploying, copy the Render URL into `PRODUCTION_API_URL` in
   `app.js`, and add the Vercel frontend's URL to `CORS_ORIGINS` in
   `backend/app/core/config.py`.

**Honestly, for a capstone viva, running both locally on the laptop you're
presenting from is the safer choice** — no cold starts, no network
dependency mid-demo, no RAM ceiling. Deploy publicly only if you actually
need a shareable link for something beyond the presentation itself.

---

## 7. Known gaps to close before the final demo

- [ ] No dataset has been trained on yet — `ml_pipeline/train_mobilenet.py`
      needs a real PlantVillage (or similar) download to run against.
- [ ] `diseases.json` currently has 6 entries (5 diseases + healthy) across
      Tomato, Potato, and Rice — extend as your dataset grows.
- [ ] Thresholds (0.60 / 0.75) are reasonable starting points, not tuned —
      revisit once you have validation-set numbers to report honestly.
- [ ] `API_BASE_URL` in `app.js` is hardcoded to localhost — update before
      deploying anywhere else.
