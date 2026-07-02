document.addEventListener('DOMContentLoaded', () => {
    // 1. 3D Perspective Card mouse tilt animation
    const tiltCards = document.querySelectorAll('.tilt-card');
    tiltCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((centerY - y) / centerY) * 10;
            const rotateY = ((x - centerX) / centerX) * 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        });
        
        card.style.transition = 'transform 0.1s ease, box-shadow 0.35s ease';
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    });

    // 2. Text-to-Speech (TTS) Announcements with English Female Voice
    function speakText(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.getVoices(); // Preload
            const msg = new SpeechSynthesisUtterance(text);
            const voices = window.speechSynthesis.getVoices();
            const femaleVoice = voices.find(v => {
                const name = v.name.toLowerCase();
                return v.lang.startsWith('en') && (name.includes('female') || name.includes('zira') || name.includes('google us english') || name.includes('google uk english female') || name.includes('natural'));
            });
            if (femaleVoice) {
                msg.voice = femaleVoice;
            }
            msg.rate = 0.95;
            msg.pitch = 1.1;
            window.speechSynthesis.speak(msg);
        }
    }

    // TTS welcome on landing screen
    const isLoginPage = window.location.pathname === '/login' || window.location.pathname === '/';
    if (isLoginPage) {
        const welcomeTrigger = () => {
            if (window.hasWelcomeSpoken) return;
            window.hasWelcomeSpoken = true;
            speakText("Welcome to ResumeAI! Please log in or register to analyze your resume.");
        };
        document.addEventListener('click', welcomeTrigger, { once: true });
        document.addEventListener('mouseover', welcomeTrigger, { once: true });
    }

    // TTS thanks on report screen
    const isReportPage = window.location.pathname.startsWith('/analyze/');
    if (isReportPage) {
        const thanksTrigger = () => {
            if (window.hasThanksSpoken) return;
            window.hasThanksSpoken = true;
            speakText("Thank you for using this site! Your resume analysis is complete. You can view your match score, missing skills, and apply to recommended companies below.");
        };
        document.addEventListener('click', thanksTrigger, { once: true });
        document.addEventListener('mouseover', thanksTrigger, { once: true });
    }

    // 3. WebRTC Biometric Face Scan Overlay Simulator
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            // Check if file is uploaded
            const fileInput = document.getElementById('file-input');
            if (!fileInput || fileInput.files.length === 0) {
                return; // Let standard required validation catch it
            }
            
            e.preventDefault(); // Intercept submit to scan face first
            
            // Create biometric overlay HTML programmatically
            const overlay = document.createElement('div');
            overlay.className = 'biometric-overlay';
            overlay.innerHTML = `
                <div class="biometric-scanner-box">
                    <h2 class="form-title" style="font-size: 1.6rem; color: #ffffff;"><i class="fa-solid fa-face-viewfinder"></i> Biometric Scan</h2>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 5px;">Holographic Face Scan Verification in progress</p>
                    
                    <div class="biometric-video-container">
                        <div class="biometric-laser"></div>
                        <video id="biometric-video" autoplay playsinline class="biometric-video"></video>
                    </div>
                    
                    <p id="biometric-status" style="font-weight: 600; font-size: 0.95rem; color: #ffffff; letter-spacing: 0.5px;">INITIALIZING WEBCAM...</p>
                </div>
            `;
            document.body.appendChild(overlay);
            
            const videoElement = document.getElementById('biometric-video');
            const statusElement = document.getElementById('biometric-status');
            let streamRef = null;

            // Start webcam
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: true, audio: false })
                    .then((stream) => {
                        streamRef = stream;
                        videoElement.srcObject = stream;
                        statusElement.innerText = "SCANNING FACE PROFILE...";
                        speakText("Biometric verification in progress.");
                        
                        // Wait 3.5 seconds to simulate verification scan
                        setTimeout(() => {
                            statusElement.innerText = "AUTHENTICATION SUCCESSFUL! ACCESS GRANTED.";
                            statusElement.style.color = "#22c55e";
                            speakText("Face verified. Access granted, welcome!");
                            
                            // 1 second buffer before submitting form
                            setTimeout(() => {
                                // Turn off webcam
                                if (streamRef) {
                                    streamRef.getTracks().forEach(track => track.stop());
                                }
                                document.body.removeChild(overlay);
                                uploadForm.submit(); // submit form
                            }, 1500);
                        }, 3500);
                    })
                    .catch((err) => {
                        console.log("Webcam error or denied: ", err);
                        statusElement.innerText = "WEBCAM ACCESS DENIED. SKIP SCANNING.";
                        statusElement.style.color = "#ef4444";
                        
                        // Auto-skip face scan if camera is missing/denied so user doesn't get blocked
                        setTimeout(() => {
                            document.body.removeChild(overlay);
                            uploadForm.submit();
                        }, 2000);
                    });
            } else {
                // Browser does not support getUserMedia
                document.body.removeChild(overlay);
                uploadForm.submit();
            }
        });
    }

    // 4. Web Speech Voice Assistant Commands Recognizer
    const micBtn = document.getElementById('voice-hud-mic');
    if (micBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            
            micBtn.addEventListener('click', () => {
                if (micBtn.classList.contains('listening')) {
                    recognition.stop();
                } else {
                    micBtn.classList.add('listening');
                    speakText("Listening, say command");
                    recognition.start();
                }
            });
            
            recognition.onresult = (event) => {
                const command = event.results[0][0].transcript.toLowerCase().trim();
                console.log("Speech Recognition Command: ", command);
                
                if (command.includes('register')) {
                    speakText("Redirecting to register page.");
                    setTimeout(() => window.location.href = '/register', 1200);
                } else if (command.includes('login') || command.includes('sign in')) {
                    speakText("Redirecting to login page.");
                    setTimeout(() => window.location.href = '/login', 1200);
                } else if (command.includes('upload') || command.includes('scan')) {
                    speakText("Opening resume upload page.");
                    setTimeout(() => window.location.href = '/upload', 1200);
                } else if (command.includes('about') || command.includes('developer')) {
                    speakText("Opening developer information and profile page.");
                    setTimeout(() => window.location.href = '/about', 1200);
                } else if (command.includes('tracker') || command.includes('application')) {
                    speakText("Opening resume applications tracker.");
                    setTimeout(() => window.location.href = '/tracker', 1200);
                } else if (command.includes('guide') || command.includes('blueprint')) {
                    speakText("Opening interactive resume guide blueprint.");
                    setTimeout(() => window.location.href = '/guide', 1200);
                } else if (command.includes('logout') || command.includes('sign out')) {
                    speakText("Logging you out.");
                    setTimeout(() => window.location.href = '/logout', 1200);
                } else {
                    speakText("Command not recognized. Say register, login, upload, tracker, guide, or about.");
                }
            };
            
            recognition.onspeechend = () => {
                recognition.stop();
            };
            
            recognition.onend = () => {
                micBtn.classList.remove('listening');
            };
            
            recognition.onerror = (e) => {
                console.log("Speech Recognition Error: ", e);
                micBtn.classList.remove('listening');
            };
        } else {
            // Speech Recognition not supported in browser
            micBtn.style.display = 'none';
        }
    }

    // 5. Drag & Drop Upload Zone helper
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.getElementById('file-label');
    
    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileLabel.innerText = `Selected File: ${fileInput.files[0].name}`;
            }
        });
        
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--primary)';
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.style.borderColor = 'var(--border-glass)';
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                fileLabel.innerText = `Dropped File: ${fileInput.files[0].name}`;
            }
        });
    }
});
