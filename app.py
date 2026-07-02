import os
import json
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import PyPDF2
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'resumeai_secret_encryption_key_v2_999')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# Database Schema Tables
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mobile_number = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(250), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    college_name = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(150), nullable=False)
    cgpa = db.Column(db.String(50), nullable=False)
    graduation_year = db.Column(db.String(50), nullable=False)
    skills = db.Column(db.Text, nullable=True) # Comma-separated technical skills

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
    status = db.Column(db.String(50), default="Applied") # Applied, Review, Interview Scheduled, Offer, Closed
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables and seed default admin user
with app.app_context():
    db.create_all()
    
    # Auto-migration schema check: Add parser_backend and mobile_number columns if they don't exist
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(analysis)"))
            columns = [row[1] for row in result.fetchall()]
            if 'parser_backend' not in columns:
                conn.execute(text("ALTER TABLE analysis ADD COLUMN parser_backend VARCHAR(50) DEFAULT 'Python'"))
                conn.commit()
                
            # Check user table for mobile_number column
            result_user = conn.execute(text("PRAGMA table_info(user)"))
            columns_user = [row[1] for row in result_user.fetchall()]
            if 'mobile_number' not in columns_user:
                conn.execute(text("ALTER TABLE user ADD COLUMN mobile_number VARCHAR(50) DEFAULT 'N/A'"))
                conn.commit()
    except Exception as db_err:
        print(f"[DB] Migration check failed: {db_err}")

    # Seed admin 'dhanush'
    admin_user = User.query.filter_by(username='dhanush').first()
    hashed_password = generate_password_hash('admin123')
    if not admin_user:
        admin = User(
            username='dhanush', 
            email='dhanush@resumeai.com', 
            mobile_number='+910000000000',
            password_hash=hashed_password, 
            is_admin=True
        )
        db.session.add(admin)
        admin_profile = Profile(
            user=admin,
            college_name="ResumeAI HQ",
            degree="Master Administrator",
            cgpa="10.0",
            graduation_year="2026",
            skills="Python, Flask, AI Development, SQL, Java"
        )
        db.session.add(admin_profile)
    else:
        admin_user.password_hash = hashed_password
        admin_user.mobile_number = '+910000000000'
        
    # Pre-seed user accounts for Dhanush to prevent deletion on Render container restarts
    dhanush_1485 = User.query.filter_by(email='dhanushravi1485@gmail.com').first()
    if not dhanush_1485:
        dhanush_1485 = User(
            username='dhanush_1485',
            email='dhanushravi1485@gmail.com',
            mobile_number='+919876543210',
            password_hash=generate_password_hash('password123'),
            is_admin=False
        )
        db.session.add(dhanush_1485)
        db.session.flush()
        
    dhanush_1485.password_hash = generate_password_hash('password123')
    dhanush_1485.mobile_number = '+919876543210'
    
    if not dhanush_1485.profile:
        p1 = Profile(
            user=dhanush_1485,
            college_name="Google verified university",
            degree="B.E. Computer Science Engineering",
            cgpa="8.5",
            graduation_year="2025",
            skills="Python, Flask, SQL, Java, Javascript"
        )
        db.session.add(p1)

    dhanush_1735 = User.query.filter_by(email='dhanushravi1735@gmail.com').first()
    if not dhanush_1735:
        dhanush_1735 = User(
            username='dhanush_1735',
            email='dhanushravi1735@gmail.com',
            mobile_number='+919876543211',
            password_hash=generate_password_hash('password123'),
            is_admin=False
        )
        db.session.add(dhanush_1735)
        db.session.flush()
        
    dhanush_1735.password_hash = generate_password_hash('password123')
    dhanush_1735.mobile_number = '+919876543211'
    
    if not dhanush_1735.profile:
        p2 = Profile(
            user=dhanush_1735,
            college_name="Google verified university",
            degree="B.E. Computer Science Engineering",
            cgpa="8.5",
            graduation_year="2025",
            skills="Python, Flask, SQL, Java, Javascript"
        )
        db.session.add(p2)
        
    db.session.commit()
    db.session.commit()

    # Compile ResumeParser.java on startup if javac is available
    try:
        import subprocess
        subprocess.run(['javac', 'ResumeParser.java'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[JAVA] ResumeParserCompiled successfully.\n")
    except Exception as e:
        print("[JAVA] compiler not detected. Running on Python fallback modes.\n")

# Helper: Retrieve Gemini Key from Database or Environment
def get_gemini_api_key():
    try:
        setting = Setting.query.filter_by(key='gemini_api_key').first()
        if setting and setting.value and setting.value.strip():
            return setting.value.strip()
    except Exception as e:
        print(f"Error checking settings DB: {e}")
    
    key = os.getenv('GEMINI_API_KEY')
    if not key or key == 'YOUR_GEMINI_API_KEY_HERE':
        return None
    return key.strip()

# Helper: Async email sender using threads
def send_email_async(to_email, subject, body):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT', 587)
    smtp_user = os.getenv('SMTP_EMAIL')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    
    # Print to console logs
    print("\n" + "="*40)
    print("📧 MOCK EMAIL SYSTEM LOG")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("="*40 + "\n")
    
    if not smtp_server or not smtp_user or not smtp_pass:
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

# Helper: AI Analysis (with Fallbacks and schema checks)
def analyze_resume_with_ai(resume_text, profile):
    api_key = get_gemini_api_key()
    
    if not api_key:
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
            "skill_gaps": ["Skill A", "Skill B"], (list of technical skills)
            "matching_jobs": [
                {{
                    "role": "Job Title",
                    "companies": ["Company A", "Company B"],
                    "salary_range": "Salary range in LPA (e.g. 10 - 15 LPA)",
                    "match_percentage": 90 (integer between 0 and 100)
                }}
            ],
            "career_advice": "Actionable feedback for profile improvements."
        }}
        """
        
        # Try gemini-1.5-flash, fallback to gemini-pro if not found
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
        except Exception as flash_err:
            err_msg = str(flash_err).lower()
            if "not found" in err_msg or "404" in err_msg or "not_found" in err_msg:
                print("[GEMINI] Falling back to gemini-pro model")
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
            else:
                raise flash_err
                
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
        
        # Schema verification
        if 'ats_score' not in data:
            data['ats_score'] = 70
        else:
            try:
                data['ats_score'] = int(data['ats_score'])
            except:
                data['ats_score'] = 70
                
        if 'skill_gaps' not in data or not isinstance(data['skill_gaps'], list):
            data['skill_gaps'] = ["Cloud Computing", "System Architecture"]
            
        if 'matching_jobs' not in data or not isinstance(data['matching_jobs'], list):
            data['matching_jobs'] = []
        else:
            cleaned_jobs = []
            for job in data['matching_jobs']:
                if isinstance(job, dict):
                    role = str(job.get('role', 'Developer')).strip()
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
            data['matching_jobs'] = cleaned_jobs
            
        if 'career_advice' not in data:
            data['career_advice'] = "Strengthen core programming skills."
            
        return data
        
    except Exception as e:
        print(f"Gemini API Error: {e}. Falling back to clean mock data.")
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
            "career_advice": "Your resume has a strong foundation. (Note: We encountered an issue communicating with the Gemini AI server. Please make sure your GEMINI_API_KEY is active and correct in the Admin settings. Displaying simulated report)."
        }
        return mock_data

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
        import random
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        mobile_number = request.form.get('mobile_number').strip()
        password = request.form.get('password')
        
        # Validations
        if not username or not email or not password or not mobile_number:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
            
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address!', 'danger')
            return redirect(url_for('register'))
            
        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            flash('Username or Email already registered!', 'danger')
            return redirect(url_for('register'))
            
        # Generate random 6-digit OTP code
        otp = str(random.randint(100000, 999999))
        
        # Store temporary data in Flask Session
        from flask import session
        session['temp_reg'] = {
            'username': username,
            'email': email,
            'mobile_number': mobile_number,
            'password': password
        }
        session['reg_otp'] = otp
        
        print("\n" + "="*40)
        print(f"🎙️ [OTP SYSTEM] CODE {otp} SENT TO MOBILE: {mobile_number}")
        print("="*40 + "\n")
        
        flash(f'Verification OTP sent to {mobile_number}!', 'info')
        return redirect(url_for('verify_otp'))
        
    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    from flask import session
    temp_reg = session.get('temp_reg')
    reg_otp = session.get('reg_otp')
    
    if not temp_reg or not reg_otp:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('register'))
        
    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        if otp_code == reg_otp:
            # Create user database record
            username = temp_reg['username']
            email = temp_reg['email']
            mobile_number = temp_reg['mobile_number']
            password = temp_reg['password']
            
            hashed_password = generate_password_hash(password)
            is_admin = False
            if username.lower() == 'dhanush' or email.lower() == 'dhanush@resumeai.com':
                is_admin = True
                
            new_user = User(
                username=username,
                email=email,
                mobile_number=mobile_number,
                password_hash=hashed_password,
                is_admin=is_admin
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Clear session
            session.pop('temp_reg', None)
            session.pop('reg_otp', None)
            
            flash('Registration complete! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP code. Please check and try again!', 'danger')
            
    return render_template('verify_otp.html', mobile=temp_reg['mobile_number'], otp=reg_otp)

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
            if not user.profile:
                return redirect(url_for('profile_setup'))
            return redirect(url_for('upload'))
        else:
            flash('Invalid email or password!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_setup():
    profile = current_user.profile
    if request.method == 'POST':
        college_name = request.form.get('college_name').strip()
        degree = request.form.get('degree').strip()
        cgpa = request.form.get('cgpa').strip()
        graduation_year = request.form.get('graduation_year').strip()
        skills = request.form.get('skills').strip()
        
        if not college_name or not degree or not cgpa or not graduation_year:
            flash('Please fill out all academic fields!', 'danger')
            return redirect(url_for('profile_setup'))
            
        if profile:
            profile.college_name = college_name
            profile.degree = degree
            profile.cgpa = cgpa
            profile.graduation_year = graduation_year
            profile.skills = skills
        else:
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
        flash('Academic profile saved successfully!', 'success')
        return redirect(url_for('upload'))
        
    return render_template('profile.html', profile=profile)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if not current_user.profile:
        flash('Please fill in your academic profile first!', 'warning')
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
            # Save file
            filename = secure_filename(f"{current_user.username}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Check Java compiled parser
            use_java = False
            try:
                import subprocess
                if os.path.exists('ResumeParser.class'):
                    res = subprocess.run(['java', 'ResumeParser', filepath], capture_output=True, text=True, check=True)
                    java_meta = json.loads(res.stdout.strip())
                    if java_meta.get('status') == 'success':
                        use_java = True
            except Exception as java_err:
                print(f"[JAVA] subprocess failed: {java_err}")
                
            # Extract Text
            with open(filepath, 'rb') as f:
                text = extract_text_from_pdf(f)
                
            if not text or len(text.strip()) < 10:
                text = f"Resume Document. Academic Profile: {current_user.profile.college_name}, Degree: {current_user.profile.degree}, skills: {current_user.profile.skills}."
                
            analysis_result = analyze_resume_with_ai(text, current_user.profile)
            parser_backend_used = "Java JDK & Python" if use_java else "Python (Fallback)"
            
            # Save
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
            
            # Dispatch Email asynchronously
            email_subject = f"Dhanush's AI Resume Analyzer - ATS Score: {analysis_result['ats_score']}%"
            email_body = f"""Hi {current_user.username},

Your resume analysis is complete on Dhanush's AI Resume Analyzer!

Here are your detailed analysis results:
- ATS Match Score: {analysis_result['ats_score']}%
- Parser Engine Used: {parser_backend_used}

Skill Gaps Identified:
{', '.join(analysis_result['skill_gaps']) if analysis_result['skill_gaps'] else 'None! Good job.'}

Recommended Job Roles & Estimated Packages:
"""
            for job in analysis_result['matching_jobs']:
                companies_str = ', '.join(job.get('companies', []))
                email_body += f"- {job.get('role')} at {companies_str} (Est. Salary: {job.get('salary_range')})\n"
                
            email_body += f"""
Actionable Career Guidance:
{analysis_result.get('career_advice')}

Thanks for using! Created by Dhanush.
"""
            send_email_async(current_user.email, email_subject, email_body)
            
            return redirect(url_for('analyze_report', analysis_id=new_analysis.id))
        else:
            flash('Only PDF resumes are supported.', 'danger')
            
    return render_template('upload.html')

@app.route('/analyze/<int:analysis_id>')
@login_required
def analyze_report(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
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

@app.route('/tracker')
@login_required
def resume_tracker():
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.timestamp.desc()).all()
    applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.timestamp.desc()).all()
    return render_template('tracker.html', analyses=analyses, applications=applications)

@app.route('/about')
def about_site():
    return render_template('about.html')

@app.route('/guide')
def resume_guide():
    return render_template('guide.html')

@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_job():
    company = request.args.get('company', '').strip()
    role = request.args.get('role', '').strip()
    
    if not company or not role:
        return redirect(url_for('upload'))
        
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '').strip()
        if 'application_resume' not in request.files:
            flash('Please upload your resume PDF to complete the application!', 'danger')
            return redirect(request.url)
            
        file = request.files['application_resume']
        if file.filename == '':
            flash('No resume selected!', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith('.pdf'):
            safe_filename = secure_filename(f"{current_user.username}_{company}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(filepath)
            
            # Save application to database
            new_app = Application(
                user_id=current_user.id,
                company_name=company,
                job_role=role,
                cover_letter=cover_letter,
                resume_filename=safe_filename
            )
            db.session.add(new_app)
            db.session.commit()
            
            demo_portal_url = f"{request.url_root}demo-portal?company={company.replace(' ', '+')}&role={role.replace(' ', '+')}"
            
            # Send Email confirmation async
            email_subject = f"Application submitted to {company}!"
            email_body = f"""Hi {current_user.username},

Your application for {role} at {company} has been received.

Tracker Link:
{demo_portal_url}

Thanks for using! Created by Dhanush.
"""
            send_email_async(current_user.email, email_subject, email_body)
            return redirect(url_for('apply_success', company=company, role=role))
            
    return render_template('apply.html', company=company, role=role)

@app.route('/apply-success')
@login_required
def apply_success():
    company = request.args.get('company', '').strip()
    role = request.args.get('role', '').strip()
    if not company or not role:
        return redirect(url_for('upload'))
    demo_url = url_for('demo_portal', company=company, role=role)
    return render_template('apply_success.html', company=company, role=role, real_url=demo_url)

@app.route('/demo-portal')
@login_required
def demo_portal():
    company = request.args.get('company', '').strip()
    role = request.args.get('role', '').strip()
    return render_template('demo_portal.html', company=company, role=role)

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin or current_user.username.lower() != 'dhanush':
        flash('Unauthorized access! Only the owner Dhanush Ravi can access Admin Settings.', 'danger')
        return redirect(url_for('upload'))
        
    users = User.query.all()
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
        
    applications = Application.query.order_by(Application.timestamp.desc()).all()
    gemini_key = get_gemini_api_key() or ''
    return render_template('admin.html', data=all_data, applications=applications, gemini_key=gemini_key)

@app.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    if not current_user.is_admin or current_user.username.lower() != 'dhanush':
        flash('Unauthorized access! Only the owner Dhanush Ravi can access Admin Settings.', 'danger')
        return redirect(url_for('upload'))
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

if __name__ == '__main__':
    app.run(debug=True)
