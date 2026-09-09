<div align="center">

# 🌾 Crop Disease Detection — Hybrid AI System

### AI-Based Crop Disease Detection Model
**VIT Bhopal Capstone Project · DSN4096 · School of Computing Science and Engineering**

![Python](https://img.shields.io/badge/python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Status](https://img.shields.io/badge/status-pre--training%20%2F%20standby%20mode-D69E2E?style=for-the-badge)
![License](https://img.shields.io/badge/license-Academic%20Use-2F855A?style=for-the-badge)

*A MobileNetV3Small classifier (primary) backed by a ResNet50 + cosine-similarity fallback (confidence-gated), served via FastAPI, with a vanilla HTML/CSS/JS frontend.*

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Team & Academic Details](#-team--academic-details)
- [Problem Statement](#-problem-statement)
- [Objectives](#-objectives)
- [Repository Structure](#-repository-structure)
- [System Architecture — The Hybrid Pipeline](#-system-architecture--the-hybrid-pipeline)
- [From Phase II to Phase III — Design Evolution](#-from-phase-ii-to-phase-iii--design-evolution)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
  - [3. Training the Classifier](#3-training-the-classifier-once-your-dataset-is-ready)
  - [4. Adding More Diseases](#4-adding-more-diseases)
- [API Response Contract](#-api-response-contract)
- [Known Gaps & Roadmap](#-known-gaps--roadmap)
- [Limitations (from Phase II Report)](#-limitations-from-phase-ii-report)
- [References](#-references)
- [Acknowledgements](#-acknowledgements)
- [License](#-license)

---

## 📖 Overview

Agriculture plays a major role in global food security, and advances in AI have opened new opportunities for improving productivity and sustainability. This project explores the application of machine learning and deep learning in agriculture, focusing on crop health monitoring and automated disease identification.

This repo is buildable and testable **right now**, before any model is trained — both models (MobileNetV3Small classifier and ResNet50 similarity matcher) start in **standby mode**, and the API reports that honestly instead of faking a prediction. Train the classifier and build the reference embeddings whenever your dataset is ready; the API and frontend don't need any code changes when you do.

```
crop-disease-detection/
├── backend/            FastAPI app — see backend/app/
├── frontend/            Static HTML/CSS/JS — see frontend/public/
├── ml_pipeline/          Dataset prep + training scripts (run independently)
├── docs/
│   └── MASTERPLAN.md    Full architecture, prompts, and task order
├── .gitignore
└── README.md            This file
```



## 🎓 Team & Academic Details

| Field | Detail |
|---|---|
| Project Title | Crop Detection for Agricultural System |
| Course | DSN4096 — Capstone Project Phase-II |
| Degree | B.Tech, Computer Science and Engineering (AI & Machine Learning) |
| Institution | VIT Bhopal University, Kothrikalan, Sehore, Madhya Pradesh – 466114 |
| School | School of Computing Science and Engineering |
| Report Date | April 2025 |
| Project Guide | Dr. ANIL KUMAR YADAV  |
| Program Chair | Dr. JITENDRA PRATAP SINGH |

**Team Members**

| Name | Registration No. |
|---|---|
| SHASHANK | 25BAI10569 |
| KANAK GUPTA | 25BAI11452 |
| KAANYA AGARWAL | 25BAI10237 |
| VAANYA Singh | 25BAI11524 |
| PRIYANSHU JAIN | 25BAI11181 |
| NAMAN SHARMA | 25BAI11560 |

## 🚨 Problem Statement

Modern agriculture is confronted with numerous challenges, including crop diseases (phytopathology), unpredictable weather conditions, and inefficient resource management, all of which contribute to reduced yields and economic losses. Traditional crop monitoring methods, such as manual inspection and basic image processing techniques, suffer from limited scalability, real-time inefficiency, and lower accuracy, making them inadequate for addressing these challenges effectively.

Furthermore, the lack of high-quality labelled datasets poses a significant barrier to developing robust machine learning models for precision agriculture. Without sufficient data, deep learning models struggle to achieve high accuracy in crop classification, disease identification, and yield estimation.

This project introduces an AI-driven Crop Recognition System that integrates deep learning-based feature extraction, AI-assisted crop analysis, and similarity-based image matching to enhance crop identification accuracy, improve decision-making for farmers, and optimize agricultural productivity.

## 🎯 Objectives

The primary objective of this project is to develop and implement an AI-driven Crop Recognition System that leverages deep learning, computer vision, and AI models to enhance data-driven decision-making in agriculture. Specifically, this study seeks to:

- Enhance crop disease detection by utilizing AI-powered analysis to classify and identify diseased plants more accurately.
- Enable precision farming by providing real-time insights into crop health, helping farmers optimize resource allocation and harvesting strategies.
- Overcome data scarcity issues by leveraging AI to improve image-based crop classification and decision-making.
- Classify different vegetable crops accurately to support automated crop identification, monitoring, and disease management for smart farming applications.


## 🗂 Repository Structure

```
crop-disease-detection/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py        # GET /health — model_loaded status for BOTH models
│   │   │   │   └── predict.py       # POST /predict
│   │   │   └── api_router.py
│   │   ├── core/
│   │   │   ├── config.py            # thresholds, upload limits, CORS_ORIGINS
│   │   │   └── security.py          # upload validation: size, MIME, PIL verify
│   │   ├── data/
│   │   │   └── diseases.json        # crop, disease, symptoms, prevention, treatment
│   │   ├── ml/
│   │   │   ├── base.py              # BasePredictor(ABC) — predict(image_bytes) -> dict
│   │   │   ├── mobilenet_model.py   # primary classifier, is_loaded flag if weights absent
│   │   │   ├── similarity_model.py  # ResNet50 feature extractor + cosine similarity
│   │   │   ├── hybrid_predictor.py  # orchestrates: try primary, fall back if low conf
│   │   │   ├── preprocessor.py      # shared 224x224 RGB normalization
│   │   │   └── weights/             # .keras / .npz artifacts (gitignored)
│   │   ├── schemas/
│   │   │   └── prediction.py        # pydantic request/response models incl. "method_used"
│   │   ├── services/
│   │   │   └── disease_service.py   # JSON lookup + low-confidence fallback message
│   │   └── main.py                  # FastAPI app, CORS, startup model loading
│   ├── tests/
│   │   └── test_api.py              # 12 tests — pass even before any model is trained
│   └── requirements.txt
├── frontend/
│   └── public/
│       ├── index.html
│       ├── css/
│       └── js/
│           └── app.js               # API_BASE_URL configured here
├── ml_pipeline/
│   ├── download_data.py             # fetch PlantVillage, organize into class folders
│   ├── validate_and_clean.py        # corrupt/dup detection, class balance report
│   ├── build_reference_embeddings.py  # ResNet50 over curated reference set
│   ├── train_mobilenet.py           # transfer learning, EarlyStopping, ModelCheckpoint
│   ├── export_class_indices.py      # saves class_names.json alongside the model
│   └── dataset/                     # raw/ + clean/ (gitignored — never commit images)
├── docs/
│   └── MASTERPLAN.md                # architecture, tool prompts, two-week task order
├── .gitignore
└── README.md
```

## 🏗 System Architecture — The Hybrid Pipeline

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

Both thresholds live in `backend/app/core/config.py` — tune them once you have real held-out validation data, don't leave them at the defaults for your final report numbers.

**Why this design is defensible in a viva:** the primary path is a trained classifier; when it's not confident, the system falls back to a similarity-search safety net instead of guessing. That's a legitimate design decision, not a hack — and it directly reuses the ResNet50 + cosine similarity code already validated in the Phase II report.


## 🔄 From Phase II to Phase III — Design Evolution

The Phase II report (Chapter 4, Design Methodology) was built around GAN-based synthetic data generation, ResNet50 feature extraction, Google Gemini AI for crop recognition, and cosine-similarity image matching. That exploration is not discarded — it evolved:

> While Phase II exploration considered GAN-based synthetic data generation, the Phase III implementation converges on a **hybrid inference design**: a MobileNetV3Small classifier as the primary decision path, with the ResNet50 + cosine similarity approach retained as a **confidence-gated fallback** rather than the primary path. This preserves the feature-extraction and similarity-matching work already validated in Phase II while adding a trainable classifier for the majority of well-lit, in-distribution cases.

Gemini AI is deliberately **not** in the live inference path for the MVP — it remains a stretch goal (e.g. generating a natural-language explanation of the result), since depending on a paid/rate-limited external API for the core demo path is a real risk during a viva.


## 🛠 Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Primary classifier | MobileNetV3Small (TensorFlow/Keras) | Small, fast, fine-tunes well on limited data |
| Fallback matcher | ResNet50 (PyTorch, torchvision) — frozen, feature extraction only | Already validated in the Phase II report; no training needed |
| Similarity | scikit-learn `cosine_similarity` | Matches the Phase II report exactly |
| Backend | FastAPI + Uvicorn | Async, typed, fast to build |
| Image processing | Pillow, NumPy, OpenCV | Standard preprocessing / augmentation |
| Frontend | Vanilla HTML/CSS/JS | Zero build tooling — one less point of failure during a live demo |
| Dataset | PlantVillage (public, pre-labeled) | Don't hand-collect for MVP — use this to start |
| Disease info | `diseases.json` | Kept decoupled from model code |
| Dev tooling | Jupyter Notebook / VS Code, Google Colab | Free GPU/TPU access for training experiments |
| Version control | GitHub | Track changes, collaborate, manage the repo |


## 🚀 Getting Started

### 1. Backend Setup

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

All 12 tests should pass even before any model is trained — several of them specifically verify the "standby mode" behavior is honest rather than faked.

Start the dev server:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check it's alive:

```bash
curl http://127.0.0.1:8000/health
```

Interactive API docs (Swagger UI) are auto-generated at `http://127.0.0.1:8000/docs`.


### 2. Frontend Setup

No build step — it's plain HTML/CSS/JS. Serve it with any static server:

```bash
cd frontend/public
python3 -m http.server 5500
```

Then open `http://127.0.0.1:5500/index.html` in a browser. The backend's CORS config in `backend/app/core/config.py` already allows `http://127.0.0.1:5500` — if you serve from a different port, add it to `CORS_ORIGINS` there.

The API base URL is set at the top of `frontend/public/js/app.js`:

```js
const API_BASE_URL = "http://127.0.0.1:8000";
```

Change this if your backend runs somewhere else.



### 3. Training the Classifier (once your dataset is ready)

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

Restart the backend after either artifact changes — models are loaded once at server startup, not per-request.

```bash
curl http://127.0.0.1:8000/health
# classifier_loaded and/or similarity_model_loaded should now be true
```


### 4. Adding More Diseases

1. Add a new entry to `backend/app/data/diseases.json`, keyed by a snake_case class name (e.g. `"wheat_rust"`).
2. Add real, correctly-labeled training images for that class under `dataset/raw/wheat_rust/` (or map an existing PlantVillage folder to it in `ml_pipeline/download_data.py`'s `CLASS_KEY_MAP`).
3. Re-run the cleaning, training, and embedding-building steps above.
4. Run `python ml_pipeline/export_class_indices.py --dataset dataset/clean` to double check every class in your dataset has a matching `diseases.json` entry before you retrain.



## 📡 API Response Contract

**`POST /predict`** — `multipart/form-data`, field name `file`

```json
{
  "crop": "string",
  "disease": "string",
  "confidence": 0.0,
  "method_used": "classifier | similarity_fallback | low_confidence",
  "symptoms": ["string"],
  "prevention": ["string"],
  "treatment": { "organic": ["string"], "chemical": ["string"] },
  "safety_notes": ["string"],
  "message": "string"
}
```

If `method_used == "low_confidence"`, `symptoms` / `prevention` / `treatment` are `null` and `message` tells the user to retake the photo.

**`GET /health`**

```json
{
  "status": "ok",
  "classifier_loaded": false,
  "similarity_model_loaded": false
}
```


## 🧭 Known Gaps & Roadmap

- [ ] No dataset has been trained on yet — `ml_pipeline/train_mobilenet.py` needs a real PlantVillage (or similar) download to run against.
- [ ] `diseases.json` currently has 6 entries (5 diseases + healthy) across Tomato, Potato, and Rice — extend as your dataset grows.
- [ ] Thresholds (0.60 / 0.75) are reasonable starting points, not tuned — revisit once you have validation-set numbers to report honestly.
- [ ] `API_BASE_URL` in `app.js` is hardcoded to localhost — update before deploying anywhere else.
- [ ] IoT integration (drones, soil sensors, weather monitoring) — future enhancement.
- [ ] Mobile application version for direct smartphone scanning.
- [ ] Multimodal data fusion — satellite imagery, soil quality, climate forecasts.
- [ ] Multi-language and voice-assisted interface for rural accessibility.


## ⚠️ Limitations (from Phase II Report)

- **Data quality and availability** — diverse, labeled, well-annotated agricultural images remain a challenge, particularly for rare crop diseases and underrepresented regions.
- **Computational requirements** — training demands high-performance GPUs or cloud-based solutions; can be time-consuming and resource-intensive.
- **Generalization challenges** — real-world variability (extreme weather, new disease strains, unseen environmental conditions) remains difficult to fully cover.
- **Real-time performance** — analysis on low-end hardware or mobile devices may be limited by computational complexity.
- **Dependency on image quality** — poor resolution, improper lighting, or blurred images can lead to misclassification.
- **Internet dependency** — a web-based interface means users in remote agricultural regions with limited connectivity may face accessibility issues.



## 📚 References

1. Goodfellow, I., et al. (2014). "Generative Adversarial Networks." *Advances in Neural Information Processing Systems*, 27.
2. He, K., et al. (2016). "Deep Residual Learning for Image Recognition." *IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*.
3. Kamilaris, A., & Prenafeta-Boldú, F. X. (2018). "Deep Learning in Agriculture: A Survey." *Computers and Electronics in Agriculture*, 147, 70–90.
4. Liakos, K. G., et al. (2018). "Machine Learning in Agriculture: A Review." *Sensors*, 18(8), 2674.
5. Zhang, C., & Kovacs, J. M. (2012). "The Application of Small Unmanned Aerial Systems for Precision Agriculture: A Review." *Precision Agriculture*, 13(6), 693–712.
6. Mohanty, S. P., et al. (2016). "Using Deep Learning for Image-Based Plant Disease Detection." *Frontiers in Plant Science*, 7, 1419.
7. Weiss, M., et al. (2020). "Remote Sensing for Agricultural Applications: A Meta-Review." *Remote Sensing of Environment*, 237, 111593.


## 🙏 Acknowledgements

We would like to thank our internal guide **Dr. ANIL KUMAR MISHRA** for continually guiding and actively participating in this project, and providing valuable suggestions throughout. We also thank **Dr. JITHENDRA PRATAP SINGH** (PC-Lead) and **Dr. ** (Dean), School of Computing Science Engineering and Artificial Intelligence, for their valuable support and encouragement, along with all the technical and teaching staff who extended support directly or indirectly.


## 📄 License

Developed as part of the **VIT Bhopal Capstone Project (DSN4096)** for academic purposes.

