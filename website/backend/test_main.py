import pytest
from fastapi.testclient import TestClient
from main import app, DATA_DIR
import os
import json

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_get_game_stats():
    """Test game stats endpoint"""
    response = client.get("/api/game/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_players" in data
    assert "total_runs" in data
    assert "highest_level" in data
    assert "bosses_defeated" in data

def test_get_leaderboard():
    """Test leaderboard endpoint"""
    response = client.get("/api/game/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_submit_score():
    """Test score submission"""
    score_data = {
        "player_name": "TestPlayer",
        "score": 1000,
        "level": 5
    }
    response = client.post("/api/game/score", json=score_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "rank" in data

def test_submit_contact():
    """Test contact form submission"""
    contact_data = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "This is a test message"
    }
    response = client.post("/api/contact", json=contact_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Message received successfully"

def test_get_projects():
    """Test projects endpoint"""
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert len(data["projects"]) > 0

def test_invalid_email_contact():
    """Test contact form with invalid email"""
    contact_data = {
        "name": "Test User",
        "email": "invalid-email",
        "message": "This is a test"
    }
    response = client.post("/api/contact", json=contact_data)
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
