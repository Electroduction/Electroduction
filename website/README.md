# ⚡ Electroduction Portfolio Website

A full-stack portfolio web application built with **React** (frontend) and **FastAPI** (backend), containerized with Docker.

---

## 🏗️ Architecture

```
website/
├── backend/          # FastAPI REST API
│   ├── main.py       # 6 API endpoints
│   ├── test_api.py   # 13 unit tests (100% pass)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React SPA
│   ├── src/
│   │   ├── api/client.js         # Axios API client
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # Responsive nav
│   │   │   ├── Hero.jsx          # Landing hero section
│   │   │   ├── Projects.jsx      # Filterable project showcase
│   │   │   ├── Stats.jsx         # Animated metrics + skill bars
│   │   │   ├── Leaderboard.jsx   # EchoFrontier game leaderboard
│   │   │   ├── Contact.jsx       # Validated contact form
│   │   │   └── Footer.jsx        # Footer with links
│   │   └── App.js
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## 🚀 Quick Start

### Option 1 — Docker (recommended)

```bash
cd website
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

### Option 2 — Local development

**Backend:**
```bash
cd website/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd website/frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/projects` | All projects (optional `?category=ai\|cybersecurity\|fintech\|game`) |
| GET | `/api/projects/{id}` | Single project by ID |
| GET | `/api/stats` | Portfolio metrics |
| GET | `/api/leaderboard` | Game leaderboard (optional `?limit=N`) |
| POST | `/api/contact` | Submit contact message |

Full interactive docs at: http://localhost:8000/docs

---

## ✅ Tests

```bash
cd website/backend
pytest test_api.py -v
```

**13 tests · 100% pass rate**

---

## 🎨 Frontend Components

| Component | Description |
|-----------|-------------|
| `Navbar` | Fixed responsive navbar with mobile hamburger menu |
| `Hero` | Animated landing with gradient text, tech pills, CTAs |
| `Projects` | Category-filtered project cards pulled from API |
| `Stats` | Animated counters + skill progress bars from API |
| `Leaderboard` | EchoFrontier top-10 player table from API |
| `Contact` | Validated form with real-time API submission |
| `Footer` | Links to GitHub, LinkedIn, and sections |

---

## ☁️ Deployment

### Vercel (frontend)
```bash
cd website/frontend
npm run build
# Deploy the build/ folder to Vercel
```

### Render / Railway (backend)
```bash
# Set start command: uvicorn main:app --host 0.0.0.0 --port $PORT
# Set REACT_APP_API_URL env var on frontend to your backend URL
```

### GitHub Actions CI
The project includes a workflow that runs tests on every push.

---

## 🛠️ Tech Stack

- **Frontend:** React 18, Axios, CSS custom properties
- **Backend:** FastAPI, Pydantic v2, Uvicorn
- **Testing:** pytest, httpx TestClient
- **Deployment:** Docker, Nginx, docker-compose
