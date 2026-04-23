import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';

const Lessons = () => {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ difficulty: 'all', sort: 'recent' });

  useEffect(() => {
    fetchLessons();
  }, [filter]);

  const fetchLessons = async () => {
    try {
      const params = new URLSearchParams();
      if (filter.difficulty !== 'all') params.append('difficulty', filter.difficulty);
      params.append('sort', filter.sort);

      const response = await api.get(`/lessons?${params}`);
      setLessons(response.data.lessons);
    } catch (error) {
      toast.error('Failed to load lessons');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold">Learning Library</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Explore curated lessons and courses</p>
        </div>
        <div className="flex gap-2 mt-4 md:mt-0">
          <select
            value={filter.difficulty}
            onChange={(e) => setFilter({...filter, difficulty: e.target.value})}
            className="input"
          >
            <option value="all">All Levels</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          <select
            value={filter.sort}
            onChange={(e) => setFilter({...filter, sort: e.target.value})}
            className="input"
          >
            <option value="recent">Recent</option>
            <option value="popular">Popular</option>
            <option value="rated">Top Rated</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading lessons...</div>
      ) : lessons.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No lessons found. Be the first to create one!</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {lessons.map((lesson) => (
            <Link key={lesson.id} to={`/lessons/${lesson.id}`} className="card hover:shadow-xl group">
              <div className="flex items-center justify-between mb-3">
                <span className={`badge ${lesson.difficulty_level === 'beginner' ? 'badge-common' : lesson.difficulty_level === 'intermediate' ? 'badge-rare' : 'badge-epic'}`}>
                  {lesson.difficulty_level}
                </span>
                {lesson.offers_credit && <span className="badge badge-legendary">Credit Available</span>}
              </div>
              <h3 className="text-xl font-bold mb-2 group-hover:text-primary-600">{lesson.title}</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">{lesson.description}</p>
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>By {lesson.display_name}</span>
                <div className="flex items-center space-x-2">
                  <span>⭐ {lesson.rating_avg?.toFixed(1) || 'N/A'}</span>
                  <span>👁 {lesson.view_count}</span>
                </div>
              </div>
              {lesson.is_ai_content && (
                <div className="mt-3 text-xs badge badge-common">
                  🤖 {lesson.ai_label || 'AI-Generated'}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default Lessons;
