"""
Database Manager for AI Certification Platform
Handles all database operations with source tracking and adaptive learning
"""
import sqlite3
import json
from datetime import datetime
import hashlib
import os

class DatabaseManager:
    def __init__(self, db_path='database/cert_platform.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                company TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Programs table (for customization)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS programs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                duration TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Enhanced Curriculum table with hierarchical support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                order_index INTEGER,
                learning_objectives TEXT,
                estimated_hours REAL,
                hierarchy_level TEXT DEFAULT 'lesson',
                parent_id INTEGER,
                word_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES programs(id),
                FOREIGN KEY (parent_id) REFERENCES curriculum(id)
            )
        ''')

        # Sources table - critical for grounding education in reliable sources
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT NOT NULL,
                lesson_id TEXT,
                url TEXT NOT NULL,
                title TEXT,
                source_type TEXT,
                reliability_score REAL DEFAULT 0.0,
                last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                citation TEXT,
                metadata TEXT,
                FOREIGN KEY (program_id) REFERENCES programs(id)
            )
        ''')

        # Enrollments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                company_id TEXT,
                enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (program_id) REFERENCES programs(id)
            )
        ''')

        # Progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                status TEXT DEFAULT 'not_started',
                score REAL,
                time_spent INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (program_id) REFERENCES programs(id)
            )
        ''')

        # Feedback table - drives adaptive learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                rating INTEGER,
                comments TEXT,
                helpful BOOLEAN,
                difficulty_rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Certificates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id TEXT PRIMARY KEY,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verification_code TEXT UNIQUE,
                certificate_data TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (program_id) REFERENCES programs(id)
            )
        ''')

        # HR Deployments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hr_deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                program_ids TEXT NOT NULL,
                employee_ids TEXT NOT NULL,
                deadline TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Content improvements tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                previous_version TEXT,
                new_version TEXT,
                improvement_reason TEXT,
                feedback_ids TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Adaptive learning paths
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                path_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Content suggestions (user-suggested changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                suggestion_type TEXT DEFAULT 'content_update',
                current_content TEXT,
                suggested_content TEXT,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                flagged_at TIMESTAMP,
                agreement_percentage REAL,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Suggestion votes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestion_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                vote BOOLEAN NOT NULL,
                comment TEXT,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(suggestion_id, student_id),
                FOREIGN KEY (suggestion_id) REFERENCES content_suggestions(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Admin notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                reference_id INTEGER,
                message TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Audio cache for text-to-speech
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_id TEXT UNIQUE NOT NULL,
                program_id TEXT,
                lesson_id TEXT,
                voice_id TEXT,
                file_path TEXT,
                duration_seconds INTEGER,
                file_size INTEGER,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Mini-certificates for subsections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mini_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                program_id TEXT NOT NULL,
                curriculum_id INTEGER NOT NULL,
                certificate_type TEXT DEFAULT 'subsection',
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verification_code TEXT UNIQUE,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (curriculum_id) REFERENCES curriculum(id)
            )
        ''')

        # Images and resources
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lesson_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                url TEXT NOT NULL,
                thumbnail_url TEXT,
                title TEXT,
                description TEXT,
                educational_value REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        print("✓ Database initialized successfully")

    def create_student(self, name, email, company=None, program_id=None):
        """Create a new student"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO students (name, email, company) VALUES (?, ?, ?)',
                (name, email, company)
            )
            student_id = cursor.lastrowid

            if program_id:
                cursor.execute(
                    'INSERT INTO enrollments (student_id, program_id, company_id) VALUES (?, ?, ?)',
                    (student_id, program_id, company)
                )

            conn.commit()
            return student_id
        except sqlite3.IntegrityError:
            # Student already exists, get their ID
            cursor.execute('SELECT id FROM students WHERE email = ?', (email,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_curriculum(self, program_id):
        """Get curriculum for a program"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM curriculum
            WHERE program_id = ?
            ORDER BY order_index
        ''', (program_id,))

        curriculum = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return curriculum

    def get_program_sources(self, program_id):
        """Get all sources for a program"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM sources
            WHERE program_id = ?
            ORDER BY reliability_score DESC
        ''', (program_id,))

        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return sources

    def save_lesson(self, program_id, lesson_id, lesson_data, sources):
        """Save or update lesson content with sources"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if lesson exists
        cursor.execute(
            'SELECT id FROM curriculum WHERE program_id = ? AND lesson_id = ?',
            (program_id, lesson_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE curriculum
                SET content = ?, title = ?, learning_objectives = ?, updated_at = CURRENT_TIMESTAMP
                WHERE program_id = ? AND lesson_id = ?
            ''', (
                json.dumps(lesson_data.get('content')),
                lesson_data.get('title'),
                json.dumps(lesson_data.get('learning_objectives', [])),
                program_id,
                lesson_id
            ))
        else:
            cursor.execute('''
                INSERT INTO curriculum (program_id, lesson_id, title, content, learning_objectives)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                program_id,
                lesson_id,
                lesson_data.get('title'),
                json.dumps(lesson_data.get('content')),
                json.dumps(lesson_data.get('learning_objectives', []))
            ))

        # Save sources
        for source in sources:
            cursor.execute('''
                INSERT INTO sources (program_id, lesson_id, url, title, source_type, reliability_score, citation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                program_id,
                lesson_id,
                source.get('url'),
                source.get('title'),
                source.get('type'),
                source.get('reliability_score', 0.8),
                source.get('citation')
            ))

        conn.commit()
        conn.close()

    def get_lesson(self, program_id, lesson_id):
        """Get lesson content"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM curriculum
            WHERE program_id = ? AND lesson_id = ?
        ''', (program_id, lesson_id))

        row = cursor.fetchone()
        conn.close()

        if row:
            lesson = dict(row)
            if lesson.get('content'):
                lesson['content'] = json.loads(lesson['content'])
            if lesson.get('learning_objectives'):
                lesson['learning_objectives'] = json.loads(lesson['learning_objectives'])
            return lesson

        return None

    def save_feedback(self, student_id, program_id, lesson_id, rating, comments, helpful=True):
        """Save student feedback"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO feedback (student_id, program_id, lesson_id, rating, comments, helpful)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, program_id, lesson_id, rating, comments, helpful))

        conn.commit()
        feedback_id = cursor.lastrowid
        conn.close()

        return feedback_id

    def get_student_progress(self, student_id):
        """Get comprehensive student progress"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all enrollments
        cursor.execute('''
            SELECT e.*, p.name as program_name
            FROM enrollments e
            LEFT JOIN programs p ON e.program_id = p.id
            WHERE e.student_id = ?
        ''', (student_id,))

        enrollments = [dict(row) for row in cursor.fetchall()]

        progress_data = {
            "enrollments": enrollments,
            "programs": []
        }

        for enrollment in enrollments:
            program_id = enrollment['program_id']

            # Get progress for this program
            cursor.execute('''
                SELECT COUNT(*) as total_lessons
                FROM curriculum
                WHERE program_id = ?
            ''', (program_id,))
            total = cursor.fetchone()['total_lessons']

            cursor.execute('''
                SELECT COUNT(*) as completed_lessons
                FROM progress
                WHERE student_id = ? AND program_id = ? AND status = 'completed'
            ''', (student_id, program_id))
            completed = cursor.fetchone()['completed_lessons']

            completion_percentage = (completed / total * 100) if total > 0 else 0

            progress_data['programs'].append({
                "program_id": program_id,
                "total_lessons": total,
                "completed_lessons": completed,
                "completion_percentage": round(completion_percentage, 2)
            })

        # Calculate overall completion
        if progress_data['programs']:
            avg_completion = sum(p['completion_percentage'] for p in progress_data['programs']) / len(progress_data['programs'])
            progress_data['completion_percentage'] = round(avg_completion, 2)
        else:
            progress_data['completion_percentage'] = 0

        # Get certificates
        cursor.execute('''
            SELECT * FROM certificates WHERE student_id = ?
        ''', (student_id,))
        progress_data['certificates_earned'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return progress_data

    def issue_certificate(self, student_id, program_id):
        """Issue a certificate"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Generate verification code
        verification_code = hashlib.sha256(
            f"{student_id}-{program_id}-{datetime.now()}".encode()
        ).hexdigest()[:16].upper()

        certificate_id = f"CERT-{verification_code}"

        cursor.execute('''
            INSERT INTO certificates (id, student_id, program_id, verification_code)
            VALUES (?, ?, ?, ?)
        ''', (certificate_id, student_id, program_id, verification_code))

        # Update enrollment status
        cursor.execute('''
            UPDATE enrollments
            SET status = 'completed', completion_date = CURRENT_TIMESTAMP
            WHERE student_id = ? AND program_id = ?
        ''', (student_id, program_id))

        conn.commit()
        conn.close()

        return {
            "certificate_id": certificate_id,
            "verification_code": verification_code,
            "issued_date": datetime.now().isoformat()
        }

    def add_source(self, program_id, url, title, reliability_score):
        """Add a verified source"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sources (program_id, url, title, reliability_score)
            VALUES (?, ?, ?, ?)
        ''', (program_id, url, title, reliability_score))

        conn.commit()
        conn.close()

    def create_deployment(self, company_id, program_ids, employee_ids, deadline=None):
        """Create HR deployment"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO hr_deployments (company_id, program_ids, employee_ids, deadline)
            VALUES (?, ?, ?, ?)
        ''', (
            company_id,
            json.dumps(program_ids),
            json.dumps(employee_ids),
            deadline
        ))

        deployment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return deployment_id

    def enroll_employee(self, employee_id, program_id, company_id):
        """Enroll an employee in a program"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO enrollments (student_id, program_id, company_id)
            VALUES (?, ?, ?)
        ''', (employee_id, program_id, company_id))

        enrollment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return enrollment_id

    def get_certification_path(self, program_id):
        """Get certification requirements and path"""
        # This would detail actual certification requirements
        # For now, return a structured path
        return {
            "program_id": program_id,
            "requirements": [
                "Complete all course modules",
                "Pass all assessments with 70% or higher",
                "Complete hands-on projects",
                "Pass final certification exam"
            ],
            "preparation": "Self-paced online learning with AI assistance",
            "assessment_type": "Online proctored exam available"
        }

    def get_total_students(self):
        """Get total number of students"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM students')
        count = cursor.fetchone()['count']
        conn.close()
        return count

    def get_total_certificates(self):
        """Get total certificates issued"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM certificates')
        count = cursor.fetchone()['count']
        conn.close()
        return count

    def get_average_completion_rate(self):
        """Get average completion rate across all students"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT AVG(
                CAST(
                    (SELECT COUNT(*) FROM progress p
                     WHERE p.student_id = e.student_id
                     AND p.program_id = e.program_id
                     AND p.status = 'completed') AS REAL
                ) / NULLIF(
                    (SELECT COUNT(*) FROM curriculum c
                     WHERE c.program_id = e.program_id), 0
                ) * 100
            ) as avg_completion
            FROM enrollments e
        ''')

        result = cursor.fetchone()
        conn.close()

        return round(result['avg_completion'] or 0, 2)

    def get_feedback_summary(self):
        """Get feedback summary statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                AVG(rating) as avg_rating,
                COUNT(*) as total_feedback,
                SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count
            FROM feedback
        ''')

        result = dict(cursor.fetchone())
        conn.close()

        return {
            "average_rating": round(result['avg_rating'] or 0, 2),
            "total_feedback": result['total_feedback'],
            "helpful_percentage": round(
                (result['helpful_count'] / result['total_feedback'] * 100)
                if result['total_feedback'] > 0 else 0,
                2
            )
        }
