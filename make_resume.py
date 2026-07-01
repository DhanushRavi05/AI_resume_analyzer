import os
import sys

def build_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor
    except ImportError:
        print("Installing reportlab library first...")
        os.system(f'"{sys.executable}" -m pip install reportlab')
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor

    pdf_path = "dhanush_resume.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    color_primary = HexColor("#1e293b")   # Slate
    color_accent = HexColor("#7c3aed")    # Violet accent
    color_text = HexColor("#334155")      # Dark gray text

    # Custom Styles
    style_title = ParagraphStyle(
        'Name',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        textColor=color_primary,
        spaceAfter=4
    )
    
    style_subtitle = ParagraphStyle(
        'JobTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=color_accent,
        spaceAfter=15
    )

    style_section = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=color_primary,
        spaceBefore=12,
        spaceAfter=6
    )

    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=color_text,
        spaceAfter=8
    )

    style_bullet = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=color_text,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []

    # Header
    story.append(Paragraph("DHANUSH", style_title))
    story.append(Paragraph("Software Engineer & Full Stack Developer  |  dhanush@resumeai.com  |  Chennai, India", style_subtitle))
    
    story.append(Paragraph("SUMMARY", style_section))
    story.append(Paragraph(
        "Highly motivated Full-Stack Developer with hands-on experience in Python, Flask, and web technologies. "
        "Passionate about building responsive, secure applications and integrating intelligent features like AI-powered analysis "
        "and SQL database systems.", style_body
    ))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("EDUCATION", style_section))
    story.append(Paragraph("<b>Bachelor of Engineering in Computer Science (B.E. CSE)</b>", style_body))
    story.append(Paragraph("Anna University, Chennai  |  CGPA: 8.5/10  |  Graduation Year: 2026", style_body))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("TECHNICAL SKILLS", style_section))
    story.append(Paragraph("<b>Programming Languages:</b> Python, JavaScript, SQL, HTML5, CSS3", style_bullet))
    story.append(Paragraph("<b>Frameworks & Tools:</b> Flask, SQLite, Node.js, Git, Gunicorn, RESTful APIs", style_bullet))
    story.append(Paragraph("<b>Development Concepts:</b> User Authentication, Database Design, Responsive Web Design, AI Integration", style_bullet))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("PROJECTS", style_section))
    
    # Project 1
    story.append(Paragraph("<b>ResumeAI — Smart Resume Analyzer</b>", style_body))
    story.append(Paragraph(
        "• Developed a secure, multi-page web application using Flask and SQLite to analyze resume PDFs.<br/>"
        "• Built an automated ATS score system, identifying skill gaps, matching job roles, and estimated salary packages.<br/>"
        "• Created a glassmorphic admin dashboard for exclusive database access and user profile monitoring.",
        style_bullet
    ))
    
    # Project 2
    story.append(Paragraph("<b>Personal Portfolio Website</b>", style_body))
    story.append(Paragraph(
        "• Designed an interactive portfolio using HTML, CSS, and modern animations to showcase projects.<br/>"
        "• Optimized visual load speeds and page structure for enhanced search engine optimization (SEO).",
        style_bullet
    ))

    # Build document
    doc.build(story)
    print(f"Successfully generated pdf resume: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
