import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const Topics = () => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    fetchTopics();
  }, []);

  const fetchTopics = async () => {
    try {
      const response = await api.get('/topics');
      setTopics(response.data.topics);
    } catch (error) {
      toast.error('Failed to load topics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading topics...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Explore Topics</h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          Choose from {topics.length} learning topics and join vibrant communities
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {topics.map((topic) => (
          <Link
            key={topic.id}
            to={`/topics/${topic.id}`}
            className="card hover:shadow-xl transition-all group"
          >
            <div className="flex items-center justify-between mb-4">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center text-3xl"
                style={{ backgroundColor: topic.color + '20' }}
              >
                {topic.icon_url || '📚'}
              </div>
              <span className="badge badge-common">{topic.category}</span>
            </div>
            <h3 className="text-xl font-bold mb-2 group-hover:text-primary-600">
              {topic.name}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
              {topic.description}
            </p>
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>👥 {topic.member_count} members</span>
              {isAuthenticated && (
                <span className="text-primary-600 font-medium">Join →</span>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Topics;
