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

    // Google Sign-In Mock Popup Overlay
    const googleLoginBtn = document.getElementById('google-login-btn');
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener('click', () => {
            // Redirect to real Google OAuth if configured
            if (window.GOOGLE_CLIENT_ID && window.GOOGLE_CLIENT_ID.trim() !== "") {
                window.location.href = "/login/google";
                return;
            }
            
            // Create a styled backdrop overlay
            const overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.background = 'rgba(0, 0, 0, 0.7)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '9999';
            overlay.style.backdropFilter = 'blur(10px)';
            
            // Create Google accounts modal
            const modal = document.createElement('div');
            modal.style.background = '#ffffff';
            modal.style.color = '#3c4043';
            modal.style.borderRadius = '8px';
            modal.style.padding = '40px 35px';
            modal.style.width = '100%';
            modal.style.maxWidth = '440px';
            modal.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.3)';
            modal.style.fontFamily = '"Roboto", "Arial", sans-serif';
            modal.style.textAlign = 'center';
            modal.style.boxSizing = 'border-box';
            
            modal.innerHTML = `
                <div id="google-account-chooser" style="display: block; width: 100%;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" alt="Google logo" style="height: 24px; margin-bottom: 20px;">
                    <h3 style="font-size: 1.45rem; font-weight: 400; margin-bottom: 5px; color: #202124; font-family: 'Roboto', sans-serif;">Choose an account</h3>
                    <p style="font-size: 0.95rem; color: #202124; margin-bottom: 25px;">to continue to <span style="font-weight: 600;">ResumeAI</span></p>
                    
                    <!-- Account List -->
                    <div style="display: flex; flex-direction: column; gap: 2px; margin-bottom: 20px; text-align: left; border-top: 1px solid #dadce0;">
                        <!-- Option 1 -->
                        <div class="google-acc-opt" data-email="dhanushravi1485@gmail.com" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #dadce0; cursor: pointer; transition: background 0.2s; background: transparent;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: #a855f7; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0;">D</div>
                            <div>
                                <div style="font-weight: 600; font-size: 0.85rem; color: #3c4043; line-height: 1.2;">Dhanush Ravi</div>
                                <div style="font-size: 0.75rem; color: #5f6368; line-height: 1.2;">dhanushravi1485@gmail.com</div>
                            </div>
                        </div>
                        
                        <!-- Option 2 -->
                        <div class="google-acc-opt" data-email="dhanushravi1735@gmail.com" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #dadce0; cursor: pointer; transition: background 0.2s; background: transparent;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: #ec4899; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0;">D</div>
                            <div>
                                <div style="font-weight: 600; font-size: 0.85rem; color: #3c4043; line-height: 1.2;">Dhanush Ravi</div>
                                <div style="font-size: 0.75rem; color: #5f6368; line-height: 1.2;">dhanushravi1735@gmail.com</div>
                            </div>
                        </div>

                        <!-- Use another account -->
                        <div id="google-use-another-btn" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #dadce0; cursor: pointer; transition: background 0.2s; background: transparent;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: transparent; border: 1px solid #dadce0; color: #5f6368; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i class="fa-regular fa-user" style="font-size: 0.85rem;"></i>
                            </div>
                            <div style="font-weight: 600; font-size: 0.85rem; color: #3c4043;">Use another account</div>
                        </div>
                    </div>

                    <p style="font-size: 0.72rem; color: #5f6368; line-height: 1.4; text-align: left; margin-bottom: 30px; margin-top: 15px;">
                        To continue, Google will share your name, email address, language preference, and profile picture with ResumeAI. Before using this app, you can review ResumeAI's <span style="color: #1a73e8; cursor: pointer; text-decoration: none;">privacy policy</span> and <span style="color: #1a73e8; cursor: pointer; text-decoration: none;">terms of service</span>.
                    </p>
                    
                    <div style="text-align: right; width: 100%;">
                        <button id="google-popup-close-chooser" style="background: transparent; border: none; color: #1a73e8; font-weight: 500; font-size: 0.9rem; cursor: pointer; padding: 10px 20px; transition: background 0.2s;">Cancel</button>
                    </div>
                </div>

                <div id="google-custom-signin-view" style="display: none; width: 100%;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" alt="Google logo" style="height: 24px; margin-bottom: 15px;">
                    <h3 style="font-size: 1.45rem; font-weight: 400; margin-bottom: 5px; color: #202124; font-family: 'Roboto', sans-serif;">Sign in</h3>
                    <p style="font-size: 0.95rem; color: #202124; margin-bottom: 25px;">with your Google Account</p>
                    
                    <!-- Custom Email Input -->
                    <div style="text-align: left; margin-bottom: 20px; width: 100%;">
                        <input type="email" id="google-custom-email" style="width: 100%; padding: 14px 12px; border: 1px solid #dadce0; border-radius: 4px; font-size: 1rem; box-sizing: border-box; outline: none; transition: border-color 0.2s;" placeholder="Email or phone">
                        <p id="google-error-msg" style="color: #d93025; font-size: 0.8rem; margin-top: 6px; display: none; font-weight: 500;"><i class="fa-solid fa-circle-exclamation"></i> Enter a valid email address</p>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 30px;">
                        <button id="google-popup-back" style="background: transparent; border: none; color: #1a73e8; font-weight: 500; font-size: 0.9rem; cursor: pointer; padding: 10px 0;">Back</button>
                        <button id="google-popup-signin" style="background: #1a73e8; color: #ffffff; border: none; padding: 10px 24px; border-radius: 4px; font-weight: 500; font-size: 0.9rem; cursor: pointer; transition: background 0.2s;">Next</button>
                    </div>
                </div>
            `;
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            const chooserView = modal.querySelector('#google-account-chooser');
            const customView = modal.querySelector('#google-custom-signin-view');
            
            const emailInput = modal.querySelector('#google-custom-email');
            const signinBtn = modal.querySelector('#google-popup-signin');
            const errorMsg = modal.querySelector('#google-error-msg');
            const useAnotherBtn = modal.querySelector('#google-use-another-btn');
            const backBtn = modal.querySelector('#google-popup-back');
            
            // Toggle Views
            useAnotherBtn.addEventListener('click', () => {
                chooserView.style.display = 'none';
                customView.style.display = 'block';
                setTimeout(() => emailInput.focus(), 100);
            });
            
            backBtn.addEventListener('click', () => {
                customView.style.display = 'none';
                chooserView.style.display = 'block';
                errorMsg.style.display = 'none';
                emailInput.style.borderColor = '#dadce0';
            });
            
            // Hover styles for account selections
            const options = modal.querySelectorAll('.google-acc-opt');
            options.forEach(opt => {
                opt.addEventListener('mouseenter', () => opt.style.background = '#f7f8f8');
                opt.addEventListener('mouseleave', () => opt.style.background = 'transparent');
                
                opt.addEventListener('click', () => {
                    const selectedEmail = opt.getAttribute('data-email');
                    window.location.href = `/login/google-mock?email=${encodeURIComponent(selectedEmail)}`;
                });
            });
            
            // Hover styles for "Use another account"
            useAnotherBtn.addEventListener('mouseenter', () => useAnotherBtn.style.background = '#f7f8f8');
            useAnotherBtn.addEventListener('mouseleave', () => useAnotherBtn.style.background = 'transparent');
            
            // Blue outline focus border for input
            emailInput.addEventListener('focus', () => emailInput.style.borderColor = '#1a73e8');
            emailInput.addEventListener('blur', () => emailInput.style.borderColor = '#dadce0');
            
            // Hover styles for buttons
            signinBtn.addEventListener('mouseenter', () => signinBtn.style.background = '#1557b0');
            signinBtn.addEventListener('mouseleave', () => signinBtn.style.background = '#1a73e8');
            
            function handleGoogleSignIn() {
                const emailVal = emailInput.value.trim();
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                
                if (!emailVal || !emailRegex.test(emailVal)) {
                    errorMsg.style.display = 'block';
                    emailInput.style.borderColor = '#d93025';
                    return;
                }
                
                errorMsg.style.display = 'none';
                emailInput.style.borderColor = '#1a73e8';
                
                // Redirect to mock route with customized email
                window.location.href = `/login/google-mock?email=${encodeURIComponent(emailVal)}`;
            }
            
            signinBtn.addEventListener('click', handleGoogleSignIn);
            emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleGoogleSignIn();
                }
            });
            
            // Close handlers
            modal.querySelector('#google-popup-close-chooser').addEventListener('click', () => {
                document.body.removeChild(overlay);
            });
        });
    }

    // Facebook Sign-In Mock Popup Overlay
    const facebookLoginBtn = document.getElementById('facebook-login-btn');
    if (facebookLoginBtn) {
        facebookLoginBtn.addEventListener('click', () => {
            const overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.background = 'rgba(0, 0, 0, 0.7)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '9999';
            overlay.style.backdropFilter = 'blur(10px)';
            
            const modal = document.createElement('div');
            modal.style.background = '#ffffff';
            modal.style.color = '#3c4043';
            modal.style.borderRadius = '8px';
            modal.style.padding = '40px 35px';
            modal.style.width = '100%';
            modal.style.maxWidth = '440px';
            modal.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.3)';
            modal.style.fontFamily = '"Helvetica Neue", Helvetica, Arial, sans-serif';
            modal.style.textAlign = 'center';
            modal.style.boxSizing = 'border-box';
            
            modal.innerHTML = `
                <div id="fb-account-chooser" style="display: block; width: 100%;">
                    <i class="fa-brands fa-facebook" style="color: #1877f2; font-size: 3rem; margin-bottom: 15px;"></i>
                    <h3 style="font-size: 1.45rem; font-weight: 600; margin-bottom: 5px; color: #1c1e21;">Log in with Facebook</h3>
                    <p style="font-size: 0.95rem; color: #606770; margin-bottom: 25px;">to continue to <span style="font-weight: 600;">ResumeAI</span></p>
                    
                    <!-- Account List -->
                    <div style="display: flex; flex-direction: column; gap: 2px; margin-bottom: 20px; text-align: left; border-top: 1px solid #dadce0;">
                        <!-- Option 1 -->
                        <div class="fb-acc-opt" data-email="dhanushravi1485@gmail.com" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #dadce0; cursor: pointer; transition: background 0.2s; background: transparent;">
                            <div style="width: 28px; height: 28px; border-radius: 4px; background: #1877f2; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0;"><i class="fa-brands fa-facebook-f" style="font-size: 0.75rem;"></i></div>
                            <div>
                                <div style="font-weight: 600; font-size: 0.85rem; color: #3c4043; line-height: 1.2;">Dhanush Ravi</div>
                                <div style="font-size: 0.75rem; color: #606770; line-height: 1.2;">dhanushravi1485@gmail.com</div>
                            </div>
                        </div>
                        
                        <!-- Option 2 -->
                        <div class="fb-acc-opt" data-email="dhanushravi1735@gmail.com" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #dadce0; cursor: pointer; transition: background 0.2s; background: transparent;">
                            <div style="width: 28px; height: 28px; border-radius: 4px; background: #1877f2; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0;"><i class="fa-brands fa-facebook-f" style="font-size: 0.75rem;"></i></div>
                            <div>
                                <div style="font-weight: 600; font-size: 0.85rem; color: #3c4043; line-height: 1.2;">Dhanush Ravi</div>
                                <div style="font-size: 0.75rem; color: #606770; line-height: 1.2;">dhanushravi1735@gmail.com</div>
                            </div>
                        </div>

                        <!-- Use another account -->
                        <div id="fb-use-another-btn" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #dadce0; cursor: pointer; transition: background 0.2s; background: transparent;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: transparent; border: 1px solid #dadce0; color: #606770; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i class="fa-regular fa-user" style="font-size: 0.85rem;"></i>
                            </div>
                            <div style="font-weight: 600; font-size: 0.85rem; color: #3c4043;">Use another account</div>
                        </div>
                    </div>
                    
                    <div style="text-align: right; width: 100%;">
                        <button id="fb-popup-close-chooser" style="background: transparent; border: none; color: #1877f2; font-weight: 600; font-size: 0.9rem; cursor: pointer; padding: 10px 20px; transition: background 0.2s;">Cancel</button>
                    </div>
                </div>

                <div id="fb-custom-signin-view" style="display: none; width: 100%;">
                    <i class="fa-brands fa-facebook" style="color: #1877f2; font-size: 3rem; margin-bottom: 15px;"></i>
                    <h3 style="font-size: 1.45rem; font-weight: 600; margin-bottom: 5px; color: #1c1e21; font-family: 'Helvetica Neue', sans-serif;">Facebook Log In</h3>
                    <p style="font-size: 0.95rem; color: #606770; margin-bottom: 25px;">Enter your credentials</p>
                    
                    <!-- Custom Email Input -->
                    <div style="text-align: left; margin-bottom: 20px; width: 100%;">
                        <input type="email" id="fb-custom-email" style="width: 100%; padding: 14px 12px; border: 1px solid #dadce0; border-radius: 4px; font-size: 1rem; box-sizing: border-box; outline: none; transition: border-color 0.2s;" placeholder="Email address or phone number">
                        <p id="fb-error-msg" style="color: #d93025; font-size: 0.8rem; margin-top: 6px; display: none; font-weight: 500;"><i class="fa-solid fa-circle-exclamation"></i> Enter a valid email address</p>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 30px;">
                        <button id="fb-popup-back" style="background: transparent; border: none; color: #1877f2; font-weight: 600; font-size: 0.9rem; cursor: pointer; padding: 10px 0;">Back</button>
                        <button id="fb-popup-signin" style="background: #1877f2; color: #ffffff; border: none; padding: 10px 24px; border-radius: 4px; font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: background 0.2s;">Log In</button>
                    </div>
                </div>
            `;
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            const chooserView = modal.querySelector('#fb-account-chooser');
            const customView = modal.querySelector('#fb-custom-signin-view');
            const emailInput = modal.querySelector('#fb-custom-email');
            const signinBtn = modal.querySelector('#fb-popup-signin');
            const errorMsg = modal.querySelector('#fb-error-msg');
            const useAnotherBtn = modal.querySelector('#fb-use-another-btn');
            const backBtn = modal.querySelector('#fb-popup-back');
            
            useAnotherBtn.addEventListener('click', () => {
                chooserView.style.display = 'none';
                customView.style.display = 'block';
                setTimeout(() => emailInput.focus(), 100);
            });
            
            backBtn.addEventListener('click', () => {
                customView.style.display = 'none';
                chooserView.style.display = 'block';
                errorMsg.style.display = 'none';
                emailInput.style.borderColor = '#dadce0';
            });
            
            const options = modal.querySelectorAll('.fb-acc-opt');
            options.forEach(opt => {
                opt.addEventListener('mouseenter', () => opt.style.background = '#f2f3f5');
                opt.addEventListener('mouseleave', () => opt.style.background = 'transparent');
                
                opt.addEventListener('click', () => {
                    const selectedEmail = opt.getAttribute('data-email');
                    window.location.href = `/login/facebook-mock?email=${encodeURIComponent(selectedEmail)}`;
                });
            });
            
            useAnotherBtn.addEventListener('mouseenter', () => useAnotherBtn.style.background = '#f2f3f5');
            useAnotherBtn.addEventListener('mouseleave', () => useAnotherBtn.style.background = 'transparent');
            
            emailInput.addEventListener('focus', () => emailInput.style.borderColor = '#1877f2');
            emailInput.addEventListener('blur', () => emailInput.style.borderColor = '#dadce0');
            
            function handleFbSignIn() {
                const emailVal = emailInput.value.trim();
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                
                if (!emailVal || !emailRegex.test(emailVal)) {
                    errorMsg.style.display = 'block';
                    emailInput.style.borderColor = '#d93025';
                    return;
                }
                
                errorMsg.style.display = 'none';
                emailInput.style.borderColor = '#1877f2';
                window.location.href = `/login/facebook-mock?email=${encodeURIComponent(emailVal)}`;
            }
            
            signinBtn.addEventListener('click', handleFbSignIn);
            emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleFbSignIn();
                }
            });
            
            modal.querySelector('#fb-popup-close-chooser').addEventListener('click', () => {
                document.body.removeChild(overlay);
            });
        });
    }

    // 3D Card mouse tilt effect
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
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    });

    // Landing / Welcome Page TTS (Female Voice)
    const isLoginPage = window.location.pathname === '/login' || window.location.pathname === '/';
    if (isLoginPage) {
        const speakWelcome = () => {
            if ('speechSynthesis' in window) {
                if (window.hasSpokenWelcome) return;
                window.hasSpokenWelcome = true;
                
                // Pre-fetch voices to satisfy Chrome's async loading
                window.speechSynthesis.getVoices();
                
                const msg = new SpeechSynthesisUtterance("Welcome to ResumeAI! Please log in or register to analyze your resume.");
                const voices = window.speechSynthesis.getVoices();
                // Find a female English voice
                const femaleVoice = voices.find(voice => {
                    const name = voice.name.toLowerCase();
                    return voice.lang.startsWith('en') && (name.includes('female') || name.includes('zira') || name.includes('google us english') || name.includes('google uk english female') || name.includes('natural'));
                });
                
                if (femaleVoice) {
                    msg.voice = femaleVoice;
                }
                msg.rate = 0.95;
                msg.pitch = 1.1;
                window.speechSynthesis.speak(msg);
            }
        };
        
        // Trigger on interaction to respect browser autoplay security block
        document.addEventListener('click', speakWelcome, { once: true });
        document.addEventListener('mouseover', speakWelcome, { once: true });
        document.addEventListener('focusin', speakWelcome, { once: true });
    }

    // Analysis Report Complete Page TTS (Female Voice)
    const isReportPage = window.location.pathname.startsWith('/analyze/');
    if (isReportPage) {
        const speakThanks = () => {
            if ('speechSynthesis' in window) {
                if (window.hasSpokenThanks) return;
                window.hasSpokenThanks = true;
                
                window.speechSynthesis.getVoices();
                
                const msg = new SpeechSynthesisUtterance("Thank you for using this site! Your resume analysis is complete. You can view your match score, missing skills, and apply to recommended companies below.");
                const voices = window.speechSynthesis.getVoices();
                const femaleVoice = voices.find(voice => {
                    const name = voice.name.toLowerCase();
                    return voice.lang.startsWith('en') && (name.includes('female') || name.includes('zira') || name.includes('google us english') || name.includes('google uk english female') || name.includes('natural'));
                });
                
                if (femaleVoice) {
                    msg.voice = femaleVoice;
                }
                msg.rate = 0.95;
                msg.pitch = 1.1;
                window.speechSynthesis.speak(msg);
            }
        };
        
        document.addEventListener('click', speakThanks, { once: true });
        document.addEventListener('mouseover', speakThanks, { once: true });
        document.addEventListener('focusin', speakThanks, { once: true });
    }
});
