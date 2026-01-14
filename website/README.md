# Electroduction Portfolio Website

A modern, full-stack portfolio website showcasing the Electroduction game and other projects by Kenny Situ.

## 🏗️ Architecture

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: CSS3 with CSS Variables
- **Testing**: Vitest + React Testing Library
- **Build**: Vite
- **Deployment**: Nginx (Docker)

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database**: JSON file storage (SQLite/PostgreSQL ready)
- **Testing**: Pytest
- **API Docs**: Auto-generated with FastAPI

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **Deployment**: Automated scripts

## 🚀 Quick Start

### Development Mode

```bash
# Option 1: Using the dev script
./dev-start.sh

# Option 2: Manual start
# Terminal 1 - Backend
cd backend
python3 main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production Deployment

```bash
# Using Docker Compose
./deploy.sh

# Or manually
docker-compose up -d --build
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test                 # Run once
npm run test:watch       # Watch mode
npm run build            # Production build
```

### Backend Tests
```bash
cd backend
python3 -m pytest test_main.py -v
```

## 📁 Project Structure

```
website/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.jsx          # Main app component
│   │   ├── App.css          # Global styles
│   │   └── App.test.jsx     # Tests
│   ├── Dockerfile           # Frontend container
│   ├── nginx.conf           # Nginx configuration
│   └── package.json
│
├── backend/                 # FastAPI application
│   ├── main.py             # API server
│   ├── test_main.py        # API tests
│   ├── Dockerfile          # Backend container
│   ├── requirements.txt    # Python dependencies
│   └── data/              # JSON storage
│
├── docker-compose.yml      # Multi-container setup
├── deploy.sh              # Production deployment
└── dev-start.sh          # Development startup
```

## 🎯 Features

### Implemented
- ✅ Responsive portfolio design
- ✅ Project showcase
- ✅ Game statistics display
- ✅ Leaderboard system
- ✅ Contact form
- ✅ RESTful API
- ✅ Unit tests (Frontend & Backend)
- ✅ Docker deployment
- ✅ Auto-generated API documentation

### API Endpoints
- `GET /api/health` - Health check
- `GET /api/game/stats` - Game statistics
- `GET /api/game/leaderboard` - Top scores
- `POST /api/game/score` - Submit score
- `POST /api/contact` - Contact form
- `GET /api/projects` - Project information

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:
```
# Backend configuration
PORT=8000
HOST=0.0.0.0
```

### Frontend API URL
Update in `src/App.jsx` and component files:
```javascript
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000'
```

## 📊 Technology Stack Decisions

| Component | Technology | Reasoning |
|-----------|-----------|-----------|
| Frontend Framework | React + Vite | Modern, fast, excellent DX |
| Backend Framework | FastAPI | High performance, auto-docs, async |
| Database | JSON Files | Simple, portable, easy to upgrade |
| Deployment | Docker | Reproducible, portable, scalable |
| Testing | Vitest + Pytest | Fast, modern, comprehensive |

## 🚢 Deployment Options

### Local/Development
- Use `./dev-start.sh` for development
- Use `./deploy.sh` for local production testing

### Cloud Deployment

#### Option 1: VPS (DigitalOcean, Linode, etc.)
```bash
# SSH into your VPS
git clone <repository>
cd website
./deploy.sh
```

#### Option 2: Heroku
- Use Heroku's container registry
- Deploy backend and frontend as separate apps

#### Option 3: Vercel + Railway
- Frontend: Vercel
- Backend: Railway

#### Option 4: AWS
- Frontend: S3 + CloudFront
- Backend: EC2 or ECS

## 📈 Performance

- Frontend build: ~206KB (gzipped: ~64KB)
- Backend response time: <50ms average
- Frontend tests: 5 tests in ~2.5s
- Backend tests: 8 tests in ~1.2s

## 🔐 Security Features

- CORS configuration
- Input validation with Pydantic
- Email validation
- Security headers (Nginx)
- No hardcoded secrets

## 🐛 Troubleshooting

**Backend won't start:**
```bash
pip install -r backend/requirements.txt
```

**Frontend build fails:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Docker issues:**
```bash
docker-compose down
docker system prune
docker-compose up --build
```

## 📝 License

This project is part of the Electroduction repository.

## 👤 Author

Kenny Situ - Software Developer, Cybersecurity Professional, AI Tutor
