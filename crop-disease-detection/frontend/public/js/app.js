// CropCare frontend logic.
//
// Talks to the FastAPI backend at API_BASE_URL. The response shape consumed
// here matches backend/app/schemas/prediction.py exactly:
//   { crop, disease, scientific_name, confidence, method_used,
//     symptoms, prevention, treatment: { organic, chemical }, safety_notes, message }
//
// method_used is one of: "classifier" | "similarity_fallback" | "low_confidence"

// Auto-detects local dev vs. a deployed frontend. When you deploy the
// backend (e.g. to Render), replace PRODUCTION_API_URL below with your real
// backend URL — this file has no build step, so this is a plain edit, not
// an env variable.
const PRODUCTION_API_URL = "https://REPLACE-WITH-YOUR-RENDER-BACKEND-URL.onrender.com";

const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_BASE_URL = isLocalhost ? "http://127.0.0.1:8000" : PRODUCTION_API_URL;

// ---- Element references ----
const dropzone = document.getElementById("dropzone");
const dropzoneEmpty = document.getElementById("dropzoneEmpty");
const dropzonePreview = document.getElementById("dropzonePreview");
const previewImg = document.getElementById("previewImg");
const fileInput = document.getElementById("fileInput");
const clearBtn = document.getElementById("clearBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const formError = document.getElementById("formError");

const resultStates = {
  idle: document.getElementById("resultIdle"),
  loading: document.getElementById("resultLoading"),
  lowConfidence: document.getElementById("resultLowConfidence"),
  error: document.getElementById("resultErrorState"),
  success: document.getElementById("resultSuccess"),
};

const lowConfidenceMessage = document.getElementById("lowConfidenceMessage");
const errorMessage = document.getElementById("errorMessage");
const retakeBtn = document.getElementById("retakeBtn");
const retryBtn = document.getElementById("retryBtn");

const standbyBanner = document.getElementById("standbyBanner");
const standbyBannerText = document.getElementById("standbyBannerText");

let selectedFile = null;

// ---- Result state switching ----
function showResultState(name) {
  Object.entries(resultStates).forEach(([key, el]) => {
    el.hidden = key !== name;
  });
}

// ---- Health check on load ----
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error("health check failed");
    const data = await res.json();

    if (!data.classifier_loaded && !data.similarity_model_loaded) {
      standbyBannerText.textContent =
        "ML engine: standby mode — no trained model or reference embeddings loaded yet.";
      standbyBanner.hidden = false;
    } else if (!data.classifier_loaded) {
      standbyBannerText.textContent =
        "Primary classifier not loaded — running on similarity search only.";
      standbyBanner.hidden = false;
    } else {
      standbyBanner.hidden = true;
    }
  } catch (err) {
    standbyBannerText.textContent =
      "Can't reach the backend at " + API_BASE_URL + ". Is it running?";
    standbyBanner.hidden = false;
  }
}
checkHealth();

// ---- Dropzone interactions ----
function openFilePicker() {
  fileInput.click();
}
dropzone.addEventListener("click", openFilePicker);
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    openFilePicker();
  }
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("is-dragover");
});
dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("is-dragover");
});
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("is-dragover");
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelected(file);
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) handleFileSelected(file);
});

clearBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  resetUpload();
});

function handleFileSelected(file) {
  hideFormError();

  const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!allowedTypes.includes(file.type)) {
    showFormError("Please choose a JPG, PNG, or WEBP image.");
    return;
  }
  const maxBytes = 10 * 1024 * 1024;
  if (file.size > maxBytes) {
    showFormError("That file is over 10MB. Please choose a smaller image.");
    return;
  }

  selectedFile = file;
  const objectUrl = URL.createObjectURL(file);
  previewImg.src = objectUrl;

  dropzoneEmpty.hidden = true;
  dropzonePreview.hidden = false;
  analyzeBtn.disabled = false;

  showResultState("idle");
}

function resetUpload() {
  selectedFile = null;
  fileInput.value = "";
  previewImg.src = "";
  dropzoneEmpty.hidden = false;
  dropzonePreview.hidden = true;
  analyzeBtn.disabled = true;
  hideFormError();
  showResultState("idle");
}

function showFormError(msg) {
  formError.textContent = msg;
  formError.hidden = false;
}
function hideFormError() {
  formError.hidden = true;
}

// ---- Analyze ----
analyzeBtn.addEventListener("click", analyzeLeaf);
retakeBtn.addEventListener("click", () => {
  resetUpload();
  openFilePicker();
});
retryBtn.addEventListener("click", analyzeLeaf);

async function analyzeLeaf() {
  if (!selectedFile) return;

  analyzeBtn.disabled = true;
  dropzone.style.pointerEvents = "none";
  showResultState("loading");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${res.status})`);
    }

    const data = await res.json();
    renderResult(data);
  } catch (err) {
    errorMessage.textContent =
      err.message === "Failed to fetch"
        ? `Couldn't reach the backend at ${API_BASE_URL}. Check that it's running.`
        : err.message;
    showResultState("error");
  } finally {
    analyzeBtn.disabled = false;
    dropzone.style.pointerEvents = "";
  }
}

function renderResult(data) {
  if (data.method_used === "low_confidence") {
    lowConfidenceMessage.textContent = data.message;
    showResultState("lowConfidence");
    return;
  }

  // --- Header ---
  document.getElementById("resultCrop").textContent = data.crop || "Unknown crop";
  document.getElementById("resultDisease").textContent = data.disease || "Unknown";
  const sciEl = document.getElementById("resultScientific");
  if (data.scientific_name) {
    sciEl.textContent = data.scientific_name;
    sciEl.hidden = false;
  } else {
    sciEl.hidden = true;
  }

  // --- Confidence ring ---
  const pct = Math.round((data.confidence || 0) * 100);
  const circumference = 169.6; // 2 * PI * r(27)
  const ring = document.getElementById("confidenceRing");
  ring.style.strokeDashoffset = String(circumference * (1 - (data.confidence || 0)));
  document.getElementById("confidenceValue").textContent = `${pct}%`;

  // --- Method note ---
  const methodNote = document.getElementById("methodNote");
  if (data.method_used === "similarity_fallback") {
    methodNote.textContent =
      "Matched via reference image comparison (the primary classifier wasn't confident enough on this photo).";
    methodNote.hidden = false;
  } else {
    methodNote.hidden = true;
  }

  // --- Tab panels ---
  renderList("panelSymptoms", data.symptoms);
  renderList("panelPrevention", data.prevention);
  renderTreatment(data.treatment);
  renderList("panelSafety", data.safety_notes);

  showResultState("success");
  resetTabs();
}

function renderList(elementId, items) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function renderTreatment(treatment) {
  const el = document.getElementById("panelTreatment");
  el.innerHTML = "";

  const organic = treatment?.organic || [];
  const chemical = treatment?.chemical || [];

  if (organic.length === 0 && chemical.length === 0) {
    el.innerHTML = '<p style="color: var(--ink-faint); font-size: 0.9rem;">No treatment needed.</p>';
    return;
  }

  if (organic.length > 0) {
    el.appendChild(buildTreatmentGroup("Organic options", organic));
  }
  if (chemical.length > 0) {
    el.appendChild(buildTreatmentGroup("Chemical options", chemical));
  }
}

function buildTreatmentGroup(title, items) {
  const group = document.createElement("div");
  group.className = "treatment-group";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const list = document.createElement("ul");
  list.style.listStyle = "none";
  list.style.margin = "0";
  list.style.padding = "0";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    li.style.position = "relative";
    li.style.padding = "0 0 12px 20px";
    li.style.color = "var(--ink-soft)";
    li.style.fontSize = "0.92rem";
    list.appendChild(li);
  });
  group.appendChild(heading);
  group.appendChild(list);
  return group;
}

// ---- Tabs ----
const tabButtons = document.querySelectorAll(".tab");
tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;
    tabButtons.forEach((b) => b.classList.toggle("is-active", b === btn));
    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.panel === target);
    });
  });
});

function resetTabs() {
  tabButtons.forEach((b, i) => b.classList.toggle("is-active", i === 0));
  document.querySelectorAll(".tab-panel").forEach((panel, i) => {
    panel.classList.toggle("is-active", i === 0);
  });
}
