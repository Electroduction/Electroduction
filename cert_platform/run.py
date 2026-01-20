#!/usr/bin/env python3
"""
AI CertPro - Main Run Script
Complete certification platform with semantic search and adaptive learning

Usage:
    python run.py init                    # Initialize database
    python run.py populate                # Populate curriculum
    python run.py populate --program cybersecurity  # Populate specific program
    python run.py server                  # Start web server
    python run.py search "network security"         # Search curriculum
    python run.py search "python" --program it_software
    python run.py stats                   # Show statistics
    python run.py demo                    # Run demo/test
"""

import sys
import os
import argparse

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.comprehensive_curriculum import ComprehensiveCurriculumGenerator
from search.semantic_search import SemanticSearchEngine
from ai_engine.source_gatherer import SourceGatherer
from ai_engine.text_to_speech import TextToSpeechSystem
from ai_engine.user_suggestions import UserSuggestionSystem

def init_database():
    """Initialize database with all tables"""
    print("🔧 Initializing database...")
    db = DatabaseManager()
    db.initialize()
    print("✅ Database initialized successfully!\n")
    return db

def populate_curriculum(db, program_id=None):
    """Populate curriculum for all or specific program"""
    generator = ComprehensiveCurriculumGenerator(db)

    if program_id:
        print(f"📚 Populating curriculum for {program_id}...")
        result = generator.generate_complete_program(program_id)
        print(f"\n✅ Populated {program_id}:")
        print(f"   Full version: {result['full_version']['lessons']} lessons ({result['full_version']['hours']:.1f} hours)")
        print(f"   Summary version: {result['summary_version']['lessons']} lessons ({result['summary_version']['hours']:.1f} hours)")
    else:
        print("📚 Populating ALL programs...")
        programs = [
            'cybersecurity', 'it_software', 'nursing', 'electrician',
            'hvac', 'mechanical_engineering', 'cooking', 'finance',
            'accounting', 'business', 'education', 'ai_education'
        ]

        for prog in programs:
            try:
                result = generator.generate_complete_program(prog)
                print(f"✓ {prog}: {result['full_version']['hours']:.1f}h full, {result['summary_version']['hours']:.1f}h summary")
            except Exception as e:
                print(f"✗ {prog}: Error - {str(e)}")

        print("\n✅ All programs populated!")

def search_curriculum(db, query, program_id=None):
    """Search curriculum using semantic search"""
    print(f"🔍 Searching for: '{query}'" + (f" in {program_id}" if program_id else " across all programs"))
    print()

    search_engine = SemanticSearchEngine(db)

    if program_id:
        results = search_engine.search_topics(query, program_id=program_id, limit=10)
    else:
        results = search_engine.search_topics(query, limit=10)

    if not results:
        print("❌ No results found.")
        return

    print(f"Found {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Program: {result['program_id']}")
        print(f"   Relevance: {result['relevance_score']:.2f}")
        print(f"   Duration: {result.get('estimated_hours', 0)*60:.0f} minutes")
        print()

def show_statistics(db):
    """Show platform statistics"""
    print("📊 Platform Statistics\n")

    conn = db.get_connection()
    cursor = conn.cursor()

    # Total programs
    cursor.execute("SELECT COUNT(DISTINCT program_id) as count FROM curriculum")
    total_programs = cursor.fetchone()['count']
    print(f"Programs: {total_programs}")

    # Total lessons
    cursor.execute("SELECT COUNT(*) as count FROM curriculum")
    total_lessons = cursor.fetchone()['count']
    print(f"Total Lessons: {total_lessons}")

    # Total hours
    cursor.execute("SELECT SUM(estimated_hours) as hours FROM curriculum")
    total_hours = cursor.fetchone()['hours'] or 0
    print(f"Total Content: {total_hours:.1f} hours")

    # By program
    cursor.execute("""
        SELECT program_id,
               COUNT(*) as lessons,
               SUM(estimated_hours) as hours
        FROM curriculum
        GROUP BY program_id
        ORDER BY program_id
    """)

    print("\nBy Program:")
    for row in cursor.fetchall():
        print(f"  {row['program_id']}: {row['lessons']} lessons, {row['hours']:.1f} hours")

    # Students
    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()['count']
    print(f"\nTotal Students: {total_students}")

    # Certificates issued
    cursor.execute("SELECT COUNT(*) as count FROM certificates")
    total_certs = cursor.fetchone()['count']
    print(f"Certificates Issued: {total_certs}")

    conn.close()

def start_server():
    """Start Flask web server"""
    print("🚀 Starting AI CertPro server...")
    print("   URL: http://localhost:5000")
    print("   Press Ctrl+C to stop\n")

    from backend.app import app
    app.run(host='0.0.0.0', port=5000, debug=True)

def run_demo(db):
    """Run demonstration of platform features"""
    print("🎯 Running AI CertPro Demo\n")

    # 1. Search demo
    print("=" * 50)
    print("DEMO 1: Semantic Search")
    print("=" * 50)
    search_curriculum(db, "network security")

    # 2. Curriculum hierarchy
    print("\n" + "=" * 50)
    print("DEMO 2: Curriculum Hierarchy")
    print("=" * 50)
    search_engine = SemanticSearchEngine(db)
    hierarchy = search_engine.get_curriculum_hierarchy('cybersecurity')
    print(f"Program: {hierarchy['program_id']}")
    print(f"Total Lessons: {hierarchy['total_lessons']}")
    print(f"Total Hours: {hierarchy['total_hours']:.1f}")

    # 3. Related topics
    print("\n" + "=" * 50)
    print("DEMO 3: Finding Related Topics")
    print("=" * 50)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lesson_id FROM curriculum LIMIT 1")
    sample_lesson = cursor.fetchone()
    conn.close()

    if sample_lesson:
        related = search_engine.find_related_topics(sample_lesson['lesson_id'])
        print(f"Related topics for: {sample_lesson['lesson_id']}")
        for topic in related[:3]:
            print(f"  - {topic['title']} (similarity: {topic['similarity_score']:.2f})")

    # 4. Text-to-speech
    print("\n" + "=" * 50)
    print("DEMO 4: Text-to-Speech System")
    print("=" * 50)
    tts = TextToSpeechSystem()
    voices = tts.get_available_voices()
    print(f"Available voices: {len(voices)}")
    for voice in voices:
        print(f"  - {voice['name']}")

    print("\n✅ Demo completed!")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AI CertPro Platform')
    parser.add_argument('command', choices=['init', 'populate', 'server', 'search', 'stats', 'demo'],
                       help='Command to run')
    parser.add_argument('query', nargs='?', help='Search query (for search command)')
    parser.add_argument('--program', help='Specific program ID')

    args = parser.parse_args()

    # Initialize database manager
    db = DatabaseManager()

    if args.command == 'init':
        init_database()

    elif args.command == 'populate':
        populate_curriculum(db, args.program)

    elif args.command == 'server':
        start_server()

    elif args.command == 'search':
        if not args.query:
            print("Error: Search query required")
            print("Usage: python run.py search 'your query' [--program program_id]")
            sys.exit(1)
        search_curriculum(db, args.query, args.program)

    elif args.command == 'stats':
        show_statistics(db)

    elif args.command == 'demo':
        run_demo(db)

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
