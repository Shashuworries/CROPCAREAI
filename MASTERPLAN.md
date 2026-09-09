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
- [3. What to Hand to Each Tool](#3-what-to-hand-to-each-tool)
- [4. Frontend Framework Decision](#4-frontend-framework-decision)
- [5. Claude Code Prompt — Backend + Hybrid ML](#5-claude-code-prompt--backend--hybrid-ml-paste-as-is)
- [6. Cursor / v0 Prompt — Frontend](#6-cursor--v0-prompt--frontend)
- [7. Minimal Working Code to Unblock Claude Code Immediately](#7-minimal-working-code-to-unblock-claude-code-immediately)
- [8. For Your Presentation Slide on "Design Methodology"](#8-for-your-presentation-slide-on-design-methodology)
- [9. Two-Week Task Order](#9-two-week-task-order-give-this-to-chatgpt-to-refine-per-your-teams-actual-pace)

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

## 3. What to Hand to Each Tool

### → ChatGPT (coordination / architecture review)
Paste **Section 1 and 2 of this file** verbatim, then:
> Review this architecture for a 5-person capstone team with ~2 weeks left before demo. Flag anything unrealistic given that timeline, and give me a day-by-day task order so Claude Code (backend/ML) and Cursor (frontend) aren't blocked waiting on each other.

### → Claude Code (backend + ML)
Use the prompt in **Section 5** below. It supersedes any earlier backend/ML prompt you gave it — tell it explicitly: *"This replaces earlier instructions — we're now building a hybrid classifier+similarity system, not classifier-only."*

### → Cursor + v0 (frontend)
Use the prompt in **Section 6**. v0 is good for generating the initial component visuals fast; Cursor is better for wiring them to your actual FastAPI endpoints once they exist. Suggested flow: generate the results/upload screens in v0 first, drop the code into your repo, then have Cursor integrate against the live API.

(Back to top)

---

## 4. Frontend framework decision

Pick **one**, don't let team members build different ones:

- **Plain HTML/CSS/JS** — faster for a 2-person frontend pair to reason about, zero build tooling, easy to demo from a single `index.html`. Recommended if your team's frontend experience is limited.
- **React (via v0 output)** — nicer component structure, better if you want the confidence gauge / tabbed treatment view to feel polished. Slightly more setup (npm, build step) which is one more thing that can break before a viva.

Given this is a **viva/demo**, not a shipped product, I'd lean **plain HTML/CSS/JS** — one less point of failure. If your team already has React comfort, ignore this and use v0's output directly.

(Back to top)

---

## 5. CLAUDE CODE PROMPT — Backend + Hybrid ML (paste as-is)

```
You are the backend and ML engineer for our capstone project: AI-Based Crop Disease
Detection System (VIT Bhopal, DSN4096).

ARCHITECTURE (this supersedes any earlier instructions you were given):

We are building a HYBRID inference pipeline, not a single classifier:

1. PRIMARY: A MobileNetV3Small classifier (TensorFlow/Keras, transfer learning),
   trained on a labeled leaf-disease dataset (starting point: PlantVillage).
2. FALLBACK: When the classifier's confidence is below a threshold (default 0.60),
   fall back to a ResNet50-based feature extractor + cosine similarity search
   against a small reference embedding set, returning the closest match if its
   similarity score is above a second threshold (default 0.75).
3. If BOTH fail their thresholds, return a "low confidence, please retake photo"
   response. Do not guess.

IMPORTANT CONSTRAINTS:
- Do NOT fabricate trained model weights, accuracy numbers, or predictions.
- If a model file isn't present on disk yet, the API must clearly report
  "model not loaded" / "standby mode" rather than faking a result.
- Keep the classifier and the similarity matcher as separate, swappable modules
  behind a common interface — the API layer should not care which one answered.
- Disease information (symptoms/prevention/treatment) lives in a separate
  diseases.json, never inside the model code.

REPO LAYOUT TO CREATE:

backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── health.py       # GET /health — model_loaded status for BOTH models
│   │   │   └── predict.py      # POST /predict
│   │   └── api_router.py
│   ├── core/
│   │   ├── config.py           # thresholds, upload limits, via pydantic BaseSettings
│   │   └── security.py         # upload validation: size, MIME, PIL verify
│   ├── data/
│   │   └── diseases.json
│   ├── ml/
│   │   ├── base.py             # BasePredictor(ABC) — predict(image_bytes) -> dict
│   │   ├── mobilenet_model.py  # primary classifier, is_loaded flag if weights absent
│   │   ├── similarity_model.py # ResNet50 feature extractor + cosine similarity
│   │   ├── hybrid_predictor.py # orchestrates: try primary, fall back if low conf
│   │   └── preprocessor.py     # shared 224x224 RGB normalization
│   ├── schemas/
│   │   └── prediction.py       # pydantic request/response models incl. "method_used"
│   ├── services/
│   │   └── disease_service.py  # JSON lookup + low-confidence fallback message
│   └── main.py                 # FastAPI app, CORS, startup model loading
├── tests/
│   └── test_api.py
└── requirements.txt

ml_pipeline/
├── download_data.py            # fetch PlantVillage, organize into class folders
├── validate_and_clean.py       # corrupt/dup detection, class balance report
├── build_reference_embeddings.py  # runs ResNet50 over a curated reference set,
│                                    saves embeddings for the similarity fallback
├── train_mobilenet.py          # transfer learning, augmentation, EarlyStopping,
│                                  ModelCheckpoint('model.keras')
└── export_class_indices.py     # saves class_names.json alongside the model

RESPONSE SCHEMA for POST /predict:
{
  "crop": str,
  "disease": str,
  "confidence": float,
  "method_used": "classifier" | "similarity_fallback" | "low_confidence",
  "symptoms": [str],
  "prevention": [str],
  "treatment": {"organic": [str], "chemical": [str]},
  "safety_notes": [str],
  "message": str
}

If method_used == "low_confidence", symptoms/prevention/treatment should be null
and message should tell the user to retake the photo.

SECURITY:
- Max upload 10MB, whitelist .jpg/.jpeg/.png/.webp
- PIL-verify every upload (reject corrupt/polyglot files)
- No stack traces in API responses, no internal paths exposed
- CORS configured for local frontend dev (http://localhost:*)

WORK ORDER (do not skip ahead):
1. Inspect repo, report what exists / is missing.
2. Build diseases.json with 4–6 real disease entries (crop, disease_name,
   scientific_name, description, symptoms, prevention, treatment.organic/chemical,
   safety_notes) — use real agricultural knowledge, not invented dosages.
3. Build core/security.py and core/config.py.
4. Build ml/base.py, then mobilenet_model.py and similarity_model.py as
   separate implementations of it, then hybrid_predictor.py to orchestrate.
5. Build services/disease_service.py.
6. Build the FastAPI endpoints and wire them to hybrid_predictor.
7. Write ml_pipeline scripts (data prep, training script, embedding builder) —
   these can run independently of the API being finished.
8. Add tests for: /health, valid image, invalid file, oversized file, corrupt
   image, low-confidence path, disease lookup, model-not-loaded path.
9. Give me exact shell commands to install deps, run tests, and start the server.

Start by inspecting the repository and reporting status before writing any code.
```

(Back to top)

---

## 6. CURSOR / v0 PROMPT — Frontend

### First, in v0 (generate the visual components):
```
Design a clean, mobile-responsive crop disease detection app for farmers.

Screens needed:
1. Upload screen: hero header "CropCare AI", drag-and-drop image dropzone with
   preview, an "Analyze Leaf" button.
2. Loading state: spinner + disabled inputs while analyzing.
3. Results screen with:
   - Confidence badge/gauge
   - Crop + disease name
   - Tabbed or accordion sections: Symptoms, Prevention, Organic Treatment,
     Chemical Treatment, Safety Notes
   - A small label showing whether the result came from the main classifier
     or the backup similarity search (method_used field) — keep this subtle,
     e.g. a small "matched via similarity search" note, not alarming
4. Low-confidence state: friendly message asking for a clearer photo.
5. Error states: invalid file, network error, backend unavailable.

Style: modern agricultural theme, greens, clean cards, no clutter, mobile-first.
Use Tailwind core utility classes only.
```

### Then, in Cursor (wire it to the real backend):
```
You are the frontend integration engineer for our crop disease detection app.

The backend is FastAPI, running at http://localhost:8000, with:
  POST /predict  — multipart/form-data, field name "file"
  GET  /health   — returns {"status": ..., "classifier_loaded": bool,
                             "similarity_model_loaded": bool}

Response shape from /predict:
{
  "crop": str, "disease": str, "confidence": float,
  "method_used": "classifier" | "similarity_fallback" | "low_confidence",
  "symptoms": [str] | null, "prevention": [str] | null,
  "treatment": {"organic": [str], "chemical": [str]} | null,
  "safety_notes": [str] | null, "message": str
}

DO NOT invent fields beyond this. If the backend isn't running yet, build
against this exact contract and leave a clear TODO for re-verification once
the backend is live — do not fabricate example responses baked into the UI.

Take the components from our v0 generation (already in the repo under
/components or /public depending on stack) and wire them to:
1. POST the uploaded file to /predict, show loading state during the request.
2. Render method_used distinctly — if "similarity_fallback", show a small
   "matched via reference image comparison" note near the confidence badge.
3. If method_used == "low_confidence", show the retake-photo state instead
   of a result card.
4. Handle network errors and backend-unavailable gracefully.
5. Call GET /health on load; if either model isn't loaded, show a small
   "ML engine: standby mode" banner instead of hiding the issue.

Test with: a valid image, an invalid file type, and (if backend running)
an actual low-confidence case.
```

(Back to top)

---

## 7. Minimal working code to unblock Claude Code immediately

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

## 8. For your presentation slide on "Design Methodology"

Since your report already has a Chapter 4 (Design Methodology) built around GANs/ResNet50/cosine similarity, don't rewrite it — **add one paragraph** bridging it to what you actually built:

> "While Phase II exploration considered GAN-based synthetic data generation, the Phase III implementation converged on a hybrid inference design: a MobileNetV3Small classifier as the primary decision path, with the ResNet50 + cosine similarity approach retained as a confidence-gated fallback rather than the primary path. This preserves the feature-extraction and similarity-matching work already validated in Phase II while adding a trainable classifier for the majority of well-lit, in-distribution cases."

This lets you keep 100% of your existing report content and slides, and just reframes the relationship between the two approaches — reviewers will read this as maturing the design, not contradicting it.

(Back to top)

---

## 9. Two-week task order (give this to ChatGPT to refine per your team's actual pace)

| Days | Backend/ML (Claude Code) | Frontend (Cursor/v0) |
|---|---|---|
| 1–2 | Repo skeleton, diseases.json, security.py, base.py | v0: generate all screens |
| 3–5 | mobilenet_model.py stub + similarity_model.py (port from report code) | Cursor: static integration against mocked JSON matching the schema |
| 6–8 | train_mobilenet.py running on PlantVillage subset; build_reference_embeddings.py | Wire loading/error states, confidence badge |
| 9–10 | hybrid_predictor.py + /predict endpoint live | Point frontend at real localhost:8000 |
| 11–12 | Tests, threshold tuning on real held-out images | Polish UI, mobile responsiveness pass |
| 13–14 | Buffer / bug fixes | End-to-end run-through, screenshot for slides |

Don't let anyone start "polish" work before the end-to-end path (upload → real prediction → real result) works once, even ugly. That's your actual MVP milestone.

(Back to top)
