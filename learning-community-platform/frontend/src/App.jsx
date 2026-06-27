import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import useAuthStore from './store/authStore';

// Layout
import Layout from './components/Layout';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Topics from './pages/Topics';
import TopicDetail from './pages/TopicDetail';
import Forum from './pages/Forum';
import PostDetail from './pages/PostDetail';
import Lessons from './pages/Lessons';
import LessonDetail from './pages/LessonDetail';
import Research from './pages/Research';
import ResearchDetail from './pages/ResearchDetail';
import Messages from './pages/Messages';
import Profile from './pages/Profile';
import Leaderboard from './pages/Leaderboard';
import RewardsShop from './pages/RewardsShop';
import TeacherApplication from './pages/TeacherApplication';
import Contact from './pages/Contact';
import StudyGroups from './pages/StudyGroups';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="topics" element={<Topics />} />
          <Route path="topics/:id" element={<TopicDetail />} />
          <Route path="lessons" element={<Lessons />} />
          <Route path="lessons/:id" element={<LessonDetail />} />
          <Route path="research" element={<Research />} />
          <Route path="research/:id" element={<ResearchDetail />} />
          <Route path="leaderboard" element={<Leaderboard />} />
          <Route path="contact" element={<Contact />} />

          {/* Protected Routes */}
          <Route path="dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="forum/:topicId" element={<ProtectedRoute><Forum /></ProtectedRoute>} />
          <Route path="posts/:id" element={<ProtectedRoute><PostDetail /></ProtectedRoute>} />
          <Route path="messages" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
          <Route path="messages/:userId" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
          <Route path="profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="rewards" element={<ProtectedRoute><RewardsShop /></ProtectedRoute>} />
          <Route path="teacher/apply" element={<ProtectedRoute><TeacherApplication /></ProtectedRoute>} />
          <Route path="study-groups" element={<ProtectedRoute><StudyGroups /></ProtectedRoute>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
