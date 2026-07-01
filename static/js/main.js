document.addEventListener('DOMContentLoaded', () => {
    // Add page-loaded class to body for entrance animation
    document.body.classList.add('page-loaded');

    // Page Exit Transition Link Handler
    const navLinks = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="javascript"])');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const destination = link.href;
            if (destination && !e.metaKey && !e.ctrlKey) {
                e.preventDefault();
                document.body.classList.add('page-exit');
                setTimeout(() => {
                    window.location.href = destination;
                }, 250); // Syncs with css fade time
            }
        });
    });

    // Radial Cursor Tracker Glow for Premium feel
    const interactiveCards = document.querySelectorAll('.glass-container, .job-card');
    interactiveCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });

    // Circular Score Ring Animation & Incremental Counter
    const scoreValEl = document.querySelector('.score-value');
    const scoreCircle = document.querySelector('.score-circle');
    
    if (scoreValEl && scoreCircle) {
        const targetVal = parseInt(scoreValEl.textContent);
        if (!isNaN(targetVal)) {
            let currentVal = 0;
            const duration = 1000; // Total count time in ms
            const stepTime = Math.max(Math.floor(duration / targetVal), 10);
            
            // Set initial state
            scoreValEl.innerHTML = `0<span style="font-size: 1.5rem; font-weight: 500;">%</span>`;
            
            const timer = setInterval(() => {
                currentVal += 1;
                
                // Update text percentage
                scoreValEl.innerHTML = `${currentVal}<span style="font-size: 1.5rem; font-weight: 500;">%</span>`;
                
                // Draw circular ring conic gradient
                scoreCircle.style.background = `conic-gradient(var(--secondary) 0%, var(--primary) ${currentVal}%, var(--border-glass) ${currentVal}%, var(--border-glass) 100%)`;
                
                if (currentVal >= targetVal) {
                    clearInterval(timer);
                }
            }, stepTime);
        }
    }

    // Drag and Drop Logic
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const loadingOverlay = document.getElementById('loading-overlay');
    const fileLabel = document.getElementById('file-label');
    const uploadForm = document.getElementById('upload-form');

    if (uploadZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove('dragover');
            }, false);
        });

        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });

        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleFileSelect(fileInput.files[0]);
            }
        });

        function handleFileSelect(file) {
            if (file.type !== 'application/pdf') {
                alert('Only PDF resumes are supported.');
                fileInput.value = '';
                return;
            }
            
            fileLabel.innerHTML = `Selected File: <strong>${file.name}</strong>`;
            
            if (uploadForm) {
                loadingOverlay.classList.add('active');
                uploadForm.submit();
            }
        }
    }

    // Direct Form Submit loader trigger
    const formsWithLoader = document.querySelectorAll('.form-trigger-loader');
    formsWithLoader.forEach(form => {
        form.addEventListener('submit', () => {
            if (loadingOverlay) {
                loadingOverlay.classList.add('active');
            }
        });
    });

    // Web Speech API Voice Note for AI Guidance (with toggle player)
    const speakBtn = document.getElementById('speak-btn');
    const adviceTextEl = document.getElementById('advice-text');
    
    if (speakBtn && adviceTextEl) {
        const welcomeMessage = "Thank you for using ResumeAI! Your resume analysis report is ready.";
        const fullMessage = welcomeMessage + " " + adviceTextEl.innerText;
        
        let isSpeaking = false;
        
        function speakReport() {
            if ('speechSynthesis' in window) {
                if (isSpeaking) {
                    window.speechSynthesis.cancel();
                    speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> Listen to AI`;
                    isSpeaking = false;
                } else {
                    const utterance = new SpeechSynthesisUtterance(fullMessage);
                    
                    // Setup voice configurations
                    const voices = window.speechSynthesis.getVoices();
                    const cleanVoice = voices.find(voice => 
                        voice.name.includes('Google US English') || 
                        voice.name.includes('Microsoft David') || 
                        voice.name.includes('Natural')
                    );
                    if (cleanVoice) utterance.voice = cleanVoice;
                    
                    utterance.rate = 1.0;
                    utterance.pitch = 1.02;
                    
                    utterance.onend = () => {
                        speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> Listen to AI`;
                        isSpeaking = false;
                    };
                    
                    utterance.onerror = () => {
                        speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> Listen to AI`;
                        isSpeaking = false;
                    };
                    
                    speakBtn.innerHTML = `<i class="fa-solid fa-circle-stop" style="color: var(--accent);"></i> Stop Listening`;
                    isSpeaking = true;
                    window.speechSynthesis.speak(utterance);
                }
            } else {
                console.log("Text-to-speech is not supported on this browser.");
            }
        }
        
        speakBtn.addEventListener('click', speakReport);
        
        // Auto-run speech note on page load (if allowed by browser autoplay policies)
        setTimeout(() => {
            speakReport();
        }, 1500); // 1.5s delay to let page entrance animation complete first
    }
});
