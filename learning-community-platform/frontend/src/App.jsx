import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import useAuthStore from './store/authStore';

import Layout from './components/Layout';
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

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

export default function App() {
  return (
    <Router>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Public */}
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
          <Route path="profile/:username" element={<Profile />} />

          {/* Forum — uses ?topic= query param */}
          <Route path="forum" element={<Forum />} />
          <Route path="forum/post/:id" element={<PostDetail />} />

          {/* Protected */}
          <Route path="dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="messages" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
          <Route path="messages/:userId" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
          <Route path="profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="rewards" element={<ProtectedRoute><RewardsShop /></ProtectedRoute>} />
          <Route path="teacher/apply" element={<ProtectedRoute><TeacherApplication /></ProtectedRoute>} />
          <Route path="study-groups" element={<ProtectedRoute><StudyGroups /></ProtectedRoute>} />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" />} />
        </Route>
      </Routes>
    </Router>
  );
}
