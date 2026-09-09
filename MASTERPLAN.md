# 🧭 MASTERPLAN.md
## Crop Disease Detection — Master Build Plan

![Edition](https://img.shields.io/badge/edition-Hybrid%20Architecture-1A365D?style=for-the-badge)
![Course](https://img.shields.io/badge/VIT%20Bhopal%20Capstone-DSN4096-2B6CB0?style=for-the-badge)
![Status](https://img.shields.io/badge/status-single%20source%20of%20truth-2F855A?style=for-the-badge)

> **VIT Bhopal Capstone (DSN4096) — Hybrid Architecture Edition**
>
> This is the single source of truth. Your report (ResNet50 + cosine similarity + Gemini) and your other prompts (MobileNetV3Small classifier) are **not actually in conflict** — you're building both, wired together so the weaker one (similarity search) backs up the stronger one (trained classifier). Give this whole file to whichever tool needs context; don't paste both old prompt sets anymore, they'll contradict each other.

---

## 📖 Table of Contents

- [1. The Actual Architecture](#1-the-actual-architecture-what-everyone-should-build-toward)
- [2. Unified Tech Stack](#2-unified-tech-stack)
- [3. GitHub Repository Structure](#3-github-repository-structure)
- [4. Frontend Structure](#4-frontend-structure)
- [5. Minimal Working Code to Unblock Development Immediately](#5-minimal-working-code-to-unblock-development-immediately)
- [6. For Your Presentation Slide on "Design Methodology"](#6-for-your-presentation-slide-on-design-methodology)
- [7. Two-Week Task Order](#7-two-week-task-order-give-this-to-chatgpt-to-refine-per-your-teams-actual-pace)

---

## 1. The Actual Architecture (what everyone should build toward)

```
                         Leaf Image Upload
                                │
                    ┌───────────────────────┐
                    │   Validation Layer     │  (size, MIME, PIL verify)
                    └───────────┬───────────┘
                                │
                    ┌───────────────────────┐
                    │  Preprocess (224x224,  │
                    │  RGB, normalize)        │
                    └───────────┬───────────┘
                                │
                    ┌───────────────────────┐
                    │ PRIMARY: MobileNetV3   │
                    │ Small classifier        │
                    │ (trained on your        │
                    │  labeled dataset)        │
                    └───────────┬───────────┘
                                │
                     confidence >= 0.60?
                        │              │
                       YES             NO
                        │              │
                        │    ┌─────────────────────┐
                        │    │ FALLBACK: ResNet50   │
                        │    │ feature extraction +  │
                        │    │ cosine similarity      │
                        │    │ vs. reference embeddings│
                        │    └───────────┬──────────┘
                        │                │
                        │        best match >= 0.75 similarity?
                        │             │         │
                        │            YES        NO
                        │             │         │
                        └─────┬───────┘   "Low confidence —
                              │            please upload a
                              │            clearer image"
                    ┌───────────────────────┐
                    │  disease_service.py     │
                    │  looks up diseases.json │
                    └───────────┬───────────┘
                                │
                    JSON: crop, disease, confidence,
                    method_used, symptoms, prevention,
                    treatment, safety_notes
                                │
                          Frontend renders
```

**Why this is good for your viva:** you can honestly say "our primary path is a trained classifier; when it's not confident, we fall back to a similarity-search safety net instead of guessing" — that's a legitimate, defensible design decision, not a hack. It also directly reuses the ResNet50+cosine code you already have working from your report (page 31–33 screenshots) instead of throwing it away.

Drop Gemini AI from the live pipeline for the MVP — keep it only as a stretch goal (e.g., generating the natural-language explanation of the result). Don't depend on a paid/rate-limited external API for your core demo path; if Gemini's quota hiccups mid-viva, your whole demo dies. I'd mention this explicitly to your team.

(Back to top)

---

## 2. Unified Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Primary classifier | MobileNetV3Small (TensorFlow/Keras) | Small, fast, fine-tunes well on limited data |
| Fallback matcher | ResNet50 (PyTorch, torchvision) — frozen, feature extraction only | Already coded in your report; no training needed |
| Similarity | scikit-learn `cosine_similarity` | Matches your report exactly |
| Backend | FastAPI + Uvicorn | Async, typed, fast to build |
| Image processing | Pillow, NumPy | Standard |
| Frontend | Vanilla HTML/CSS/JS or React (your call — see §4) | Cursor/v0 both handle either |
| Dataset | PlantVillage (public, pre-labeled) | Don't hand-collect for MVP — use this to start |
| Disease info | `diseases.json` | Keep decoupled from model, as your report's design already implies |

Two frameworks in one repo (TF for classifier, PyTorch for ResNet50) is fine — they don't conflict, just costs a bit more install size. Don't waste time porting the ResNet50 code to TF; it already works.

(Back to top)

---

## 3. GitHub Repository Structure

This reflects the **actual current layout** of [github.com/Shashuworries/CROPCAREAI](https://github.com/Shashuworries/CROPCAREAI) — `crop-disease-detection` and `frontend` sit as two **sibling top-level folders**, not one nested inside the other:

```
CROPCAREAI/
├── crop-disease-detection/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── health.py        # GET /health — model_loaded status for BOTH models
│   │   │   │   │   └── predict.py       # POST /predict
│   │   │   │   └── api_router.py
│   │   │   ├── core/
│   │   │   │   ├── config.py            # thresholds, upload limits, CORS_ORIGINS
│   │   │   │   └── security.py          # upload validation: size, MIME, PIL verify
│   │   │   ├── data/
│   │   │   │   └── diseases.json        # crop, disease, symptoms, prevention, treatment
│   │   │   ├── ml/
│   │   │   │   ├── base.py              # BasePredictor(ABC) — predict(image_bytes) -> dict
│   │   │   │   ├── mobilenet_model.py   # primary classifier, is_loaded flag if weights absent
│   │   │   │   ├── similarity_model.py  # ResNet50 feature extractor + cosine similarity
│   │   │   │   ├── hybrid_predictor.py  # orchestrates: try primary, fall back if low conf
│   │   │   │   ├── preprocessor.py      # shared 224x224 RGB normalization
│   │   │   │   └── weights/             # .keras / .npz artifacts (gitignored)
│   │   │   ├── schemas/
│   │   │   │   └── prediction.py        # pydantic models incl. "method_used"
│   │   │   ├── services/
│   │   │   │   └── disease_service.py   # JSON lookup + low-confidence fallback message
│   │   │   └── main.py                  # FastAPI app, CORS, startup model loading
│   │   ├── tests/
│   │   │   └── test_api.py              # 12 tests — pass even before any model is trained
│   │   └── requirements.txt
│   └── ml_pipeline/
│       ├── download_data.py               # fetch PlantVillage, organize into class folders
│       ├── validate_and_clean.py          # corrupt/dup detection, class balance report
│       ├── build_reference_embeddings.py  # ResNet50 over curated reference set
│       ├── train_mobilenet.py             # transfer learning, EarlyStopping, ModelCheckpoint
│       ├── export_class_indices.py        # saves class_names.json alongside the model
│       └── dataset/                       # raw/ + clean/ (gitignored — never commit images)
├── frontend/
│   └── public/
│       ├── index.html
│       ├── css/
│       └── js/
│           └── app.js               # API_BASE_URL configured here
├── MASTERPLAN.md                    # this file
├── README.md
└── gitignore
```

**Notes on the real layout vs. earlier drafts:**
- `frontend/` lives at the **repo root**, as a sibling of `crop-disease-detection/` — not nested underneath it. Keep any relative paths in scripts/docs consistent with this.
- The `.gitignore` file is currently committed as **`gitignore`** (no leading dot) at the root — rename it to `.gitignore` before it can actually take effect on new commits, otherwise the model-weight and dataset exclusion rules in it are inert.
- `docs/` doesn't exist as a separate folder in the live repo — `MASTERPLAN.md` and `README.md` both sit directly at root. If you want a `docs/` folder later, move both files together and update any relative links between them.

(Back to top)

---

## 4. Frontend Structure

```
frontend/
└── public/
    ├── index.html          # single entry point — hero, upload dropzone, results panel
    ├── css/
    │   └── styles.css      # modern agricultural theme: greens, clean cards, mobile-first
    └── js/
        └── app.js          # API_BASE_URL constant + all fetch() calls to the backend
```

**Screens the frontend needs to cover:**

1. **Upload screen** — hero header ("CropCare AI"), drag-and-drop image dropzone with preview, an "Analyze Leaf" button.
2. **Loading state** — spinner + disabled inputs while the request is in flight.
3. **Results screen** — confidence badge/gauge, crop + disease name, and sections for Symptoms / Prevention / Organic Treatment / Chemical Treatment / Safety Notes. Include a small, non-alarming label showing whether the result came from the main classifier or the backup similarity search (the `method_used` field), e.g. *"matched via similarity search."*
4. **Low-confidence state** — friendly message asking for a clearer photo, shown instead of a result card when `method_used == "low_confidence"`.
5. **Error states** — invalid file type, network error, backend unavailable.

**Integration contract (what `app.js` talks to):**

- `POST /predict` — `multipart/form-data`, field name `file`. Show the loading state while the request is in flight.
- `GET /health` — returns `{"status": ..., "classifier_loaded": bool, "similarity_model_loaded": bool}`. Call this on page load; if either model isn't loaded, show a small **"ML engine: standby mode"** banner instead of hiding the issue.
- Don't invent response fields beyond the schema in [Section 1](#1-the-actual-architecture-what-everyone-should-build-toward) — if the backend isn't running yet, build against the documented contract and leave a clear TODO for re-verification once it's live, rather than baking fabricated example responses into the UI.

**Framework decision — pick one, don't let team members build different ones:**

- **Plain HTML/CSS/JS** *(current choice, matches the live `frontend/public/` layout above)* — zero build tooling, easy to demo from a single `index.html`, one less thing that can break before a viva.
- **React** — nicer component structure if you want the confidence gauge / tabbed treatment view to feel more polished, but adds an npm/build step. Only switch if the team already has React comfort; otherwise stick with plain HTML/CSS/JS for a viva/demo, not a shipped product.

(Back to top)

---

## 5. Minimal working code to unblock development immediately

If you want something you can literally run today while Claude Code works on the full version, here's the core hybrid logic in ~40 lines. This matches your report's ResNet50 code almost exactly, plus the classifier branch on top.

```python
# app/ml/hybrid_predictor.py — orchestration skeleton
from app.ml.mobilenet_model import MobileNetPredictor
from app.ml.similarity_model import SimilarityPredictor

CLASSIFIER_THRESHOLD = 0.60
SIMILARITY_THRESHOLD = 0.75

class HybridPredictor:
    def __init__(self):
        self.classifier = MobileNetPredictor()   # loads model.keras if present
        self.similarity = SimilarityPredictor()  # loads ResNet50 + reference embeddings

    def predict(self, image_bytes: bytes) -> dict:
        if self.classifier.is_loaded:
            result = self.classifier.predict(image_bytes)
            if result["confidence"] >= CLASSIFIER_THRESHOLD:
                result["method_used"] = "classifier"
                return result

        if self.similarity.is_loaded:
            sim_result = self.similarity.predict(image_bytes)
            if sim_result["confidence"] >= SIMILARITY_THRESHOLD:
                sim_result["method_used"] = "similarity_fallback"
                return sim_result

        return {
            "crop": None, "disease": None, "confidence": 0.0,
            "method_used": "low_confidence",
            "message": "Unable to confidently identify the disease. "
                       "Please upload a clearer, well-lit photo of the leaf."
        }
```

Give this file directly to Claude Code as a starting skeleton — tell it to build `mobilenet_model.py` and `similarity_model.py` to match this interface (both need `.is_loaded` and `.predict(image_bytes) -> dict`).

(Back to top)

---

## 6. For your presentation slide on "Design Methodology"

Since your report already has a Chapter 4 (Design Methodology) built around GANs/ResNet50/cosine similarity, don't rewrite it — **add one paragraph** bridging it to what you actually built:

> "While Phase II exploration considered GAN-based synthetic data generation, the Phase III implementation converged on a hybrid inference design: a MobileNetV3Small classifier as the primary decision path, with the ResNet50 + cosine similarity approach retained as a confidence-gated fallback rather than the primary path. This preserves the feature-extraction and similarity-matching work already validated in Phase II while adding a trainable classifier for the majority of well-lit, in-distribution cases."

This lets you keep 100% of your existing report content and slides, and just reframes the relationship between the two approaches — reviewers will read this as maturing the design, not contradicting it.

(Back to top)

---

## 7. Two-week task order (give this to ChatGPT to refine per your team's actual pace)

| Days | Backend/ML | Frontend |
|---|---|---|
| 1–2 | Repo skeleton, diseases.json, security.py, base.py | Build/wire all screens (§4) against mocked JSON |
| 3–5 | mobilenet_model.py stub + similarity_model.py (port from report code) | Static integration matching the response schema |
| 6–8 | train_mobilenet.py running on PlantVillage subset; build_reference_embeddings.py | Wire loading/error states, confidence badge |
| 9–10 | hybrid_predictor.py + /predict endpoint live | Point frontend at real localhost:8000 |
| 11–12 | Tests, threshold tuning on real held-out images | Polish UI, mobile responsiveness pass |
| 13–14 | Buffer / bug fixes | End-to-end run-through, screenshot for slides |

Don't let anyone start "polish" work before the end-to-end path (upload → real prediction → real result) works once, even ugly. That's your actual MVP milestone.

(Back to top)
