"""
AI-Powered Rapid Certification Platform
Main application server with Flask backend
"""
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from database.db_manager import DatabaseManager
from ai_engine.education_engine import AIEducationEngine
from ai_engine.source_gatherer import SourceGatherer
from ai_engine.adaptive_learning import AdaptiveLearningSystem

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.secret_key = os.urandom(24)
CORS(app)

# Initialize systems
db = DatabaseManager()
ai_engine = AIEducationEngine()
source_gatherer = SourceGatherer()
adaptive_system = AdaptiveLearningSystem()

# Available certification programs
CERTIFICATION_PROGRAMS = [
    {
        "id": "education",
        "name": "Education & Teaching Certificate",
        "duration": "8-12 weeks",
        "job_roles": ["Teacher Assistant", "Online Tutor", "Corporate Trainer"],
        "key_skills": ["Curriculum Design", "Learning Management Systems", "Student Assessment"]
    },
    {
        "id": "finance",
        "name": "Finance & Investment Certificate",
        "duration": "10-14 weeks",
        "job_roles": ["Financial Analyst", "Investment Advisor", "Portfolio Manager"],
        "key_skills": ["Financial Analysis", "Investment Strategies", "Risk Management"]
    },
    {
        "id": "it_software",
        "name": "IT & Software Development Certificate",
        "duration": "12-16 weeks",
        "job_roles": ["Software Developer", "Systems Administrator", "DevOps Engineer"],
        "key_skills": ["Python/JavaScript", "Cloud Computing", "Database Management", "API Development"]
    },
    {
        "id": "cooking",
        "name": "Professional Culinary Certificate",
        "duration": "8-10 weeks",
        "job_roles": ["Line Cook", "Sous Chef", "Catering Manager"],
        "key_skills": ["Food Safety", "Culinary Techniques", "Menu Planning", "Kitchen Management"]
    },
    {
        "id": "mechanical_engineering",
        "name": "Mechanical Engineering Technician Certificate",
        "duration": "14-18 weeks",
        "job_roles": ["CAD Technician", "Quality Control Inspector", "Maintenance Technician"],
        "key_skills": ["CAD Software", "Blueprint Reading", "Materials Science", "Manufacturing Processes"]
    },
    {
        "id": "electrician",
        "name": "Licensed Electrician Certificate",
        "duration": "16-20 weeks",
        "job_roles": ["Residential Electrician", "Commercial Electrician", "Maintenance Electrician"],
        "key_skills": ["Electrical Code (NEC)", "Wiring & Circuitry", "Safety Protocols", "Troubleshooting"]
    },
    {
        "id": "hvac",
        "name": "HVAC Technician Certificate",
        "duration": "12-16 weeks",
        "job_roles": ["HVAC Installer", "Service Technician", "System Designer"],
        "key_skills": ["EPA 608 Certification", "System Installation", "Diagnostics", "Energy Efficiency"]
    },
    {
        "id": "nursing",
        "name": "Certified Nursing Assistant (CNA)",
        "duration": "6-8 weeks",
        "job_roles": ["Certified Nursing Assistant", "Home Health Aide", "Patient Care Technician"],
        "key_skills": ["Patient Care", "Medical Terminology", "Vital Signs", "Clinical Procedures"]
    },
    {
        "id": "cybersecurity",
        "name": "Cybersecurity Specialist Certificate",
        "duration": "12-16 weeks",
        "job_roles": ["Security Analyst", "Penetration Tester", "Security Operations Specialist"],
        "key_skills": ["Network Security", "Threat Detection", "Incident Response", "Security Tools"]
    },
    {
        "id": "accounting",
        "name": "Accounting & Bookkeeping Certificate",
        "duration": "10-12 weeks",
        "job_roles": ["Bookkeeper", "Accounts Payable/Receivable Clerk", "Payroll Specialist"],
        "key_skills": ["QuickBooks", "Financial Reporting", "Tax Preparation", "Accounts Reconciliation"]
    },
    {
        "id": "business",
        "name": "Business Administration Certificate",
        "duration": "8-12 weeks",
        "job_roles": ["Office Manager", "Business Analyst", "Operations Coordinator"],
        "key_skills": ["Project Management", "Business Communication", "Data Analysis", "Operations Management"]
    },
    {
        "id": "ai_education",
        "name": "AI & Machine Learning Certificate",
        "duration": "14-18 weeks",
        "job_roles": ["AI Developer", "ML Engineer", "Data Scientist", "AI Consultant"],
        "key_skills": ["Machine Learning", "Neural Networks", "Python/TensorFlow", "AI Ethics", "Model Deployment"]
    }
]

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html', programs=CERTIFICATION_PROGRAMS)

@app.route('/api/programs')
def get_programs():
    """Get all certification programs"""
    return jsonify(CERTIFICATION_PROGRAMS)

@app.route('/api/program/<program_id>')
def get_program_detail(program_id):
    """Get detailed information about a specific program"""
    program = next((p for p in CERTIFICATION_PROGRAMS if p['id'] == program_id), None)
    if not program:
        return jsonify({"error": "Program not found"}), 404

    # Get curriculum from database
    curriculum = db.get_curriculum(program_id)

    # Get sources
    sources = db.get_program_sources(program_id)

    return jsonify({
        "program": program,
        "curriculum": curriculum,
        "sources": sources,
        "certification_path": db.get_certification_path(program_id)
    })

@app.route('/api/enroll', methods=['POST'])
def enroll_student():
    """Enroll a student in a program"""
    data = request.json
    student_id = db.create_student(
        name=data['name'],
        email=data['email'],
        company=data.get('company'),
        program_id=data['program_id']
    )

    # Initialize personalized learning path
    learning_path = adaptive_system.create_learning_path(
        student_id=student_id,
        program_id=data['program_id'],
        prior_knowledge=data.get('prior_knowledge', {})
    )

    return jsonify({
        "student_id": student_id,
        "learning_path": learning_path,
        "message": "Successfully enrolled!"
    })

@app.route('/api/lesson/<program_id>/<lesson_id>')
def get_lesson(program_id, lesson_id):
    """Get AI-generated lesson content with sources"""
    lesson = db.get_lesson(program_id, lesson_id)

    if not lesson or not lesson.get('content'):
        # Generate new content using AI engine
        lesson = ai_engine.generate_lesson(program_id, lesson_id)

        # Gather sources
        sources = source_gatherer.gather_sources(
            topic=lesson['title'],
            program=program_id
        )

        # Save to database
        db.save_lesson(program_id, lesson_id, lesson, sources)

    return jsonify(lesson)

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit student feedback to improve content"""
    data = request.json

    # Save feedback
    db.save_feedback(
        student_id=data['student_id'],
        program_id=data['program_id'],
        lesson_id=data['lesson_id'],
        rating=data['rating'],
        comments=data.get('comments'),
        helpful=data.get('helpful', True)
    )

    # Update adaptive learning system
    adaptive_system.process_feedback(data)

    # If rating is low, trigger content improvement
    if data['rating'] < 3:
        ai_engine.improve_content(
            program_id=data['program_id'],
            lesson_id=data['lesson_id'],
            feedback=data['comments']
        )

    return jsonify({"message": "Feedback received and processed"})

@app.route('/api/hr/workforce-analysis', methods=['POST'])
def workforce_analysis():
    """Analyze workforce gaps for HR deployment"""
    data = request.json

    analysis = {
        "company_id": data.get('company_id'),
        "current_skills": data.get('current_skills', []),
        "required_skills": data.get('required_skills', []),
        "gaps": [],
        "recommended_programs": []
    }

    # Identify skill gaps
    current = set(data.get('current_skills', []))
    required = set(data.get('required_skills', []))
    gaps = required - current

    analysis['gaps'] = list(gaps)

    # Recommend programs
    for gap in gaps:
        for program in CERTIFICATION_PROGRAMS:
            if any(skill.lower() in gap.lower() or gap.lower() in skill.lower()
                   for skill in program['key_skills']):
                if program not in analysis['recommended_programs']:
                    analysis['recommended_programs'].append(program)

    return jsonify(analysis)

@app.route('/api/hr/deploy-training', methods=['POST'])
def deploy_training():
    """Deploy training programs to employees"""
    data = request.json

    deployment = db.create_deployment(
        company_id=data['company_id'],
        program_ids=data['program_ids'],
        employee_ids=data['employee_ids'],
        deadline=data.get('deadline')
    )

    # Enroll all employees
    enrollments = []
    for employee_id in data['employee_ids']:
        for program_id in data['program_ids']:
            enrollment = db.enroll_employee(
                employee_id=employee_id,
                program_id=program_id,
                company_id=data['company_id']
            )
            enrollments.append(enrollment)

    return jsonify({
        "deployment_id": deployment,
        "enrollments": enrollments,
        "message": f"Successfully deployed training to {len(data['employee_ids'])} employees"
    })

@app.route('/api/progress/<student_id>')
def get_progress(student_id):
    """Get student progress and analytics"""
    progress = db.get_student_progress(student_id)

    return jsonify({
        "student_id": student_id,
        "progress": progress,
        "completion_percentage": progress.get('completion_percentage', 0),
        "certificates_earned": progress.get('certificates_earned', []),
        "next_lessons": adaptive_system.get_next_lessons(student_id)
    })

@app.route('/api/certificate/<student_id>/<program_id>')
def issue_certificate(student_id, program_id):
    """Issue certificate upon completion"""
    progress = db.get_student_progress(student_id)

    if progress.get('completion_percentage', 0) >= 100:
        certificate = db.issue_certificate(
            student_id=student_id,
            program_id=program_id
        )
        return jsonify(certificate)
    else:
        return jsonify({
            "error": "Program not completed",
            "completion": progress.get('completion_percentage', 0)
        }), 400

@app.route('/api/sources/verify', methods=['POST'])
def verify_source():
    """Verify and add a new educational source"""
    data = request.json

    verification = source_gatherer.verify_source(
        url=data['url'],
        program_id=data['program_id']
    )

    if verification['valid']:
        db.add_source(
            program_id=data['program_id'],
            url=data['url'],
            title=verification['title'],
            reliability_score=verification['score']
        )

    return jsonify(verification)

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard for monitoring"""
    stats = {
        "total_students": db.get_total_students(),
        "total_certificates_issued": db.get_total_certificates(),
        "programs_count": len(CERTIFICATION_PROGRAMS),
        "average_completion_rate": db.get_average_completion_rate(),
        "feedback_summary": db.get_feedback_summary()
    }

    return render_template('admin_dashboard.html', stats=stats)

if __name__ == '__main__':
    # Initialize database
    db.initialize()

    # Start server
    app.run(host='0.0.0.0', port=5000, debug=True)
