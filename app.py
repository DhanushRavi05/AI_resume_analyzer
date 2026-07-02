import os
import json
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import PyPDF2
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkeyforresumeai')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File uploads folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    profile = db.relationship('Profile', backref='user', uselist=False, lazy=True)
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    applications = db.relationship('Application', backref='user', lazy=True)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    college_name = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(150), nullable=False)
    cgpa = db.Column(db.String(50), nullable=False)
    graduation_year = db.Column(db.String(50), nullable=False)
    skills = db.Column(db.Text, nullable=True) # Comma-separated skills

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ats_score = db.Column(db.Integer, nullable=False)
    skill_gaps = db.Column(db.Text, nullable=False) # JSON list
    matching_jobs = db.Column(db.Text, nullable=False) # JSON list of dicts
    career_advice = db.Column(db.Text, nullable=True)
    parser_backend = db.Column(db.String(50), default="Python")
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    job_role = db.Column(db.String(150), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    resume_filename = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50), default="Applied") # Applied, Review, Offer, Closed
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables and seed default admin user
with app.app_context():
    db.create_all()
    # Check if admin exists, if not, create one
    admin_user = User.query.filter_by(username='dhanush').first()
    hashed_password = generate_password_hash('admin123')
    if not admin_user:
        admin = User(
            username='dhanush', 
            email='dhanush@resumeai.com', 
            password_hash=hashed_password, 
            is_admin=True
        )
        db.session.add(admin)
        
        # Auto-create admin academic profile to skip redirection
        admin_profile = Profile(
            user=admin,
            college_name="ResumeAI HQ",
            degree="Master Administrator",
            cgpa="10.0",
            graduation_year="2026",
            skills="Python, Flask, AI Development, SQL"
        )
        db.session.add(admin_profile)
    else:
        # Force-update admin password to ensure hashing compatibility
        admin_user.password_hash = hashed_password
        
    db.session.commit()
    print("\n=== DEFAULT ADMIN ACCOUNT CREATED ===")
    print("Email: dhanush@resumeai.com")
    print("Password: admin123")
    print("=====================================\n")

    # Compile ResumeParser.java on startup if javac is available
    try:
        import subprocess
        subprocess.run(['javac', 'ResumeParser.java'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("=== JAVA BACKEND PARSER COMPILED SUCCESSFULLY ===\n")
    except Exception as e:
        print("=== JAVA COMPILER NOT FOUND. USING PYTHON FALLBACK PARSER ===\n")

# Helper: Retrieve Gemini Key from Database or Environment
def get_gemini_api_key():
    try:
        setting = Setting.query.filter_by(key='gemini_api_key').first()
        if setting and setting.value and setting.value.strip():
            return setting.value.strip()
    except Exception as e:
        print(f"Error checking settings DB: {e}")
    
    # Fallback to .env
    key = os.getenv('GEMINI_API_KEY')
    if not key or key == 'YOUR_GEMINI_API_KEY_HERE':
        return None
    return key.strip()

# Helper: Async email sender using threads
def send_email_async(to_email, subject, body):
    # Fetch credentials
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT', 587)
    smtp_user = os.getenv('SMTP_EMAIL')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    
    # Always print to console/terminal for development log visibility
    print("\n" + "="*40)
    print("📧 MOCK EMAIL SYSTEM LOG (By Dhanush)")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("="*40 + "\n")
    
    if not smtp_server or not smtp_user or not smtp_pass:
        print("[SMTP] Configuration missing in .env. Printed email details to server terminal instead.")
        return
        
    def send():
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
            server.quit()
            print(f"[SMTP] Actual email delivered successfully to {to_email}!")
        except Exception as e:
            print(f"[SMTP] Error sending email: {e}")
            
    threading.Thread(target=send).start()

# Helper: Extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

# Helper: AI Analysis (with Mock Fallback)
def analyze_resume_with_ai(resume_text, profile):
    api_key = get_gemini_api_key()
    
    if not api_key:
        # Return elegant Mock data if API key is not configured
        mock_data = {
            "ats_score": 75,
            "skill_gaps": ["Docker", "Kubernetes", "System Design", "Cloud Computing (AWS/GCP)"],
            "matching_jobs": [
                {
                    "role": "Full Stack Developer",
                    "companies": ["Google", "Zoho", "Freshworks"],
                    "salary_range": "8 - 15 LPA",
                    "match_percentage": 85
                },
                {
                    "role": "Software Engineer",
                    "companies": ["Microsoft", "Cognizant", "TCS"],
                    "salary_range": "6 - 12 LPA",
                    "match_percentage": 78
                },
                {
                    "role": "Junior DevOps Engineer",
                    "companies": ["Infosys", "Wipro", "Amazon"],
                    "salary_range": "7 - 11 LPA",
                    "match_percentage": 65
                }
            ],
            "career_advice": "Your resume has a strong foundation in core programming, but to target top-tier companies, you should gain hands-on experience with cloud deployment tools (AWS, Docker) and strengthen your database optimization skills. Focus on building real-world projects."
        }
        return mock_data

    # Real Gemini API analysis
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an expert ATS (Applicant Tracking System) software and Technical Recruiter.
        Analyze the following resume text along with the candidate's academic profile.

        Academic Profile:
        - College: {profile.college_name}
        - Degree: {profile.degree}
        - CGPA: {profile.cgpa}
        - Graduation Year: {profile.graduation_year}
        - Declared Skills: {profile.skills}

        Resume Content:
        {resume_text}

        Provide your analysis response STRICTLY as a single JSON object. Do not wrap it in ```json ... ``` code blocks. Do not add any conversational text or markdown formatting. The output should be valid JSON matching this schema:
        {{
            "ats_score": 85, (integer between 0 and 100)
            "skill_gaps": ["Skill A", "Skill B"], (list of strings showing missing technical skills)
            "matching_jobs": [
                {{
                    "role": "Job Title",
                    "companies": ["Company 1", "Company 2"],
                    "salary_range": "Salary range in LPA (e.g. 10 - 15 LPA) or USD equivalent",
                    "match_percentage": 90 (integer between 0 and 100)
                }}
            ],
            "career_advice": "A paragraph offering actionable guidance for profile improvement."
        }}
        """
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Robustly extract JSON block if wrapped in markdown code blocks
        if "```json" in response_text:
            try:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            except:
                pass
        elif "```" in response_text:
            try:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            except:
                pass
        else:
            response_text = response_text.strip()
        
        data = json.loads(response_text)
        
        # Robust schema validation and cleaning to guarantee company and salary structures
        if not isinstance(data, dict):
            raise ValueError("Root response is not a JSON object")
            
        if 'ats_score' not in data:
            data['ats_score'] = 70
        else:
            try:
                data['ats_score'] = int(data['ats_score'])
            except:
                data['ats_score'] = 70
                
        if 'skill_gaps' not in data or not isinstance(data['skill_gaps'], list):
            data['skill_gaps'] = []
            
        if 'matching_jobs' not in data or not isinstance(data['matching_jobs'], list):
            data['matching_jobs'] = [
                {
                    "role": "Software Developer",
                    "companies": ["Google", "Zoho", "TCS"],
                    "salary_range": "8 - 14 LPA",
                    "match_percentage": 80
                }
            ]
        else:
            cleaned_jobs = []
            for job in data['matching_jobs']:
                if isinstance(job, dict):
                    role = job.get('role', 'Developer').strip()
                    companies = job.get('companies', [])
                    if isinstance(companies, str):
                        companies = [c.strip() for c in companies.split(',')]
                    elif not isinstance(companies, list):
                        companies = ["Tech Company"]
                    else:
                        companies = [str(c).strip() for c in companies]
                        
                    salary_range = str(job.get('salary_range', '6 - 10 LPA')).strip()
                    try:
                        match_pct = int(job.get('match_percentage', 75))
                    except:
                        match_pct = 75
                        
                    cleaned_jobs.append({
                        "role": role,
                        "companies": companies,
                        "salary_range": salary_range,
                        "match_percentage": match_pct
                    })
                elif isinstance(job, str):
                    cleaned_jobs.append({
                        "role": job,
                        "companies": ["Top Match"],
                        "salary_range": "10 - 15 LPA",
                        "match_percentage": 85
                    })
            data['matching_jobs'] = cleaned_jobs
            
        if 'career_advice' not in data:
            data['career_advice'] = "Focus on strengthening technical skills and projects."
            
        return data
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Fallback to mock if API fails mid-way
        return {
            "ats_score": 60,
            "skill_gaps": ["Error during AI processing. Please check API configuration."],
            "matching_jobs": [
                {
                    "role": "General Developer",
                    "companies": ["Review API Configuration"],
                    "salary_range": "N/A",
                    "match_percentage": 50
                }
            ],
            "career_advice": "We encountered an issue communicating with the AI server. Please make sure your GEMINI_API_KEY in the Admin panel is active and correct."
        }

# Routes
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
        
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        
        # Check if user already exists
        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            flash('Username or Email already registered!', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        # Auto-promote 'dhanush' or 'dhanush@resumeai.com' to admin
        is_admin = False
        if email.lower() == 'dhanush@resumeai.com' or username.lower() == 'dhanush':
            is_admin = True
            
        new_user = User(username=username, email=email, password_hash=hashed_password, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
        
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            # If user hasn't filled profile, redirect to profile setup
            if not user.profile:
                return redirect(url_for('profile_setup'))
            return redirect(url_for('upload'))
        else:
            flash('Invalid email or password!', 'danger')
            
    client_id, _ = get_google_oauth_credentials()
    return render_template('login.html', google_client_id=client_id or "")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# Google OAuth configuration details
def get_google_oauth_credentials():
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Try fetching from DB settings as well
    try:
        id_setting = Setting.query.filter_by(key='google_client_id').first()
        secret_setting = Setting.query.filter_by(key='google_client_secret').first()
        if id_setting and id_setting.value:
            client_id = id_setting.value.strip()
        if secret_setting and secret_setting.value:
            client_secret = secret_setting.value.strip()
    except Exception as e:
        print(f"Error checking google settings: {e}")
        
    return client_id, client_secret

@app.route('/login/google')
def google_login_redirect():
    client_id, _ = get_google_oauth_credentials()
    if not client_id:
        return redirect(url_for('login'))
        
    import urllib.parse
    state = "resumeai_oauth_state"
    redirect_uri = f"{request.url_root.replace('http://', 'https://') if 'onrender.com' in request.url_root else request.url_root}login/google/callback"
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account'
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(url)

@app.route('/login/google/callback')
def google_login_callback():
    code = request.args.get('code')
    if not code:
        flash('Google authentication cancelled.', 'warning')
        return redirect(url_for('login'))
        
    client_id, client_secret = get_google_oauth_credentials()
    redirect_uri = f"{request.url_root.replace('http://', 'https://') if 'onrender.com' in request.url_root else request.url_root}login/google/callback"
    
    # Exchange code for token
    import requests
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        r = requests.post(token_url, data=data)
        token_data = r.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            flash('Failed to retrieve tokens from Google.', 'danger')
            return redirect(url_for('login'))
            
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_r = requests.get(userinfo_url, headers=headers)
        user_info = userinfo_r.json()
        
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        if not email:
            flash('Failed to retrieve email from Google profile.', 'danger')
            return redirect(url_for('login'))
            
        # Log in or register user
        user = User.query.filter_by(email=email).first()
        if not user:
            hashed_password = generate_password_hash('googleoauthloginsecurepwd123')
            user = User(username=name, email=email, password_hash=hashed_password, is_admin=False)
            db.session.add(user)
            db.session.commit()
            
        login_user(user)
        
        # If user has no profile, create a default one to save time
        if not user.profile:
            profile = Profile(
                user_id=user.id,
                college_name="Google Verified University",
                degree="Computer Science Engineering",
                cgpa="8.5",
                graduation_year="2025",
                skills="Python, Javascript, React, SQL, Cloud Architecture"
            )
            db.session.add(profile)
            db.session.commit()
            
        flash('Logged in successfully via Google!', 'success')
        return redirect(url_for('upload'))
        
    except Exception as e:
        print(f"Google Callback Error: {e}")
        flash('Error during Google authentication exchange.', 'danger')
        return redirect(url_for('login'))

# Simulated Google OAuth login route for clean live demo
@app.route('/login/google-mock')
def google_mock_login():
    email = request.args.get('email', 'dhanushravi1485@gmail.com').strip()
    username = email.split('@')[0]
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create user
        hashed_password = generate_password_hash('googleauthbypass123')
        user = User(username=username, email=email, password_hash=hashed_password, is_admin=False)
        db.session.add(user)
        db.session.commit()
        
    login_user(user)
    flash('Logged in successfully via Google!', 'success')
    
    # If user has no profile, create a default one to save time
    if not user.profile:
        profile = Profile(
            user_id=user.id,
            college_name="Google Verified University",
            degree="Computer Science Engineering",
            cgpa="8.5",
            graduation_year="2025",
            skills="Python, Javascript, React, SQL, Cloud Architecture"
        )
        db.session.add(profile)
        db.session.commit()
        
    return redirect(url_for('upload'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_setup():
    # Fetch existing profile if any
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        college_name = request.form.get('college_name').strip()
        degree = request.form.get('degree').strip()
        cgpa = request.form.get('cgpa').strip()
        graduation_year = request.form.get('graduation_year').strip()
        skills = request.form.get('skills').strip()
        
        if profile:
            # Update existing
            profile.college_name = college_name
            profile.degree = degree
            profile.cgpa = cgpa
            profile.graduation_year = graduation_year
            profile.skills = skills
        else:
            # Create new
            profile = Profile(
                user_id=current_user.id,
                college_name=college_name,
                degree=degree,
                cgpa=cgpa,
                graduation_year=graduation_year,
                skills=skills
            )
            db.session.add(profile)
            
        db.session.commit()
        flash('Profile details saved successfully!', 'success')
        return redirect(url_for('upload'))
        
    return render_template('profile.html', profile=profile)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # Require profile setup before uploading resume
    if not current_user.profile:
        flash('Please fill in your college details first!', 'warning')
        return redirect(url_for('profile_setup'))
        
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file uploaded!', 'danger')
            return redirect(request.url)
            
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected!', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith('.pdf'):
            # Save uploaded file temporarily to run Java subprocess on path
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Run Java parser subprocess check
            use_java = False
            try:
                import subprocess
                if os.path.exists('ResumeParser.class'):
                    # Run Java ResumeParser subprocess
                    res = subprocess.run(['java', 'ResumeParser', filepath], capture_output=True, text=True, check=True)
                    java_meta = json.loads(res.stdout.strip())
                    if java_meta.get('status') == 'success':
                        use_java = True
                        print(f"Java Parser parsed successfully: {java_meta}")
            except Exception as e:
                print(f"Java subprocess failed/not available: {e}. Falling back to Python PyPDF2.")
                
            # Open saved file and extract text via Python PyPDF2 helper
            with open(filepath, 'rb') as f:
                text = extract_text_from_pdf(f)
                
            if not text or len(text.strip()) < 10:
                text = f"Resume Document. Candidate Academic Profile: {current_user.profile.college_name}, Degree: {current_user.profile.degree}, Skills: {current_user.profile.skills}. Professional profile: Technical Developer with experience in web engineering, Python, HTML/CSS, SQL database integration, Javascript frameworks, and application development."
                
            # Perform AI analysis
            analysis_result = analyze_resume_with_ai(text, current_user.profile)
            
            parser_backend_used = "Java JDK & Python" if use_java else "Python (Fallback)"
            
            # Save analysis results
            new_analysis = Analysis(
                user_id=current_user.id,
                ats_score=analysis_result['ats_score'],
                skill_gaps=json.dumps(analysis_result['skill_gaps']),
                matching_jobs=json.dumps(analysis_result['matching_jobs']),
                career_advice=analysis_result.get('career_advice', ''),
                parser_backend=parser_backend_used
            )
            db.session.add(new_analysis)
            db.session.commit()
            
            return redirect(url_for('analyze_report', analysis_id=new_analysis.id))
        else:
            flash('Only PDF resumes are supported currently.', 'danger')
            
    return render_template('upload.html')

@app.route('/analyze/<int:analysis_id>')
@login_required
def analyze_report(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Restrict users from viewing other users' reports (unless admin)
    if analysis.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    skill_gaps = json.loads(analysis.skill_gaps)
    matching_jobs = json.loads(analysis.matching_jobs)
    
    gemini_enabled = (get_gemini_api_key() is not None)
    
    return render_template(
        'analyze.html', 
        analysis=analysis, 
        skill_gaps=skill_gaps, 
        matching_jobs=matching_jobs,
        gemini_enabled=gemini_enabled
    )

# Job Application form with Resume Upload & Email Notifications
@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_job():
    company = request.args.get('company', '').strip()
    role = request.args.get('role', '').strip()
    
    if not company or not role:
        flash('Invalid Application parameters.', 'danger')
        return redirect(url_for('upload'))
        
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '').strip()
        
        # Check and handle resume file upload
        if 'application_resume' not in request.files:
            flash('Please upload your resume PDF to complete the application!', 'danger')
            return redirect(request.url)
            
        file = request.files['application_resume']
        if file.filename == '':
            flash('No resume selected!', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith('.pdf'):
            # Save file locally
            safe_filename = secure_filename(f"{current_user.username}_{company}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(filepath)
            
            # Save to DB
            new_app = Application(
                user_id=current_user.id,
                company_name=company,
                job_role=role,
                cover_letter=cover_letter,
                resume_filename=safe_filename
            )
            db.session.add(new_app)
            db.session.commit()
            
            # Formulate Demo careers link for redirecting locally
            demo_portal_url = f"{request.url_root}demo-portal?company={company.replace(' ', '+')}&role={role.replace(' ', '+')}"
            
            # Send Email Confirmation with Dhanush sign-off
            email_subject = f"ResumeAI - Application submitted successfully to {company} for {role}!"
            email_body = f"""Hi {current_user.username},

Your job application for {role} at {company} has been received successfully on ResumeAI!

Here are your application details:
- Applicant Name: {current_user.username}
- Target Company: {company}
- Target Role: {role}
- Academic Profile: {current_user.profile.college_name} | CGPA: {current_user.profile.cgpa}
- Pitch Note: {cover_letter}

Next Step:
To view your simulated interview schedule and status on the demo portal, click the link below:
{demo_portal_url}

Thank you for using our site!

Best regards,
By Dhanush
Founder, ResumeAI
"""
            # Trigger async email
            send_email_async(current_user.email, email_subject, email_body)
            
            # Redirect to success screen
            return redirect(url_for('apply_success', company=company, role=role))
        else:
            flash('Only PDF resumes are supported.', 'danger')
            
    return render_template('apply.html', company=company, role=role)

# Success confirmation page
@app.route('/apply-success')
@login_required
def apply_success():
    company = request.args.get('company', '').strip()
    role = request.args.get('role', '').strip()
    
    if not company or not role:
        return redirect(url_for('upload'))
        
    demo_url = url_for('demo_portal', company=company, role=role)
    return render_template('apply_success.html', company=company, role=role, real_url=demo_url)

# Demo Company Career Portal Simulator
@app.route('/demo-portal')
@login_required
def demo_portal():
    company = request.args.get('company', '').strip()
    role = request.args.get('role', '').strip()
    
    if not company or not role:
        return redirect(url_for('upload'))
        
    return render_template('demo_portal.html', company=company, role=role)

# Admin panel (restricted to Dhanush)
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
        
    # Get all users and their details
    users = User.query.all()
    # Find active analyses for each user
    all_data = []
    for u in users:
        if u.is_admin:
            continue
        latest_analysis = Analysis.query.filter_by(user_id=u.id).order_by(Analysis.timestamp.desc()).first()
        all_data.append({
            'user': u,
            'profile': u.profile,
            'analysis': latest_analysis
        })
        
    # Get all applications submitted by candidates
    applications = Application.query.order_by(Application.timestamp.desc()).all()
    
    gemini_key = get_gemini_api_key() or ''
    return render_template('admin.html', data=all_data, applications=applications, gemini_key=gemini_key)

# Admin API Key configuration route
@app.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    if not current_user.is_admin:
        abort(403)
    gemini_key = request.form.get('gemini_key', '').strip()
    
    setting = Setting.query.filter_by(key='gemini_api_key').first()
    if not setting:
        setting = Setting(key='gemini_api_key', value=gemini_key)
        db.session.add(setting)
    else:
        setting.value = gemini_key
    db.session.commit()
    
    if gemini_key:
        flash('Gemini API Key saved and activated successfully!', 'success')
    else:
        flash('Gemini API Key removed. Running in Mock Mode.', 'warning')
        
    return redirect(url_for('admin_panel'))

# Visual Resume Formatting Blueprint checklist Guide Route
@app.route('/guide')
def resume_guide():
    return render_template('guide.html')

# Simulated Facebook Login route
@app.route('/login/facebook-mock')
def facebook_mock_login():
    email = request.args.get('email', 'dhanush.facebook@gmail.com').strip()
    username = email.split('@')[0]
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create user
        hashed_password = generate_password_hash('facebookauthbypass123')
        user = User(username=username, email=email, password_hash=hashed_password, is_admin=False)
        db.session.add(user)
        db.session.commit()
        
    login_user(user)
    flash('Logged in successfully via Facebook!', 'success')
    
    # If user has no profile, create a default one to save time
    if not user.profile:
        profile = Profile(
            user_id=user.id,
            college_name="Facebook Verified User",
            degree="Engineering Candidate",
            cgpa="8.2",
            graduation_year="2025",
            skills="Python, SQL, JavaScript"
        )
        db.session.add(profile)
        db.session.commit()
        
    return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(debug=True)
