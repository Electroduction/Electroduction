"""
Electroduction Portfolio API
FastAPI backend with 6 RESTful endpoints
Author: Kenny Situ
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import datetime

app = FastAPI(
    title="Electroduction Portfolio API",
    description="Backend API for Kenny Situ's developer portfolio",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ─────────────────────────────────────────────────────

class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str
    message: str

# ── Helpers ────────────────────────────────────────────────────

def utcnow() -> str:
    """Return current UTC time as ISO string (timezone-aware)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# ── Data ───────────────────────────────────────────────────────

PROJECTS = [
    {
        "id": 1,
        "title": "Cybersecurity AI System",
        "description": "AI-powered cybersecurity platform with threat detection, vulnerability scanning, and automated response capabilities.",
        "tech": ["Python", "Machine Learning", "FastAPI", "MongoDB"],
        "category": "cybersecurity",
        "github": "https://github.com/Electroduction/Electroduction",
        "status": "active",
        "highlights": ["Threat detection algorithms", "Automated vulnerability scanning", "Real-time monitoring"],
    },
    {
        "id": 2,
        "title": "EchoFrontier Game",
        "description": "A Python-based video game with AI-driven NPCs, procedural content generation, and advanced game mechanics.",
        "tech": ["Python", "Pygame", "AI/ML", "CustomTkinter"],
        "category": "game",
        "github": "https://github.com/Electroduction/Electroduction",
        "status": "active",
        "highlights": ["AI-driven NPCs", "Procedural generation", "Leaderboard system"],
    },
    {
        "id": 3,
        "title": "Finance AI Education Tool",
        "description": "Intelligent finance education platform with personalized learning paths and real-time market data integration.",
        "tech": ["Python", "FastAPI", "React", "FinTech APIs"],
        "category": "fintech",
        "github": "https://github.com/Electroduction/Electroduction",
        "status": "active",
        "highlights": ["Personalized learning", "Market data integration", "Portfolio tracking"],
    },
    {
        "id": 4,
        "title": "Music Generation AI",
        "description": "AI system that composes original music using deep learning models trained on diverse musical genres.",
        "tech": ["Python", "TensorFlow", "Music21", "NumPy"],
        "category": "ai",
        "github": "https://github.com/Electroduction/Electroduction",
        "status": "active",
        "highlights": ["Deep learning composition", "Multi-genre support", "MIDI export"],
    },
    {
        "id": 5,
        "title": "Video Content Creation AI",
        "description": "Automated video content pipeline with AI-powered scripting, scene generation, and post-production tools.",
        "tech": ["Python", "OpenCV", "FFmpeg", "GPT Integration"],
        "category": "ai",
        "github": "https://github.com/Electroduction/Electroduction",
        "status": "active",
        "highlights": ["Auto-scripting", "Scene generation", "Subtitle automation"],
    },
    {
        "id": 6,
        "title": "Art & Creativity AI",
        "description": "Generative art platform combining neural style transfer, image synthesis, and interactive creative tools.",
        "tech": ["Python", "PyTorch", "Stable Diffusion", "PIL"],
        "category": "ai",
        "github": "https://github.com/Electroduction/Electroduction",
        "status": "active",
        "highlights": ["Neural style transfer", "Image synthesis", "Interactive canvas"],
    },
]

STATS = {
    "projects": len(PROJECTS),
    "tests_passing": 19,
    "test_pass_rate": 100,
    "lines_of_code": 15000,
    "technologies": 20,
    "hours_developed": 200,
}

LEADERBOARD = [
    {"rank": 1,  "name": "Player_Alpha", "score": 98500, "level": 42, "games": 120},
    {"rank": 2,  "name": "NeonByte",     "score": 87200, "level": 38, "games": 95},
    {"rank": 3,  "name": "CyberKnight",  "score": 75600, "level": 35, "games": 80},
    {"rank": 4,  "name": "DataPunk",     "score": 68900, "level": 31, "games": 72},
    {"rank": 5,  "name": "ElectroAce",   "score": 55300, "level": 28, "games": 65},
    {"rank": 6,  "name": "BitWarden",    "score": 44700, "level": 24, "games": 53},
    {"rank": 7,  "name": "QuantumQ",     "score": 38100, "level": 21, "games": 45},
    {"rank": 8,  "name": "ShadowStack",  "score": 29800, "level": 18, "games": 38},
    {"rank": 9,  "name": "GlitchGuru",   "score": 21400, "level": 14, "games": 30},
    {"rank": 10, "name": "ByteBomber",   "score": 12600, "level": 10, "games": 22},
]

contact_messages: list = []

# ── Endpoints ──────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "Electroduction Portfolio API is running",
        "version": "1.0.0",
        "timestamp": utcnow(),
    }


@app.get("/api/projects", tags=["Projects"])
def get_projects(category: Optional[str] = None):
    """
    Get all portfolio projects.
    Optionally filter by category: cybersecurity | game | fintech | ai
    """
    if category:
        filtered = [p for p in PROJECTS if p["category"] == category]
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No projects found for category '{category}'")
        return {"projects": filtered, "count": len(filtered)}
    return {"projects": PROJECTS, "count": len(PROJECTS)}


@app.get("/api/projects/{project_id}", tags=["Projects"])
def get_project(project_id: int):
    """Get a single project by ID."""
    project = next((p for p in PROJECTS if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/api/stats", tags=["Stats"])
def get_stats():
    """Get portfolio statistics and key metrics."""
    return {**STATS, "last_updated": utcnow()}


@app.get("/api/leaderboard", tags=["Game"])
def get_leaderboard(limit: int = 10):
    """Get EchoFrontier game leaderboard. Default top 10."""
    limit = max(1, min(limit, len(LEADERBOARD)))
    return {
        "leaderboard": LEADERBOARD[:limit],
        "total_players": len(LEADERBOARD),
        "last_updated": utcnow(),
    }


@app.post("/api/contact", tags=["Contact"])
def send_contact(msg: ContactMessage):
    """Submit a contact form message."""
    if len(msg.message.strip()) < 10:
        raise HTTPException(status_code=422, detail="Message must be at least 10 characters.")
    entry = {
        "id": len(contact_messages) + 1,
        **msg.model_dump(),
        "received_at": utcnow(),
    }
    contact_messages.append(entry)
    return {
        "success": True,
        "message": f"Thanks {msg.name}! Your message has been received.",
        "id": entry["id"],
    }
