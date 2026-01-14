from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import json
import os

app = FastAPI(title="Electroduction Portfolio API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

class GameScore(BaseModel):
    player_name: str
    score: int
    level: int
    date: datetime = datetime.now()

class LeaderboardEntry(BaseModel):
    player_name: str
    score: int
    level: int
    date: datetime

# In-memory storage (replace with database in production)
DATA_DIR = "/home/user/Electroduction/website/backend/data"
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename: str, default=None):
    """Load JSON data from file"""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else []

def save_data(filename: str, data):
    """Save data to JSON file"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Electroduction Portfolio API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "game_stats": "/api/game/stats",
            "leaderboard": "/api/game/leaderboard",
            "submit_score": "/api/game/score",
            "contact": "/api/contact"
        }
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/game/stats")
async def get_game_stats():
    """Get overall game statistics"""
    leaderboard = load_data("leaderboard.json", [])

    total_players = len(set(entry["player_name"] for entry in leaderboard))
    total_runs = len(leaderboard)
    highest_level = max((entry["level"] for entry in leaderboard), default=0)
    bosses_defeated = sum(1 for entry in leaderboard if entry["level"] >= 5)

    return {
        "total_players": total_players,
        "total_runs": total_runs,
        "highest_level": highest_level,
        "bosses_defeated": bosses_defeated
    }

@app.get("/api/game/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = 10):
    """Get top scores"""
    leaderboard = load_data("leaderboard.json", [])

    # Sort by score descending
    sorted_leaderboard = sorted(
        leaderboard,
        key=lambda x: x["score"],
        reverse=True
    )[:limit]

    return sorted_leaderboard

@app.post("/api/game/score")
async def submit_score(score: GameScore):
    """Submit a new game score"""
    leaderboard = load_data("leaderboard.json", [])

    new_entry = {
        "player_name": score.player_name,
        "score": score.score,
        "level": score.level,
        "date": score.date.isoformat()
    }

    leaderboard.append(new_entry)
    save_data("leaderboard.json", leaderboard)

    return {
        "message": "Score submitted successfully",
        "rank": len([e for e in leaderboard if e["score"] > score.score]) + 1
    }

@app.post("/api/contact")
async def submit_contact(message: ContactMessage):
    """Submit a contact message"""
    messages = load_data("messages.json", [])

    new_message = {
        "name": message.name,
        "email": message.email,
        "message": message.message,
        "timestamp": datetime.now().isoformat()
    }

    messages.append(new_message)
    save_data("messages.json", messages)

    return {"message": "Message received successfully"}

@app.get("/api/projects")
async def get_projects():
    """Get project information"""
    return {
        "projects": [
            {
                "id": "electroduction",
                "name": "Electroduction",
                "description": "AAA Roguelike Game",
                "tech": ["Python", "Pygame"],
                "stats": {
                    "lines_of_code": 5000,
                    "files": 24,
                    "systems": ["Combat", "Dungeon Gen", "AI", "Audio"]
                }
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
