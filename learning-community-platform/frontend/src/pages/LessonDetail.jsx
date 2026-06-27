import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

export default function LessonDetail() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);

  const fetchLesson = useCallback(async () => {
    try {
      const r = await api.get(`/lessons/${id}`);
      setLesson(r.data.lesson);
      if (user) {
        const p = await api.get(`/lessons/${id}/progress`).catch(() => ({ data: { progress: null } }));
        setProgress(p.data.progress);
      }
    } catch {
      toast.error('Lesson not found');
      navigate('/lessons');
    } finally { setLoading(false); }
  }, [id, user, navigate]);

  useEffect(() => { fetchLesson(); }, [fetchLesson]);

  const markComplete = async () => {
    if (!user) { toast.error('Sign in to track progress'); return; }
    setCompleting(true);
    try {
      await api.post(`/lessons/${id}/complete`);
      toast.success('Lesson completed! +10 karma');
      setProgress({ completed: true, completed_at: new Date().toISOString() });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to mark complete');
    } finally { setCompleting(false); }
  };

  if (loading) return <div className="card text-center py-12 text-gray-400">Loading lesson…</div>;
  if (!lesson) return null;

  const completed = progress?.completed;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={() => navigate('/lessons')} className="text-sm text-primary-600 hover:underline">← Back to lessons</button>

      <div className="card">
        <div className="flex flex-wrap gap-2 mb-3">
          <span className="badge badge-common">{lesson.topic_name || lesson.category}</span>
          <span className={`badge ${lesson.difficulty === 'beginner' ? 'bg-green-100 text-green-800' : lesson.difficulty === 'intermediate' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'} dark:bg-opacity-30`}>
            {lesson.difficulty}
          </span>
          {completed && <span className="badge bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">✓ Completed</span>}
          {lesson.credit_eligible && <span className="badge bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">🎓 Credit eligible</span>}
        </div>

        <h1 className="text-2xl font-bold mb-2">{lesson.title}</h1>

        {lesson.description && (
          <p className="text-gray-600 dark:text-gray-400 mb-4">{lesson.description}</p>
        )}

        <div className="flex items-center gap-4 text-sm text-gray-500 pb-4 mb-4 border-b dark:border-gray-700">
          <span>👤 {lesson.teacher_name || lesson.display_name || 'Instructor'}</span>
          {lesson.duration_minutes && <span>⏱ {lesson.duration_minutes} min</span>}
          <span>👁 {lesson.view_count || 0} views</span>
          <span>✓ {lesson.completion_count || 0} completions</span>
        </div>

        {lesson.content ? (
          <div className="prose dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap mb-6">
            {lesson.content}
          </div>
        ) : (
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 text-center mb-6">
            <div className="text-4xl mb-2">📚</div>
            <p className="text-gray-500">Lesson content will be displayed here</p>
          </div>
        )}

        {lesson.video_url && (
          <div className="mb-6">
            <h2 className="font-semibold mb-2">Video</h2>
            <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center">
              <a href={lesson.video_url} target="_blank" rel="noreferrer" className="text-white text-center">
                <div className="text-5xl mb-2">▶️</div>
                <p>Open video</p>
              </a>
            </div>
          </div>
        )}

        {lesson.resources && (
          <div className="mb-6">
            <h2 className="font-semibold mb-2">Resources</h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm whitespace-pre-wrap">{lesson.resources}</p>
          </div>
        )}

        <div className="flex gap-3">
          {!completed ? (
            <button onClick={markComplete} disabled={completing || !user}
              className="btn-primary">
              {completing ? 'Saving…' : '✓ Mark as complete (+10 karma)'}
            </button>
          ) : (
            <div className="flex items-center gap-2 text-green-600">
              <span className="text-xl">✅</span>
              <span className="font-medium">Completed on {new Date(progress.completed_at).toLocaleDateString()}</span>
            </div>
          )}
          {!user && <p className="text-sm text-gray-500 self-center">Sign in to track your progress</p>}
        </div>
      </div>
    </div>
  );
}
