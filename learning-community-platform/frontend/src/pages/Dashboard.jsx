import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const Dashboard = () => {
  const { user } = useAuthStore();
  const [stats, setStats] = useState({
    topics: [],
    streak: 0,
    karma: 0,
    points: 0
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [profileRes, topicsRes] = await Promise.all([
        api.get('/auth/profile'),
        api.get('/topics/user')
      ]);

      setStats({
        topics: topicsRes.data.topics,
        streak: profileRes.data.user.learning_streak,
        karma: profileRes.data.user.karma_points,
        points: profileRes.data.user.reward_points
      });
    } catch (error) {
      toast.error('Failed to load dashboard');
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold">Welcome back, {user?.display_name || user?.username}!</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">Here's your learning overview</p>
      </div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-4 gap-6">
        <div className="card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
          <div className="text-3xl font-bold">{stats.streak}</div>
          <div className="text-sm opacity-90">Day Streak 🔥</div>
        </div>
        <div className="card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <div className="text-3xl font-bold">{stats.karma}</div>
          <div className="text-sm opacity-90">Karma Points ⭐</div>
        </div>
        <div className="card bg-gradient-to-br from-pink-500 to-pink-600 text-white">
          <div className="text-3xl font-bold">{stats.points}</div>
          <div className="text-sm opacity-90">Reward Points 🏆</div>
        </div>
        <div className="card bg-gradient-to-br from-yellow-500 to-yellow-600 text-white">
          <div className="text-3xl font-bold">{stats.topics.length}</div>
          <div className="text-sm opacity-90">Topics Joined 📚</div>
        </div>
      </div>

      {/* My Topics */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-4">My Learning Topics</h2>
        {stats.topics.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>You haven't joined any topics yet.</p>
            <Link to="/topics" className="btn-primary mt-4 inline-block">
              Explore Topics
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.topics.map((topic) => (
              <Link
                key={topic.id}
                to={`/topics/${topic.id}`}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-2xl" style={{backgroundColor: topic.color + '20'}}>
                    {topic.icon_url || '📚'}
                  </div>
                  <div>
                    <h3 className="font-medium">{topic.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{topic.skill_level}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6">
        <Link to="/lessons" className="card hover:shadow-xl">
          <h3 className="text-xl font-bold mb-2">📖 Browse Lessons</h3>
          <p className="text-gray-600 dark:text-gray-400">Discover new courses and lessons</p>
        </Link>
        <Link to="/study-groups" className="card hover:shadow-xl">
          <h3 className="text-xl font-bold mb-2">👥 Study Groups</h3>
          <p className="text-gray-600 dark:text-gray-400">Join or create study groups</p>
        </Link>
        <Link to="/research" className="card hover:shadow-xl">
          <h3 className="text-xl font-bold mb-2">🔬 Research</h3>
          <p className="text-gray-600 dark:text-gray-400">Explore research papers</p>
        </Link>
      </div>
    </div>
  );
};

export default Dashboard;
