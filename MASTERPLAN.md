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
## 3. Frontend framework decision

Pick **one**, don't let team members build different ones:

- **Plain HTML/CSS/JS** — faster for a 2-person frontend pair to reason about, zero build tooling, easy to demo from a single `index.html`. Recommended if your team's frontend experience is limited.
- **React (via v0 output)** — nicer component structure, better if you want the confidence gauge / tabbed treatment view to feel polished. Slightly more setup (npm, build step) which is one more thing that can break before a viva.

Given this is a **viva/demo**, not a shipped product, I'd lean **plain HTML/CSS/JS** — one less point of failure. If your team already has React comfort, ignore this and use v0's output directly.

(Back to top)
