/**
 * CropCare AI - Smartphone Crop Disease Detection & Farmer Support System
 * Frontend Application Logic (Review 1 Prototype)
 */

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. APPLICATION STATE
    // ==========================================
    const appState = {
        currentScreen: 'screen-home',
        language: 'en', // 'en' | 'hi'
        selectedFile: null,
        selectedImageDataUrl: null,
        simulationOutcome: 'high', // 'high' | 'low' (Developer controlled)
        isSpeaking: false,
        
        // Demo Scan History Data (Pre-populated for Review 1 demonstration)
        scanHistory: [
            {
                id: 'scan-101',
                crop: 'Tomato',
                disease: 'Early Blight',
                date: 'Sep 08, 2026',
                confidence: 87,
                severity: 'Moderate',
                imgUrl: 'https://images.unsplash.com/photo-1592417817098-8f3d6eb231fc?auto=format&fit=crop&w=300&q=80',
                symptoms: [
                    'Brown spots on leaves with concentric ring markings',
                    'Yellowing around the affected leaf areas',
                    'Lower leaves turning dark and dropping prematurely'
                ],
                prevention: [
                    'Improve air circulation around plants',
                    'Avoid overhead watering; water at soil level',
                    'Rotate crops regularly'
                ],
                organic: [
                    'Copper-based organic spray',
                    'Neem oil solution (5ml/L)',
                    'Prune infected leaves'
                ],
                chemical: [
                    'Mancozeb 75% WP @ 2g/L',
                    'Chlorothalonil spray',
                    'Repeat after 12 days'
                ],
                safety: 'Follow product label instructions carefully. Wear protective equipment (mask, gloves) when applying sprays.'
            },
            {
                id: 'scan-102',
                crop: 'Potato',
                disease: 'Late Blight',
                date: 'Sep 05, 2026',
                confidence: 91,
                severity: 'High',
                imgUrl: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=300&q=80',
                symptoms: [
                    'Water-soaked dark lesions on leaf tips',
                    'White fungal growth on leaf undersides in high humidity',
                    'Rapid rotting of leaves and stems'
                ],
                prevention: [
                    'Plant certified disease-free potato seed tubers',
                    'Destroy volunteer potato plants around the field',
                    'Improve soil drainage and avoid standing water'
                ],
                organic: [
                    'Bordeaux mixture (1%) spray',
                    'Trichoderma viride bio-spray'
                ],
                chemical: [
                    'Cymoxanil + Mancozeb @ 2g/L',
                    'Metalaxyl-M systemic fungicide'
                ],
                safety: 'Do not harvest crops within 14 days of spraying. Wash hands thoroughly after handling.'
            },
            {
                id: 'scan-103',
                crop: 'Wheat',
                disease: 'Leaf Rust',
                date: 'Aug 28, 2026',
                confidence: 84,
                severity: 'Mild',
                imgUrl: 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=300&q=80',
                symptoms: [
                    'Small orange-red pustules scattered on upper leaf surface',
                    'Dusty orange powder releasing from leaves when touched'
                ],
                prevention: [
                    'Grow rust-resistant wheat varieties',
                    'Avoid excess nitrogen fertilizer application'
                ],
                organic: [
                    'Cow urine & sour buttermilk spray',
                    'Sulfur-based dust application'
                ],
                chemical: [
                    'Propiconazole 25% EC @ 1ml/L'
                ],
                safety: 'Use protective eyewear and nose mask during sulfur dusting.'
            }
        ]
    };

    // Active Report Data (Default: Tomato Early Blight)
    let currentActiveReport = { ...appState.scanHistory[0] };

    // ==========================================
    // 2. DICTIONARY (English & Hindi Translations)
    // ==========================================
    const i18n = {
        en: {
            greeting: 'Namaste, Farmer 👋',
            subgreeting: "Let's keep your crops healthy.",
            heroTitle: 'Analyze Your Crop',
            heroDesc: 'Take a photo of a crop leaf and let CropCare AI help identify possible diseases.',
            ctaAnalyze: 'Scan Crop →',
            quickActions: 'Quick Actions',
            qaScan: 'Scan',
            qaHistory: 'History',
            qaSupport: 'Support',
            recentChecks: 'Recent Checks',

            scanTitle: 'Check Your Crop',
            scanSub: 'Take a clear photo of the affected leaf.',
            uploadHeading: 'Tap to upload or take a photo',
            uploadSubtext: 'JPG · PNG · WEBP · Max 10MB',
            btnCamera: 'Take Photo',
            btnGallery: 'Upload from Gallery',
            tipsTitle: '💡 For better results',
            tip1: 'Use good lighting',
            tip2: 'Keep the leaf clearly visible',
            tip3: 'Avoid blurry photos',
            tip4: 'Focus on the affected area',

            previewTitle: 'Review Your Photo',
            previewSub: 'Check if the leaf is clearly visible.',
            btnAnalyzeLeaf: '🌿 Analyze Leaf →',
            btnChooseAnother: 'Choose Another',

            loadingTitle: 'Analyzing your crop...',
            loadingSub: 'Our AI is examining the leaf for possible diseases.',
            chk1: 'Image quality checked',
            chk2: 'Crop image processed',
            chk3: 'Detecting possible disease...',

            reportTitle: 'Crop Health Report',
            btnAudio: '🔊 Listen in Hindi',
            symptomsTitle: '🌿 Symptoms',
            preventionTitle: '🛡 Prevention',
            treatmentTitle: '🌱 Treatment Options',
            safetyTitle: 'Safety Information',
            btnAnalyzeAnother: 'Analyze Another Leaf',
            btnSave: 'Save to History ✓',

            lowconfTitle: 'Unclear Photo',
            lowconfHeading: "We couldn't identify the disease confidently.",
            lowconfDesc: 'Please try another photo with better lighting and the leaf clearly visible.',
            lcTip1: 'Good lighting',
            lcTip2: 'Leaf clearly visible',
            lcTip3: 'Avoid blurry images',
            btnRetry: '📷 Try Another Photo',

            historyTitle: 'Scan History',
            historySub: 'Previous crop checks saved on your device',

            supportTitle: 'Farmer Support',
            supportSub: 'Helplines, schemes, and agricultural assistance',
            supHelplineTitle: 'Agricultural Helplines',

            navHome: 'Home',
            navHistory: 'History',
            navScan: 'Scan',
            navSupport: 'Support'
        },
        hi: {
            greeting: 'नमस्ते, किसान भाई 👋',
            subgreeting: 'आइए आपकी फसलों को स्वस्थ रखें।',
            heroTitle: 'अपनी फसल की जांच करें',
            heroDesc: 'संक्रमित पत्ते की फोटो लें और बीमारी की तुरंत पहचान पाएं।',
            ctaAnalyze: 'स्कैन शुरू करें →',
            quickActions: 'त्वरित विकल्प',
            qaScan: 'स्कैन',
            qaHistory: 'इतिहास',
            qaSupport: 'सहायता',
            recentChecks: 'हाल की जांचें',

            scanTitle: 'फसल की जांच करें',
            scanSub: 'प्रभावित पत्ते की एक स्पष्ट तस्वीर लें।',
            uploadHeading: 'फोटो चुनने के लिए टैप करें',
            uploadSubtext: 'JPG · PNG · WEBP · अधिकतम 10MB',
            btnCamera: 'फोटो खींचें',
            btnGallery: 'गैलरी से अपलोड करें',
            tipsTitle: '💡 बेहतर परिणाम के लिए',
            tip1: 'अच्छी रोशनी का उपयोग करें',
            tip2: 'पत्ते को स्पष्ट रखें',
            tip3: 'धुंधली फोटो से बचें',
            tip4: 'प्रभावित हिस्से पर ध्यान दें',

            previewTitle: 'अपनी फोटो जांचें',
            previewSub: 'देखें कि क्या पत्ता स्पष्ट दिखाई दे रहा है।',
            btnAnalyzeLeaf: '🌿 जांच शुरू करें →',
            btnChooseAnother: 'दूसरी फोटो चुनें',

            loadingTitle: 'आपकी फसल की जांच की जा रही है...',
            loadingSub: 'हमारा AI संभव बीमारियों की जांच कर रहा है।',
            chk1: 'फोटो गुणवत्ता जांच की गई',
            chk2: 'पत्ते की फोटो संसाधित की गई',
            chk3: 'संभावित बीमारी की पहचान की जा रही है...',

            reportTitle: 'फसल स्वास्थ्य रिपोर्ट',
            btnAudio: '🔊 हिंदी में सुनें',
            symptomsTitle: '🌿 बीमारी के लक्षण',
            preventionTitle: '🛡 बचाव के उपाय',
            treatmentTitle: '🌱 उपचार के विकल्प',
            safetyTitle: 'सुरक्षा निर्देश',
            btnAnalyzeAnother: 'दूसरे पत्ते की जांच करें',
            btnSave: 'इतिहास में सहेजा गया ✓',

            lowconfTitle: 'अस्पष्ट फोटो',
            lowconfHeading: 'हम बीमारी की स्पष्ट पहचान नहीं कर सके।',
            lowconfDesc: 'कृपया अच्छी रोशनी में और पत्ते को स्पष्ट रखते हुए दूसरी फोटो लें।',
            lcTip1: 'अच्छी रोशनी',
            lcTip2: 'पत्ता स्पष्ट दिखाई दे रहा है',
            lcTip3: 'धुंधली फोटो से बचें',
            btnRetry: '📷 दूसरी फोटो खींचें',

            historyTitle: 'जांच इतिहास',
            historySub: 'आपकी पिछली फसल जांच की सूची',

            supportTitle: 'किसान सहायता',
            supportSub: 'हेल्पलाइन, सरकारी योजनाएं और कृषि सहायता',
            supHelplineTitle: 'कृषि हेल्पलाइन',

            navHome: 'होम',
            navHistory: 'इतिहास',
            navScan: 'स्कैन',
            navSupport: 'सहायता'
        }
    };

    // ==========================================
    // 3. NAVIGATION CONTROLLER
    // ==========================================
    function navigateTo(screenId) {
        const screens = document.querySelectorAll('.screen');
        screens.forEach(s => s.classList.remove('active'));

        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
            appState.currentScreen = screenId;
        }

        // Update Bottom Nav active state
        const navItems = document.querySelectorAll('.bottom-nav .nav-item');
        navItems.forEach(item => {
            if (item.getAttribute('data-screen') === screenId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Scroll content to top
        const contentArea = document.querySelector('.app-content');
        if (contentArea) contentArea.scrollTop = 0;
    }

    // Attach Click Handlers to Bottom Nav
    document.querySelectorAll('.bottom-nav .nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const screenId = btn.getAttribute('data-screen');
            if (screenId) navigateTo(screenId);
        });
    });

    // Back Buttons
    document.getElementById('btn-scan-back').addEventListener('click', () => navigateTo('screen-home'));
    document.getElementById('btn-preview-back').addEventListener('click', () => navigateTo('screen-scan'));
    document.getElementById('btn-result-home').addEventListener('click', () => navigateTo('screen-home'));
    document.getElementById('btn-lowconf-back').addEventListener('click', () => navigateTo('screen-scan'));

    // Home Quick Actions
    document.getElementById('btn-hero-analyze').addEventListener('click', () => navigateTo('screen-scan'));
    document.getElementById('qa-scan').addEventListener('click', () => navigateTo('screen-scan'));
    document.getElementById('qa-history').addEventListener('click', () => navigateTo('screen-history'));
    document.getElementById('qa-support').addEventListener('click', () => navigateTo('screen-support'));
    document.getElementById('btn-view-all-history').addEventListener('click', () => navigateTo('screen-history'));

    // ==========================================
    // 4. IMAGE UPLOAD & VALIDATION LOGIC
    // ==========================================
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('leaf-input-file');
    const cameraInput = document.getElementById('leaf-input-camera');

    document.getElementById('btn-trigger-gallery').addEventListener('click', () => fileInput.click());
    document.getElementById('btn-trigger-camera').addEventListener('click', () => cameraInput.click());
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    cameraInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    function handleSelectedFile(file) {
        const errorBanner = document.getElementById('preview-error-banner');
        errorBanner.classList.add('hidden');

        // 1. Validate File Format
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type.toLowerCase())) {
            showPreviewError('Invalid format! Please upload a JPG, PNG, or WEBP image.');
            return;
        }

        // 2. Validate File Size (<= 10 MB)
        const maxSizeInBytes = 10 * 1024 * 1024;
        if (file.size > maxSizeInBytes) {
            showPreviewError('File size exceeds 10 MB limit. Please choose a smaller photo.');
            return;
        }

        appState.selectedFile = file;

        // Metadata display
        document.getElementById('file-name-disp').textContent = file.name;
        document.getElementById('file-size-disp').textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB · ' + file.type.split('/')[1].toUpperCase();

        const reader = new FileReader();
        reader.onload = function (e) {
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

    document.getElementById('btn-reselect-image').addEventListener('click', () => {
        fileInput.value = '';
        cameraInput.value = '';
        appState.selectedFile = null;
        appState.selectedImageDataUrl = null;
        navigateTo('screen-scan');
    });

    // ==========================================
    // 5. SIMULATED AI ANALYSIS FLOW
    // ==========================================
    document.getElementById('btn-confirm-analyze').addEventListener('click', () => {
        startAnalysisSimulation();
    });

    function startAnalysisSimulation() {
        navigateTo('screen-loading');

        const step1 = document.getElementById('chk-step-1');
        const step2 = document.getElementById('chk-step-2');
        const step3 = document.getElementById('chk-step-3');

        step1.className = 'checklist-row done';
        step2.className = 'checklist-row active';
        step3.className = 'checklist-row';

        setTimeout(() => {
            step2.className = 'checklist-row done';
            step3.className = 'checklist-row active';
        }, 1200);

        setTimeout(() => {
            step3.className = 'checklist-row done';

            if (appState.simulationOutcome === 'low') {
                navigateTo('screen-low-confidence');
            } else {
                renderDiseaseReport(currentActiveReport);
                navigateTo('screen-result');
            }
        }, 2600);
    }

    document.getElementById('btn-try-another-photo').addEventListener('click', () => navigateTo('screen-scan'));
    document.getElementById('btn-result-another').addEventListener('click', () => navigateTo('screen-scan'));

    document.getElementById('btn-save-history').addEventListener('click', () => {
        if (appState.selectedImageDataUrl) {
            const newEntry = {
                id: 'scan-' + Date.now(),
                crop: currentActiveReport.crop,
                disease: currentActiveReport.disease,
                date: 'Just now',
                confidence: currentActiveReport.confidence,
                severity: currentActiveReport.severity,
                imgUrl: appState.selectedImageDataUrl
            };
            appState.scanHistory.unshift(newEntry);
            renderRecentChecks();
            renderHistoryList('all');
        }
        alert('Report saved to your Scan History!');
    });

    // ==========================================
    // 6. DISEASE REPORT RENDERER
    // ==========================================
    function renderDiseaseReport(report) {
        document.getElementById('res-crop-name').textContent = '🍅 ' + report.crop;
        document.getElementById('res-disease-title').textContent = report.disease;
        document.getElementById('res-confidence-val').textContent = report.confidence + '%';
        document.getElementById('res-severity-badge').textContent = report.severity;

        const gaugePath = document.getElementById('res-confidence-path');
        if (gaugePath) {
            gaugePath.setAttribute('stroke-dasharray', `${report.confidence}, 100`);
        }

        if (appState.selectedImageDataUrl) {
            document.getElementById('img-result-display').src = appState.selectedImageDataUrl;
        }

        // Render Symptoms
        const sList = document.getElementById('res-symptoms-list');
        sList.innerHTML = '';
        report.symptoms.forEach(sym => {
            const li = document.createElement('li');
            li.textContent = sym;
            sList.appendChild(li);
        });

        // Render Prevention
        const pList = document.getElementById('res-prevention-list');
        pList.innerHTML
