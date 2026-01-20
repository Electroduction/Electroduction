# SkillSphere - Community Learning Hub 🚀

> **"Where Knowledge Grows Together"**

A comprehensive, gamified learning platform that combines community interaction, structured lessons, research collaboration, and real-time communication to create an engaging educational experience.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Features in Detail](#features-in-detail)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## 🌟 Overview

**SkillSphere** is a next-generation learning community platform that gamifies education and fosters meaningful connections between learners at all skill levels. Inspired by Discord's community model, it provides:

- **Interactive Learning Communities** - Join topic-based communities with learners at different skill levels
- **Comprehensive Lesson Library** - Access curated courses and create your own
- **Research Platform** - Publish research, find collaborators, and contribute to knowledge
- **Gamification System** - Earn karma points, badges, and rewards as you learn
- **Real-time Messaging** - Connect with fellow learners instantly
- **Credit Pathways** - Framework for college credit partnerships
- **AI Transparency** - Clear labeling of AI-generated vs. human-created content

---

## ✨ Features

### Core Features

#### 🎓 Learning & Education
- **Topic Exploration**: Browse 100+ curated subjects across multiple categories
- **Skill Levels**: Content tailored for beginner, intermediate, and advanced learners
- **Structured Lessons**: Complete courses with progress tracking and completion certificates
- **Credit System**: Framework for offering college credits (partnership-ready)

#### 💬 Community & Social
- **Discord-like Forums**: Topic-based discussion boards with threaded comments
- **Real-time Messaging**: Direct messages and group chats using Socket.IO
- **Study Groups**: Create or join study groups for collaborative learning
- **User Profiles**: Customizable profiles with bio, avatar, and achievement displays

#### 🏆 Gamification
- **Karma System**: Earn points through contributions and helpfulness
- **Ranking Tiers**: Bronze → Silver → Gold → Platinum → Diamond
- **Badges & Achievements**: Unlock special badges for milestones
- **Rewards Shop**: Purchase custom emojis, profile borders, and avatar frames
- **Leaderboards**: Compete on karma, streaks, and reward points

#### 🔬 Research & Collaboration
- **Research Publication**: Share your findings with the community
- **Collaboration Finder**: Find research partners and co-authors
- **Citation Tracking**: Track how your work influences others
- **AI Labeling**: Transparent marking of AI-assisted research

#### 👨‍🏫 Teaching
- **Teacher Applications**: Apply to become a verified teacher
- **Lesson Creation**: Build and publish comprehensive courses
- **Student Analytics**: Track lesson completion and engagement
- **Credit Offering**: Option to offer credit-bearing courses

#### 🤖 AI Integration
- **Content Labeling**: All AI-generated content clearly marked
- **Label Types**: "AI-Generated", "AI-Assisted", or "Human-Created"
- **Transparency**: Users always know the content source

#### 💰 Monetization
- **Google AdSense Integration**: Non-intrusive ad placement with close option
- **Premium Features**: Framework for future premium subscriptions
- **Rewards Economy**: Virtual currency system

---

## 🛠 Technology Stack

### Backend
- **Node.js** + **Express.js** - REST API server
- **SQLite** - Lightweight, file-based database
- **Socket.IO** - Real-time bidirectional communication
- **JWT** - Secure authentication
- **bcrypt** - Password hashing
- **Helmet** - Security middleware
- **CORS** - Cross-origin resource sharing

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Zustand** - State management
- **Axios** - HTTP client
- **React Hot Toast** - Toast notifications
- **Heroicons** - Icon library

### Development Tools
- **Jest** - Testing framework
- **Nodemon** - Auto-restart dev server
- **ESLint** - Code linting
- **PostCSS** + **Autoprefixer** - CSS processing

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18.0.0 or higher
- **npm** v9.0.0 or higher
- **Git**

### Installation

1. **Clone or navigate to the project**
   ```bash
   cd learning-community-platform
   ```

2. **Install Backend Dependencies**
   ```bash
   cd backend
   npm install
   ```

3. **Initialize Database**
   ```bash
   npm run init-db
   ```
   This creates the SQLite database with all tables and sample data.

4. **Install Frontend Dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the Backend Server** (Terminal 1)
   ```bash
   cd backend
   npm run dev
   ```
   Server runs on: `http://localhost:5000`

2. **Start the Frontend** (Terminal 2)
   ```bash
   cd frontend
   npm run dev
   ```
   App runs on: `http://localhost:5173`

3. **Open your browser**
   ```
   http://localhost:5173
   ```

### Default Test Accounts

After initializing the database, you can create accounts or use these test credentials:

- Register a new account at `/register`
- Login at `/login`

---

## 📁 Project Structure

```
learning-community-platform/
├── backend/
│   ├── config/
│   │   └── database.js           # Database connection
│   ├── controllers/              # Request handlers
│   │   ├── authController.js     # Auth logic
│   │   ├── topicsController.js   # Topics management
│   │   ├── forumController.js    # Forum posts/comments
│   │   ├── lessonsController.js  # Lessons/courses
│   │   ├── rewardsController.js  # Gamification
│   │   ├── researchController.js # Research papers
│   │   ├── messagingController.js # DMs
│   │   ├── teacherController.js  # Teacher apps
│   │   ├── notificationsController.js
│   │   └── studyGroupsController.js
│   ├── middleware/
│   │   └── auth.js               # JWT authentication
│   ├── routes/                   # API routes
│   ├── scripts/
│   │   └── initDatabase.js       # DB initialization
│   ├── tests/
│   │   └── api.test.js           # Test suite
│   ├── .env                      # Environment variables
│   ├── package.json
│   └── server.js                 # Entry point
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx        # App layout
│   │   │   └── GoogleAdPlaceholder.jsx
│   │   ├── pages/                # Route pages
│   │   │   ├── Home.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Topics.jsx
│   │   │   ├── TopicDetail.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Lessons.jsx
│   │   │   ├── Forum.jsx
│   │   │   ├── Research.jsx
│   │   │   ├── Messages.jsx
│   │   │   ├── Profile.jsx
│   │   │   ├── Leaderboard.jsx
│   │   │   ├── RewardsShop.jsx
│   │   │   ├── TeacherApplication.jsx
│   │   │   ├── Contact.jsx
│   │   │   └── StudyGroups.jsx
│   │   ├── store/
│   │   │   └── authStore.js      # Auth state
│   │   ├── utils/
│   │   │   └── api.js            # API client
│   │   ├── App.jsx               # Main app component
│   │   ├── main.jsx              # Entry point
│   │   └── index.css             # Global styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── test-platform.js              # Validation script
└── README.md                     # This file
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Authentication Endpoints

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "displayName": "string" (optional)
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

#### Get Profile
```http
GET /api/auth/profile
Authorization: Bearer {token}
```

### Topics Endpoints

```http
GET  /api/topics              # Get all topics
GET  /api/topics/:id          # Get topic details
POST /api/topics/:id/join     # Join a topic (auth required)
GET  /api/topics/user         # Get user's topics (auth required)
```

### Forum Endpoints

```http
GET  /api/forum/topics/:topicId/posts  # Get posts in topic
POST /api/forum/posts                  # Create post (auth required)
GET  /api/forum/posts/:id              # Get post details
POST /api/forum/posts/:id/vote         # Vote on post (auth required)
GET  /api/forum/posts/:postId/comments # Get comments
POST /api/forum/comments               # Create comment (auth required)
```

### Lessons Endpoints

```http
GET  /api/lessons             # Get all lessons
GET  /api/lessons/:id         # Get lesson details
POST /api/lessons             # Create lesson (teacher auth required)
POST /api/lessons/:id/start   # Start lesson (auth required)
POST /api/lessons/:id/complete # Complete lesson (auth required)
```

### Research Endpoints

```http
GET  /api/research            # Get research papers
POST /api/research            # Create paper (auth required)
GET  /api/research/:id        # Get paper details
POST /api/research/:id/publish # Publish paper (auth required)
```

### Gamification Endpoints

```http
GET  /api/gamification/rewards      # Get available rewards
POST /api/gamification/rewards/:id/purchase  # Purchase reward
GET  /api/gamification/badges       # Get badges
GET  /api/gamification/leaderboard  # Get leaderboard
```

### Messaging Endpoints

```http
GET  /api/messages/conversations    # Get conversations (auth required)
GET  /api/messages/:userId          # Get messages with user
POST /api/messages                  # Send message
```

---

## 🎯 Features in Detail

### Karma & Ranking System

Users earn karma points through positive contributions:

- **Creating a post**: +5 karma
- **Creating a comment**: +2 karma
- **Receiving an upvote**: +1 karma
- **Completing a lesson**: +10 karma
- **Publishing research**: +50 karma

**Ranking Levels:**
- Bronze: 0-99 karma
- Silver: 100-499 karma
- Gold: 500-1,999 karma
- Platinum: 2,000-4,999 karma
- Diamond: 5,000+ karma

### Reward Points System

Separate from karma, reward points are earned for:
- Completing lessons: +5 points
- Publishing research: +20 points
- Achieving milestones: Variable

Use reward points to purchase:
- Custom emojis (10-15 points)
- Profile borders (100-150 points)
- Animated avatar frames (200 points)
- Special badges (50-500 points)

### Learning Streaks

Daily login rewards encourage consistent learning:
- Login on consecutive days to build streak
- Streaks reset if you miss a day
- Special badges for 7, 30, 100, 365-day streaks

### AI Content Policy

All content must be labeled:
- **AI-Generated**: Fully created by AI
- **AI-Assisted**: Human-created with AI help
- **Human-Created**: No AI involvement

Users can filter content based on these labels.

### Credit System

Framework for offering college credits:
- Teachers can mark lessons as credit-bearing
- Specify credit type (e.g., "Computer Science 101")
- Track completion for credit eligibility
- Partner integration ready for official credits

---

## 🧪 Testing

### Run Validation Script

```bash
node test-platform.js
```

This script checks:
- ✓ All files are present
- ✓ Dependencies are installed
- ✓ Database is initialized
- ✓ Features are implemented
- ✓ System requirements met

### Run Backend Tests

```bash
cd backend
npm test
```

### Manual Testing Checklist

1. **Authentication**
   - [ ] Register new user
   - [ ] Login with credentials
   - [ ] Access protected routes
   - [ ] Logout

2. **Topics**
   - [ ] Browse topics
   - [ ] Join a topic
   - [ ] View topic details
   - [ ] Leave a topic

3. **Forum**
   - [ ] Create a post
   - [ ] Comment on post
   - [ ] Upvote/downvote
   - [ ] View post details

4. **Lessons**
   - [ ] Browse lessons
   - [ ] Start a lesson
   - [ ] Track progress
   - [ ] Complete lesson

5. **Gamification**
   - [ ] View leaderboard
   - [ ] Purchase reward
   - [ ] Earn karma
   - [ ] View badges

6. **Research**
   - [ ] Create research paper
   - [ ] Publish paper
   - [ ] Browse papers
   - [ ] Find collaborators

7. **Messaging**
   - [ ] Send direct message
   - [ ] View conversations
   - [ ] Receive notifications

8. **Profile**
   - [ ] Update profile
   - [ ] View stats
   - [ ] Display badges

---

## 🚢 Deployment

### Environment Variables

Create `.env` files for production:

**Backend (.env)**
```env
NODE_ENV=production
PORT=5000
JWT_SECRET=your-super-secret-production-key
FRONTEND_URL=https://your-domain.com
```

**Frontend (.env.production)**
```env
VITE_API_URL=https://api.your-domain.com
```

### Build for Production

**Backend:**
```bash
cd backend
npm install --production
npm run init-db
npm start
```

**Frontend:**
```bash
cd frontend
npm run build
```

Serve the `dist/` folder with a static file server (Nginx, Apache, Vercel, Netlify).

### Recommended Hosting

- **Backend**: Heroku, Railway, Render, DigitalOcean
- **Frontend**: Vercel, Netlify, Cloudflare Pages
- **Database**: For production, consider PostgreSQL (easy migration from SQLite)

### Google AdSense Setup

1. Sign up for Google AdSense
2. Get your AdSense client ID
3. Update `/api/ads/config` endpoint in `server.js`
4. Replace placeholders in frontend ad components
5. Follow Google AdSense policies for ad placement

---

## 🤝 Contributing

We welcome contributions! Areas for improvement:

### High Priority
- [ ] Complete real-time messaging UI
- [ ] Implement notification system UI
- [ ] Add image upload for avatars
- [ ] Build admin dashboard
- [ ] Add content moderation tools

### Medium Priority
- [ ] Implement search functionality
- [ ] Add email notifications
- [ ] Create mobile app (React Native)
- [ ] Add video lesson support
- [ ] Implement live streaming for classes

### Low Priority
- [ ] Add more badge designs
- [ ] Create achievement animations
- [ ] Add theme customization
- [ ] Implement playlist creation
- [ ] Add bookmark/favorite feature

---

## 📝 License

This project is created for educational purposes.

---

## 🙏 Acknowledgments

Built with modern web technologies and inspired by the best learning platforms:

- **Discord** - Community interaction model
- **Reddit** - Karma and voting system
- **Coursera/Udemy** - Lesson structure
- **Stack Overflow** - Q&A format
- **GitHub** - Contribution model

---

## 📞 Support

For questions or issues:

- **GitHub Issues**: Report bugs and feature requests
- **Email**: support@skillsphere.com (example)
- **Discord**: Join our community server (example)
- **Contact Form**: Use the in-app contact page

---

## 🎉 Get Started!

Ready to launch your learning journey?

```bash
# Quick start
cd backend && npm install && npm run init-db && npm run dev
# In new terminal
cd frontend && npm install && npm run dev
```

Visit `http://localhost:5173` and create your account!

---

**Made with ❤️ for learners everywhere**
