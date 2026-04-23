import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const TopicDetail = () => {
  const { id } = useParams();
  const [topic, setTopic] = useState(null);
  const [joined, setJoined] = useState(false);
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    fetchTopic();
  }, [id]);

  const fetchTopic = async () => {
    try {
      const response = await api.get(`/topics/${id}`);
      setTopic(response.data.topic);
    } catch (error) {
      toast.error('Failed to load topic');
    }
  };

  const handleJoin = async (skillLevel) => {
    try {
      await api.post(`/topics/${id}/join`, { skillLevel });
      toast.success('Joined topic successfully!');
      setJoined(true);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to join');
    }
  };

  if (!topic) return <div>Loading...</div>;

  return (
    <div className="space-y-8">
      <div className="card">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 rounded-full text-4xl flex items-center justify-center" style={{backgroundColor: topic.color + '20'}}>
              {topic.icon_url || '📚'}
            </div>
            <div>
              <h1 className="text-3xl font-bold">{topic.name}</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">{topic.description}</p>
              <div className="flex items-center space-x-4 mt-4 text-sm">
                <span className="badge badge-common">{topic.category}</span>
                <span>👥 {topic.member_count} members</span>
              </div>
            </div>
          </div>
        </div>

        {isAuthenticated && !joined && (
          <div className="mt-6 space-y-3">
            <p className="font-medium">Select your skill level:</p>
            <div className="flex gap-2">
              <button onClick={() => handleJoin('beginner')} className="btn-secondary">Beginner</button>
              <button onClick={() => handleJoin('intermediate')} className="btn-secondary">Intermediate</button>
              <button onClick={() => handleJoin('advanced')} className="btn-secondary">Advanced</button>
            </div>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Link to={`/forum/${id}`} className="card hover:shadow-xl">
          <h3 className="text-xl font-bold mb-2">💬 Discussion Forum</h3>
          <p className="text-gray-600 dark:text-gray-400">Join conversations and ask questions</p>
        </Link>
        <Link to={`/lessons?topic=${id}`} className="card hover:shadow-xl">
          <h3 className="text-xl font-bold mb-2">📖 Lessons</h3>
          <p className="text-gray-600 dark:text-gray-400">Browse structured learning content</p>
        </Link>
      </div>
    </div>
  );
};

export default TopicDetail;
