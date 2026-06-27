# AI CertPro - Complete Usage Guide

## Quick Start

```bash
# 1. Initialize the database
python run.py init

# 2. Populate curriculum (all programs)
python run.py populate

# 3. Populate specific program
python run.py populate --program cybersecurity

# 4. Start the web server
python run.py server

# 5. Search curriculum
python run.py search "network security"
python run.py search "python programming" --program it_software

# 6. View statistics
python run.py stats

# 7. Run demo
python run.py demo
```

## Detailed Features

### 1. Comprehensive Curriculum (8-10+ Hours Each Program)

Every program includes:
- **Full Version**: 8-12 hours of detailed instruction (20-30 lessons @ 25 min each)
- **Summary Version**: 2-5 hours of condensed essentials (8-12 lessons @ 25 min each)
- **Quality**: Matches or exceeds industry certificate programs

#### Content Structure:
```
Main Topic (Module)
├── Main Section
│   ├── Section
│   │   ├── Subsection (Lesson - 25 min)
│   │   ├── Subsection (Lesson - 25 min)
│   │   └── Subsection (Lesson - 25 min)
│   └── Section
│       └── Subsections...
└── Main Section...
```

#### Each 25-Minute Lesson Includes:
- Learning Objectives (3-5 specific outcomes)
- Introduction (context and importance)
- Detailed Content (5000-6000 words)
  - Core concepts with explanations
  - Step-by-step guides
  - Technical details
- Real-World Case Studies
- Practical Exercises
- Common Challenges and Solutions
- Best Practices
- Industry Insights
- Hands-On Activities
- Knowledge Check Questions
- Summary and Key Takeaways
- Further Reading Resources

### 2. Semantic Search

Search across all curriculum content intelligently:

```bash
# Search all programs
python run.py search "encryption"

# Search specific program
python run.py search "patient care" --program nursing

# Programmatic search
from search.semantic_search import SemanticSearchEngine
from database.db_manager import DatabaseManager

db = DatabaseManager()
search = SemanticSearchEngine(db)

# Topic search
results = search.search_topics("network security", program_id="cybersecurity")

# Keyword search
results = search.search_by_keywords(["python", "programming", "loops"])

# Find related topics
related = search.find_related_topics("cyber_001")

# Search by learning objective
results = search.search_by_learning_objective("understand TCP/IP")

# Cross-program search
all_results = search.search_across_programs("machine learning")
```

### 3. Text-to-Speech (Radio Mode)

Listen to lessons like an audiobook or radio program:

```python
from ai_engine.text_to_speech import TextToSpeechSystem

tts = TextToSpeechSystem()

# Generate audio for lesson
audio = tts.generate_lesson_audio(lesson_data, voice_id="professional_female")
# Returns: audio_url, duration, file_size

# Available voices
voices = tts.get_available_voices()
# - Professional Female
# - Professional Male
# - Friendly Instructor

# Generate section audio
section_audio = tts.generate_section_audio(section_text, "section_001")

# Create playlist
playlist = tts.generate_playlist("cybersecurity", ["cyber_001", "cyber_002", "cyber_003"])
```

#### Web Interface:
```html
<!-- Lesson page will include -->
<button id="read-aloud">🔊 Play Lesson Audio</button>
<audio id="lesson-player" src="/static/audio/lessons/{audio_id}.mp3" controls></audio>
```

### 4. User Suggestions & Voting System

Students can suggest changes - 75% agreement triggers admin review:

```python
from ai_engine.user_suggestions import UserSuggestionSystem

suggestion_system = UserSuggestionSystem(db)

# Submit suggestion
suggestion_id = suggestion_system.submit_suggestion(
    student_id=123,
    program_id="cybersecurity",
    lesson_id="cyber_001",
    suggestion_data={
        'type': 'content_update',
        'current_content': 'Original text...',
        'suggested_content': 'Improved text...',
        'reason': 'The current explanation is confusing. This version is clearer.'
    }
)

# Vote on suggestion
vote_result = suggestion_system.vote_on_suggestion(
    suggestion_id=suggestion_id,
    student_id=456,
    vote=True,  # True = agree, False = disagree
    comment="This is much clearer!"
)

# Check if threshold met (75%)
if vote_result['threshold_met']:
    print(f"Suggestion flagged for admin review!")
    print(f"Agreement: {vote_result['agreement_percentage']}%")

# Admin review
suggestion_system.admin_review_suggestion(
    suggestion_id=suggestion_id,
    admin_id=1,
    action='approve',  # or 'reject', 'modify'
    admin_notes='Excellent suggestion, approved for inclusion'
)
```

#### Web Interface:
```html
<!-- Lesson page -->
<button id="suggest-change">✏️ Suggest Improvement</button>

<!-- Suggestion modal -->
<form id="suggestion-form">
    <textarea name="current">Current text to improve</textarea>
    <textarea name="suggested">Your suggested improvement</textarea>
    <textarea name="reason">Why is this better?</textarea>
    <button type="submit">Submit Suggestion</button>
</form>

<!-- View suggestions -->
<div class="suggestion">
    <p>Current: "The CIA triad stands for..."</p>
    <p>Suggested: "The CIA triad—Confidentiality, Integrity, Availability—forms..."</p>
    <div class="votes">
        <span>85% agree (17/20 votes)</span>
        <button class="vote-agree">👍 Agree</button>
        <button class="vote-disagree">👎 Disagree</button>
    </div>
</div>
```

### 5. Adaptive Configuration

Easily configure programs via `config/programs_config.json`:

```json
{
  "programs": {
    "custom_program": {
      "name": "Custom Certificate Program",
      "target_hours_full": 10,
      "target_hours_summary": 3,
      "difficulty": "intermediate",
      "modules": [
        {
          "name": "Module 1",
          "hours": 2,
          "lessons": 5
        }
      ]
    }
  },
  "settings": {
    "min_lesson_minutes": 25,
    "suggestion_approval_threshold": 0.75
  }
}
```

### 6. Mini-Certificates

Earn certificates for completing subsections:

```python
# Award mini-certificate
db = DatabaseManager()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    INSERT INTO mini_certificates (
        student_id, program_id, curriculum_id,
        certificate_type, verification_code
    ) VALUES (?, ?, ?, ?, ?)
''', (student_id, program_id, curriculum_id, 'subsection', verification_code))
```

Students collect mini-certificates as they progress through:
- Subsections (individual lessons)
- Sections (groups of lessons)
- Main Sections (modules)
- Complete Program (final certificate)

### 7. Source Grounding

All content linked to authoritative sources:

```python
from ai_engine.source_gatherer import SourceGatherer

gatherer = SourceGatherer()

# Gather sources for topic
sources = gatherer.gather_sources(
    topic="Network Security Fundamentals",
    program="cybersecurity",
    subtopic="Firewalls"
)

# Gather images
images = gatherer.gather_images(
    topic="Network Topology",
    program="cybersecurity"
)

# Gather videos
videos = gatherer.gather_videos(
    topic="Python Tutorial",
    program="it_software"
)

# Comprehensive resources
resources = gatherer.gather_comprehensive_resources(
    topic="HVAC Installation",
    program="hvac"
)
# Returns: sources, images, videos, total_resources
```

### 8. Database Schema

#### Key Tables:
- **curriculum** - All lessons with hierarchy (main→section→subsection)
- **sources** - Source URLs with reliability scores
- **content_suggestions** - User-submitted improvements
- **suggestion_votes** - Voting on suggestions
- **audio_cache** - Text-to-speech audio files
- **mini_certificates** - Subsection completion certificates
- **lesson_resources** - Images, videos, links per lesson

## API Endpoints

### Student Enrollment
```bash
POST /api/enroll
{
  "name": "John Doe",
  "email": "john@example.com",
  "program_id": "cybersecurity",
  "prior_knowledge": {
    "years_experience": 2,
    "education_level": "bachelors"
  }
}
```

### Search Curriculum
```bash
GET /api/search?q=network+security&program=cybersecurity
```

### Get Lesson with Audio
```bash
GET /api/lesson/cybersecurity/cyber_001
{
  "lesson": {...},
  "audio_url": "/static/audio/lessons/{id}.mp3",
  "duration": "25:30",
  "sources": [...],
  "images": [...],
  "related_topics": [...]
}
```

### Submit Suggestion
```bash
POST /api/suggestion
{
  "student_id": 123,
  "lesson_id": "cyber_001",
  "suggested_content": "...",
  "reason": "..."
}
```

### Vote on Suggestion
```bash
POST /api/suggestion/vote
{
  "suggestion_id": 456,
  "student_id": 123,
  "vote": true,
  "comment": "Great improvement!"
}
```

## Advanced Usage

### Custom Curriculum Generation
```python
from database.comprehensive_curriculum import ComprehensiveCurriculumGenerator

generator = ComprehensiveCurriculumGenerator(db)

# Generate with custom parameters
curriculum = generator.generate_full_curriculum("cybersecurity")
summary = generator.generate_summary_curriculum("cybersecurity", curriculum)

# Save to database
generator._save_curriculum("cybersecurity", curriculum, "full")
generator._save_curriculum("cybersecurity", summary, "summary")
```

### Export Search Index
```python
search_engine = SemanticSearchEngine(db)
index = search_engine.export_search_index("search_index.json")
```

### Batch Operations
```python
# Enroll multiple students
students = [
    {"name": "Alice", "email": "alice@company.com", "program_id": "it_software"},
    {"name": "Bob", "email": "bob@company.com", "program_id": "cybersecurity"}
]

for student in students:
    db.create_student(**student)

# Generate audio for all lessons
lessons = db.get_curriculum("cybersecurity")
for lesson in lessons:
    audio = tts.generate_lesson_audio(lesson)
    print(f"Generated: {audio['audio_url']}")
```

## Troubleshooting

### Database not initialized
```bash
python run.py init
```

### Missing curriculum
```bash
python run.py populate
```

### Search returns no results
```bash
# Check if curriculum populated
python run.py stats

# Repopulate if needed
python run.py populate --program cybersecurity
```

### Audio files not generating
```
# Check audio cache directory exists
mkdir -p static/audio/lessons

# In production, configure TTS API keys:
export GOOGLE_TTS_API_KEY="your_key"
```

## Production Deployment

1. **Database**: Migrate from SQLite to PostgreSQL
2. **TTS**: Configure Google Cloud TTS, Amazon Polly, or ElevenLabs
3. **Search**: Implement actual vector embeddings (sentence-transformers)
4. **Caching**: Add Redis for session management
5. **CDN**: Serve audio files from CDN
6. **Web Server**: Use Gunicorn + Nginx

See `DEPLOYMENT.md` for full production setup.
