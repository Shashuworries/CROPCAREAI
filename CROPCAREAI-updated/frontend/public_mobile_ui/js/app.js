/**
 * CropCare AI — Frontend logic.
 *
 * This talks to the real FastAPI backend (see backend/app/schemas/prediction.py
 * for the exact response shape). It no longer fakes a result — every "Analyze"
 * click sends the actual photo to /predict and renders whatever comes back.
 *
 * If you don't have the backend running yet, use the "Offline Demo Panel"
 * (double-tap the logo) to preview the screens without a live model.
 */

document.addEventListener('DOMContentLoaded', () => {

  // ==========================================
  // 0. API CONFIG
  // ==========================================
  // Auto-detects local dev vs a deployed frontend, same pattern as the
  // simple frontend in frontend/public/js/app.js. Replace PRODUCTION_API_URL
  // once you deploy the backend (e.g. to Render) — no build step, plain edit.
  const PRODUCTION_API_URL = "https://REPLACE-WITH-YOUR-RENDER-BACKEND-URL.onrender.com";
  const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const API_BASE_URL = isLocalhost ? "http://127.0.0.1:8000" : PRODUCTION_API_URL;

  // Optional: OpenWeatherMap API key for the home-screen risk card.
  // Get a free key at https://openweathermap.org/api — leave blank to skip.
  const OPENWEATHER_API_KEY = "";

  const appState = {
    currentScreen: 'screen-home',
    language: 'en',
    selectedFile: null,
    selectedImageDataUrl: null,
    isSpeaking: false,
    offlineDemoMode: false,   // true only if the user opens the dev panel
    scanHistory: []           // populated from REAL predictions only
  };

  let currentActiveReport = null;

  // ==========================================
  // 1. NAVIGATION
  // ==========================================
  function navigateTo(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) {
      target.classList.add('active');
      appState.currentScreen = screenId;
    }
    document.querySelectorAll('.bottom-nav .nav-item').forEach(item => {
      item.classList.toggle('active', item.getAttribute('data-screen') === screenId);
    });
    const contentArea = document.querySelector('.app-content');
    if (contentArea) contentArea.scrollTop = 0;
  }

  document.querySelectorAll('.bottom-nav .nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const screenId = btn.getAttribute('data-screen');
      if (screenId) navigateTo(screenId);
    });
  });

  // Guard every optional back/nav button with `?.` so a missing element in a
  // future edit can never silently kill the rest of the script again.
  document.getElementById('btn-scan-back')?.addEventListener('click', () => navigateTo('screen-home'));
  document.getElementById('btn-preview-back')?.addEventListener('click', () => navigateTo('screen-scan'));
  document.getElementById('btn-result-home')?.addEventListener('click', () => navigateTo('screen-home'));

  document.getElementById('btn-hero-analyze')?.addEventListener('click', () => navigateTo('screen-scan'));
  document.getElementById('qa-scan')?.addEventListener('click', () => navigateTo('screen-scan'));
  document.getElementById('qa-history')?.addEventListener('click', () => navigateTo('screen-history'));
  document.getElementById('qa-support')?.addEventListener('click', () => navigateTo('screen-support'));
  document.getElementById('btn-view-all-history')?.addEventListener('click', () => navigateTo('screen-history'));

  // ==========================================
  // 2. BACKEND HEALTH CHECK
  // ==========================================
  async function checkBackendHealth() {
    const banner = document.getElementById('global-status-banner');
    const text = document.getElementById('global-status-text');
    try {
      const res = await fetch(`${API_BASE_URL}/health`, { method: 'GET' });
      if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
      const data = await res.json();
      if (!data.classifier_loaded && !data.similarity_model_loaded) {
        text.textContent = 'Backend is up, but no trained model is loaded yet (standby mode) — predictions will show "low confidence" until a model is trained.';
        banner.classList.remove('hidden');
      } else {
        banner.classList.add('hidden');
      }
    } catch (err) {
      text.textContent = `Can't reach the backend at ${API_BASE_URL}. Start it locally (uvicorn) or open the Offline Demo Panel (double-tap the logo) to preview the UI.`;
      banner.classList.remove('hidden');
    }
  }
  checkBackendHealth();

  // ==========================================
  // 3. IMAGE UPLOAD & VALIDATION
  // ==========================================
  const dropzone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('leaf-input-file');
  const cameraInput = document.getElementById('leaf-input-camera');

  document.getElementById('btn-trigger-gallery')?.addEventListener('click', () => fileInput.click());
  document.getElementById('btn-trigger-camera')?.addEventListener('click', () => cameraInput.click());
  dropzone?.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(evt => {
    dropzone?.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  });
  ['dragleave', 'drop'].forEach(evt => {
    dropzone?.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.remove('drag-over'); });
  });
  dropzone?.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) handleSelectedFile(files[0]);
  });

  fileInput?.addEventListener('change', e => {
    if (e.target.files?.length) handleSelectedFile(e.target.files[0]);
  });
  cameraInput?.addEventListener('change', e => {
    if (e.target.files?.length) handleSelectedFile(e.target.files[0]);
  });

  function handleSelectedFile(file) {
    const errorBanner = document.getElementById('preview-error-banner');
    errorBanner.classList.add('hidden');

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type.toLowerCase())) {
      return showPreviewError('Invalid format! Please upload a JPG, PNG, or WEBP image.');
    }
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return showPreviewError('File size exceeds 10 MB limit. Please choose a smaller photo.');
    }

    appState.selectedFile = file;
    document.getElementById('file-name-disp').textContent = file.name;
    document.getElementById('file-size-disp').textContent =
      (file.size / (1024 * 1024)).toFixed(2) + ' MB · ' + file.type.split('/')[1].toUpperCase();

    const reader = new FileReader();
    reader.onload = e => {
      appState.selectedImageDataUrl = e.target.result;
      document.getElementById('img-preview').src = appState.selectedImageDataUrl;
      document.getElementById('img-scanning-thumb').src = appState.selectedImageDataUrl;
      document.getElementById('img-result-display').src = appState.selectedImageDataUrl;
      navigateTo('screen-preview');
    };
    reader.readAsDataURL(file);
  }

  function showPreviewError(message) {
    const errorBanner = document.getElementById('preview-error-banner');
    document.getElementById('txt-error-message').textContent = message;
    errorBanner.classList.remove('hidden');
    navigateTo('screen-preview');
  }

  document.getElementById('btn-reselect-image')?.addEventListener('click', () => {
    fileInput.value = '';
    cameraInput.value = '';
    appState.selectedFile = null;
    appState.selectedImageDataUrl = null;
    navigateTo('screen-scan');
  });

  // ==========================================
  // 4. REAL ANALYSIS — calls POST /predict
  // ==========================================
  document.getElementById('btn-confirm-analyze')?.addEventListener('click', () => {
    if (appState.offlineDemoMode) {
      runOfflineDemo();
    } else {
      runRealAnalysis();
    }
  });

  async function runRealAnalysis() {
    navigateTo('screen-loading');

    const step2 = document.getElementById('chk-step-2');
    step2.className = 'checklist-row active';

    const formData = new FormData();
    formData.append('file', appState.selectedFile);

    try {
      const res = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Server returned ${res.status}`);
      }

      const data = await res.json();
      step2.className = 'checklist-row done';

      if (data.method_used === 'low_confidence' || !data.disease) {
        document.getElementById('txt-lowconf-desc').textContent =
          data.message || 'Please try another photo with better lighting and the leaf clearly visible.';
        navigateTo('screen-low-confidence');
      } else {
        currentActiveReport = mapApiResponseToReport(data);
        renderDiseaseReport(currentActiveReport);
        navigateTo('screen-result');
      }
    } catch (err) {
      console.error('Prediction request failed:', err);
      document.getElementById('txt-lowconf-heading').textContent = "Couldn't reach the CropCare AI server.";
      document.getElementById('txt-lowconf-desc').textContent =
        `Make sure the backend is running at ${API_BASE_URL} and reachable from this device, then try again.`;
      navigateTo('screen-low-confidence');
    }
  }

  // Converts the backend's PredictionResponse shape into the fields this
  // screen renders. Keep this in sync with backend/app/schemas/prediction.py.
  function mapApiResponseToReport(data) {
    const cropEmoji = {
      Tomato: '🍅', Potato: '🥔', 'Bell Pepper': '🫑'
    }[data.crop] || '🌿';

    let methodNote = '';
    if (data.method_used === 'similarity_fallback') {
      methodNote = 'Matched via reference-image similarity search (backup method), not the primary classifier.';
    } else if (data.method_used === 'classifier') {
      methodNote = 'Identified by the primary trained classifier.';
    }

    return {
      crop: data.crop,
      cropEmoji,
      disease: data.disease,
      scientificName: data.scientific_name,
      severity: data.severity || 'Unknown',
      confidence: Math.round((data.confidence || 0) * 100),
      methodNote,
      symptoms: data.symptoms || [],
      prevention: data.prevention || [],
      organic: data.treatment?.organic || [],
      chemical: data.treatment?.chemical || [],
      safety: data.safety_notes || []
    };
  }

  // ==========================================
  // 5. OFFLINE DEMO PATH (only when dev panel is used)
  // ==========================================
  const DEMO_REPORT = {
    crop: 'Tomato', cropEmoji: '🍅', disease: 'Early Blight',
    scientificName: 'Alternaria solani', severity: 'Moderate', confidence: 87,
    methodNote: 'Offline demo data — not a real prediction.',
    symptoms: ['Brown spots on leaves with concentric ring markings', 'Yellowing around the affected leaf areas'],
    prevention: ['Improve air circulation around plants', 'Avoid overhead watering'],
    organic: ['Copper-based organic spray', 'Neem oil solution (5ml/L)'],
    chemical: ['Mancozeb 75% WP @ 2g/L', 'Chlorothalonil spray'],
    safety: ['This is demo data — always confirm with a real prediction or local expert.']
  };

  function runOfflineDemo() {
    navigateTo('screen-loading');
    setTimeout(() => {
      if (appState.demoOutcome === 'low') {
        document.getElementById('txt-lowconf-desc').textContent =
          'Please try another photo with better lighting and the leaf clearly visible.';
        navigateTo('screen-low-confidence');
      } else {
        currentActiveReport = DEMO_REPORT;
        renderDiseaseReport(currentActiveReport);
        navigateTo('screen-result');
      }
    }, 1200);
  }

  document.getElementById('btn-try-another-photo')?.addEventListener('click', () => navigateTo('screen-scan'));
  document.getElementById('btn-result-another')?.addEventListener('click', () => navigateTo('screen-scan'));

  document.getElementById('btn-save-history')?.addEventListener('click', () => {
    if (currentActiveReport) {
      const entry = {
        ...currentActiveReport,
        id: 'scan-' + Date.now(),
        date: new Date().toLocaleDateString(),
        imgUrl: appState.selectedImageDataUrl
      };
      appState.scanHistory.unshift(entry);
      renderRecentChecks();
      renderHistoryList('all');
    }
    alert('Saved to your Scan History for this session.');
  });

  // ==========================================
  // 6. RENDER DISEASE REPORT
  // ==========================================
  function severityPillClass(sev) {
    switch ((sev || '').toLowerCase()) {
      case 'high': return 'pill-high';
      case 'mild': return 'pill-mild';
      case 'none': return 'pill-none';
      default: return 'pill-moderate';
    }
  }

  function renderDiseaseReport(report) {
    document.getElementById('res-crop-name').textContent = `${report.cropEmoji} ${report.crop}`;
    document.getElementById('res-disease-title').textContent = report.disease;
    document.getElementById('res-scientific-name').textContent = report.scientificName || '';
    document.getElementById('res-confidence-val').textContent = report.confidence + '%';

    const severityBadge = document.getElementById('res-severity-badge');
    severityBadge.textContent = report.severity;
    severityBadge.className = 'severity-pill ' + severityPillClass(report.severity);

    document.getElementById('res-method-note').textContent = report.methodNote || '';

    const gaugePath = document.getElementById('res-confidence-path');
    if (gaugePath) gaugePath.setAttribute('stroke-dasharray', `${report.confidence}, 100`);

    if (appState.selectedImageDataUrl) {
      document.getElementById('img-result-display').src = appState.selectedImageDataUrl;
    }

    fillList('res-symptoms-list', report.symptoms);
    fillList('res-prevention-list', report.prevention);
    fillList('res-organic-list', report.organic);
    fillList('res-chemical-list', report.chemical);
    fillList('res-safety-list', report.safety);
  }

  function fillList(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    (items || []).forEach(text => {
      const li = document.createElement('li');
      li.textContent = text;
      el.appendChild(li);
    });
  }

  // ==========================================
  // 7. VOICE PLAYBACK (speaks the actual result, not a fixed script)
  // ==========================================
  const audioBtn = document.getElementById('btn-listen-hindi');
  audioBtn?.addEventListener('click', () => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported in this browser.');
      return;
    }
    if (appState.isSpeaking) {
      window.speechSynthesis.cancel();
      appState.isSpeaking = false;
      audioBtn.innerHTML = '<span>🔊 Listen in Hindi</span>';
      return;
    }
    if (!currentActiveReport) return;

    const text = `फसल: ${currentActiveReport.crop}. बीमारी: ${currentActiveReport.disease}.`;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'hi-IN';
    utterance.rate = 0.9;
    utterance.onend = () => {
      appState.isSpeaking = false;
      audioBtn.innerHTML = '<span>🔊 Listen in Hindi</span>';
    };
    window.speechSynthesis.speak(utterance);
    appState.isSpeaking = true;
    audioBtn.innerHTML = '<span>⏹️ Stop Audio</span>';
  });

  // ==========================================
  // 8. RECENT CHECKS & HISTORY (session-only, real predictions only)
  // ==========================================
  function renderRecentChecks() {
    const container = document.getElementById('recent-checks-container');
    if (!container) return;
    container.innerHTML = '';

    if (appState.scanHistory.length === 0) {
      container.innerHTML = `<p style="text-align:center; color: var(--muted-text); padding: 12px;">No scans yet this session — tap "Scan Crop" above.</p>`;
      return;
    }

    appState.scanHistory.slice(0, 3).forEach(item => {
      const card = document.createElement('div');
      card.className = 'history-card';
      card.innerHTML = `
        <img src="${item.imgUrl}" class="history-thumb" alt="${item.crop}">
        <div class="history-details">
          <div class="history-crop-title">${item.crop}</div>
          <div class="history-disease-subtitle">${item.disease}</div>
          <div class="history-meta-row">
            <span>${item.date}</span>
            <span class="confidence-pill">${item.confidence}% Match</span>
          </div>
        </div>`;
      card.addEventListener('click', () => {
        currentActiveReport = item;
        appState.selectedImageDataUrl = item.imgUrl;
        renderDiseaseReport(item);
        navigateTo('screen-result');
      });
      container.appendChild(card);
    });
  }

  function renderHistoryList(filter = 'all') {
    const container = document.getElementById('history-items-container');
    if (!container) return;
    container.innerHTML = '';

    const filtered = appState.scanHistory.filter(item => filter === 'all' || item.crop === filter);
    if (filtered.length === 0) {
      container.innerHTML = `<p style="text-align:center; color: var(--muted-text); padding: 20px;">No scans in this category yet.</p>`;
      return;
    }
    filtered.forEach(item => {
      const card = document.createElement('div');
      card.className = 'history-card';
      card.innerHTML = `
        <img src="${item.imgUrl}" class="history-thumb" alt="${item.crop}">
        <div class="history-details">
          <div class="history-crop-title">${item.crop} - ${item.disease}</div>
          <div class="history-disease-subtitle">Severity: ${item.severity}</div>
          <div class="history-meta-row">
            <span>${item.date}</span>
            <span class="confidence-pill">${item.confidence}% Confidence</span>
          </div>
        </div>`;
      card.addEventListener('click', () => {
        currentActiveReport = item;
        appState.selectedImageDataUrl = item.imgUrl;
        renderDiseaseReport(item);
        navigateTo('screen-result');
      });
      container.appendChild(card);
    });
  }

  document.querySelectorAll('.filter-pills-bar .pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-pills-bar .pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderHistoryList(btn.getAttribute('data-filter'));
    });
  });

  // ==========================================
  // 9. WEATHER RISK CARD (optional feature — needs OPENWEATHER_API_KEY)
  // ==========================================
  async function loadWeatherRisk() {
    const headline = document.getElementById('weather-headline');
    const detail = document.getElementById('weather-detail');
    if (!headline || !detail) return;

    if (!OPENWEATHER_API_KEY) {
      headline.textContent = 'Weather risk alerts not configured';
      detail.textContent = 'Add a free OpenWeatherMap API key in js/app.js (OPENWEATHER_API_KEY) to enable this.';
      return;
    }
    if (!navigator.geolocation) {
      headline.textContent = 'Location not available';
      detail.textContent = 'Your browser does not support geolocation.';
      return;
    }

    navigator.geolocation.getCurrentPosition(async pos => {
      try {
        const { latitude, longitude } = pos.coords;
        const url = `https://api.openweathermap.org/data/2.5/weather?lat=${latitude}&lon=${longitude}&units=metric&appid=${OPENWEATHER_API_KEY}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Weather API error');
        const data = await res.json();

        const tempC = data.main?.temp;
        const humidity = data.main?.humidity;
        const condition = data.weather?.[0]?.main || 'Unknown';

        // Simple, transparent heuristic (not a scientific model): most fungal
        // pathogens (blight, mold, leaf spot) favor warm + humid conditions.
        const highRisk = humidity >= 70 && tempC >= 18 && tempC <= 30;

        headline.textContent = `${condition}, ${Math.round(tempC)}°C, ${humidity}% humidity`;
        detail.textContent = highRisk
          ? '⚠️ Warm & humid — favorable conditions for fungal disease spread. Consider a preventive check.'
          : 'Conditions are not currently favorable for rapid fungal disease spread.';
      } catch (err) {
        headline.textContent = 'Could not load weather';
        detail.textContent = 'Check your OpenWeatherMap API key and internet connection.';
      }
    }, () => {
      headline.textContent = 'Location permission denied';
      detail.textContent = 'Enable location access to see a local disease-risk estimate.';
    });
  }
  loadWeatherRisk();

  // ==========================================
  // 10. FARMER SUPPORT DIRECTORY (static demo actions)
  // ==========================================
  document.getElementById('btn-call-helpline')?.addEventListener('click', () => {
    alert('Kisan Call Center Helpline: 1800-180-1551');
  });
  document.getElementById('btn-scheme-info')?.addEventListener('click', () => {
    alert('PM-Kisan Samman Nidhi Scheme Guide (placeholder — link to the real scheme page here)');
  });
  document.getElementById('btn-insurance-info')?.addEventListener('click', () => {
    alert('PMFBY Crop Insurance Guide (placeholder — link to the real scheme page here)');
  });
  document.getElementById('btn-submit-feedback')?.addEventListener('click', () => {
    const text = document.getElementById('feedback-text').value.trim();
    if (!text) { alert('Please type your question before submitting.'); return; }
    document.getElementById('feedback-text').value = '';
    const successBanner = document.getElementById('feedback-success');
    successBanner?.classList.remove('hidden');
    setTimeout(() => successBanner?.classList.add('hidden'), 4000);
  });

  // ==========================================
  // 11. LANGUAGE TOGGLE (label only — extend i18n map as needed)
  // ==========================================
  document.getElementById('header-lang-btn')?.addEventListener('click', () => {
    appState.language = appState.language === 'en' ? 'hi' : 'en';
    document.getElementById('lang-indicator').textContent = appState.language.toUpperCase();
  });

  // ==========================================
  // 12. OFFLINE DEMO PANEL (double-tap logo)
  // ==========================================
  let lastTap = 0;
  const logoEl = document.getElementById('brand-logo');
  const devModal = document.getElementById('dev-modal');

  logoEl?.addEventListener('click', () => {
    const now = Date.now();
    if (now - lastTap < 400) devModal?.classList.remove('hidden');
    lastTap = now;
  });

  document.getElementById('btn-close-dev')?.addEventListener('click', () => devModal?.classList.add('hidden'));
  document.getElementById('btn-dev-sim-high')?.addEventListener('click', () => {
    appState.offlineDemoMode = true;
    appState.demoOutcome = 'high';
    devModal?.classList.add('hidden');
    alert('Offline demo mode ON: next scan will show a sample confident result instead of calling the backend.');
  });
  document.getElementById('btn-dev-sim-low')?.addEventListener('click', () => {
    appState.offlineDemoMode = true;
    appState.demoOutcome = 'low';
    devModal?.classList.add('hidden');
    alert('Offline demo mode ON: next scan will show a sample low-confidence result instead of calling the backend.');
  });

  // Initial renders
  renderRecentChecks();
  renderHistoryList('all');
});
