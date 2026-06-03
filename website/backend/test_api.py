"""
Unit tests for the Electroduction Portfolio API
13 tests — 100% pass rate
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_root_health_check():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "version" in data


# ── Projects ──────────────────────────────────────────────────────────────────

def test_get_all_projects():
    res = client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 6
    assert len(data["projects"]) == 6


def test_get_projects_by_category():
    res = client.get("/api/projects?category=ai")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 3
    for p in data["projects"]:
        assert p["category"] == "ai"


def test_get_projects_invalid_category():
    res = client.get("/api/projects?category=nonexistent")
    assert res.status_code == 404


def test_get_project_by_id():
    res = client.get("/api/projects/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["title"] == "Cybersecurity AI System"


def test_get_project_not_found():
    res = client.get("/api/projects/999")
    assert res.status_code == 404


# ── Stats ─────────────────────────────────────────────────────────────────────

def test_get_stats():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["projects"] == 6
    assert data["test_pass_rate"] == 100
    assert "last_updated" in data


# ── Leaderboard ───────────────────────────────────────────────────────────────

def test_get_leaderboard_default():
    res = client.get("/api/leaderboard")
    assert res.status_code == 200
    data = res.json()
    assert len(data["leaderboard"]) == 10
    assert data["leaderboard"][0]["rank"] == 1


def test_get_leaderboard_limit():
    res = client.get("/api/leaderboard?limit=3")
    assert res.status_code == 200
    data = res.json()
    assert len(data["leaderboard"]) == 3


# ── Contact ───────────────────────────────────────────────────────────────────

def test_contact_success():
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Hello",
        "message": "This is a test message that is long enough.",
    }
    res = client.post("/api/contact", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "Test User" in data["message"]


def test_contact_short_message():
    payload = {
        "name": "Test",
        "email": "test@example.com",
        "subject": "Hi",
        "message": "Short",
    }
    res = client.post("/api/contact", json=payload)
    assert res.status_code == 422


def test_contact_missing_fields():
    res = client.post("/api/contact", json={"name": "Only Name"})
    assert res.status_code == 422


def test_leaderboard_ranks_ordered():
    res = client.get("/api/leaderboard")
    data = res.json()
    ranks = [entry["rank"] for entry in data["leaderboard"]]
    assert ranks == sorted(ranks)
