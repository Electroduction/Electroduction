import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import useAuthStore from '../store/authStore';
import {
  HomeIcon,
  AcademicCapIcon,
  BookOpenIcon,
  BeakerIcon,
  ChatBubbleLeftRightIcon,
  TrophyIcon,
  UserGroupIcon,
  Bars3Icon,
  XMarkIcon,
  MoonIcon,
  SunIcon,
} from '@heroicons/react/24/outline';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true');
  const { isAuthenticated, user, logout } = useAuthStore();
  const navigate = useNavigate();

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', newMode);
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navigation = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Topics', href: '/topics', icon: AcademicCapIcon },
    { name: 'Lessons', href: '/lessons', icon: BookOpenIcon },
    { name: 'Research', href: '/research', icon: BeakerIcon },
    { name: 'Study Groups', href: '/study-groups', icon: UserGroupIcon, requiresAuth: true },
    { name: 'Messages', href: '/messages', icon: ChatBubbleLeftRightIcon, requiresAuth: true },
    { name: 'Leaderboard', href: '/leaderboard', icon: TrophyIcon },
  ];

  return (
    <div className="min-h-screen">
      {/* Top Navigation */}
      <nav className="bg-white dark:bg-gray-800 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {sidebarOpen ? (
                  <XMarkIcon className="h-6 w-6" />
                ) : (
                  <Bars3Icon className="h-6 w-6" />
                )}
              </button>
              <Link to="/" className="flex items-center ml-2">
                <span className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                  SkillSphere
                </span>
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {darkMode ? (
                  <SunIcon className="h-6 w-6 text-yellow-500" />
                ) : (
                  <MoonIcon className="h-6 w-6 text-gray-600" />
                )}
              </button>

              {isAuthenticated ? (
                <div className="flex items-center space-x-4">
                  <Link to="/rewards" className="btn-secondary text-sm">
                    🏆 {user?.reward_points || 0} Points
                  </Link>
                  <Link to="/profile" className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-medium">
                      {user?.username?.[0]?.toUpperCase()}
                    </div>
                    <span className="hidden md:block font-medium">{user?.username}</span>
                  </Link>
                  <button onClick={handleLogout} className="btn-secondary text-sm">
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Link to="/login" className="btn-secondary text-sm">
                    Login
                  </Link>
                  <Link to="/register" className="btn-primary text-sm">
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } md:translate-x-0 fixed md:sticky top-16 left-0 z-40 w-64 h-[calc(100vh-4rem)] transition-transform bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto`}
        >
          <nav className="p-4 space-y-2">
            {navigation.map((item) => {
              if (item.requiresAuth && !isAuthenticated) return null;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}

            {isAuthenticated && user?.is_teacher && (
              <Link
                to="/dashboard"
                className="flex items-center space-x-3 px-4 py-3 rounded-lg bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium"
                onClick={() => setSidebarOpen(false)}
              >
                <AcademicCapIcon className="h-6 w-6" />
                <span>Teacher Dashboard</span>
              </Link>
            )}

            {isAuthenticated && !user?.is_teacher && (
              <Link
                to="/teacher/apply"
                className="flex items-center space-x-3 px-4 py-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 font-medium"
                onClick={() => setSidebarOpen(false)}
              >
                <AcademicCapIcon className="h-6 w-6" />
                <span>Become a Teacher</span>
              </Link>
            )}

            <Link
              to="/contact"
              className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              onClick={() => setSidebarOpen(false)}
            >
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
              <span className="font-medium">Contact Us</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-h-[calc(100vh-4rem)]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
