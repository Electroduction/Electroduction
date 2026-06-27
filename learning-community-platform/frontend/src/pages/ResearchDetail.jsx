import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

export default function ResearchDetail() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchPaper = useCallback(async () => {
    try {
      const r = await api.get(`/research/${id}`);
      setPaper(r.data.paper);
    } catch {
      toast.error('Research paper not found');
      navigate('/research');
    } finally { setLoading(false); }
  }, [id, navigate]);

  useEffect(() => { fetchPaper(); }, [fetchPaper]);

  const requestCollab = async () => {
    if (!user) { toast.error('Sign in to collaborate'); return; }
    try {
      await api.post(`/research/${id}/collaborate`);
      toast.success('Collaboration request sent!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to send request');
    }
  };

  const cite = async () => {
    if (!user) { toast.error('Sign in to cite'); return; }
    try {
      await api.post(`/research/${id}/cite`);
      toast.success('Citation recorded');
      setPaper(p => ({ ...p, citation_count: (p.citation_count||0)+1 }));
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to cite');
    }
  };

  if (loading) return <div className="card text-center py-12 text-gray-400">Loading…</div>;
  if (!paper) return null;

  const keywords = paper.keywords
    ? (typeof paper.keywords === 'string' ? paper.keywords.split(',') : paper.keywords)
    : [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button onClick={() => navigate('/research')} className="text-sm text-primary-600 hover:underline">← Back to research</button>

      <div className="card">
        <div className="flex flex-wrap gap-2 mb-4">
          {paper.is_ai_content ? (
            <span className="badge bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">🤖 {paper.ai_label || 'AI-Assisted'}</span>
          ) : (
            <span className="badge bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">✍️ Human-Created</span>
          )}
          {paper.topic_name && <span className="badge badge-common">{paper.topic_name}</span>}
          {paper.status === 'draft' && <span className="badge bg-yellow-100 text-yellow-800">Draft</span>}
        </div>

        <h1 className="text-3xl font-bold mb-3">{paper.title}</h1>

        <div className="flex items-center gap-4 text-sm text-gray-500 mb-6 pb-6 border-b dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 text-xs font-bold">
              {(paper.display_name || paper.username || '?')[0].toUpperCase()}
            </div>
            <span className="font-medium">{paper.display_name || paper.username}</span>
          </div>
          <span>📖 {paper.view_count || 0} views</span>
          <span>🔗 {paper.citation_count || 0} citations</span>
          <span>{new Date(paper.published_at || paper.created_at).toLocaleDateString()}</span>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Abstract</h2>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{paper.abstract}</p>
        </div>

        {paper.content && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Full paper</h2>
            <div className="prose dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
              {paper.content}
            </div>
          </div>
        )}

        {keywords.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">Keywords</h2>
            <div className="flex flex-wrap gap-2">
              {keywords.map(k => <span key={k} className="badge badge-common">{k.trim()}</span>)}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-3 pt-4 border-t dark:border-gray-700">
          <button onClick={cite} className="btn-secondary text-sm">🔗 Cite this paper</button>
          {paper.seeking_collaborators && user && paper.user_id !== user.id && (
            <button onClick={requestCollab} className="btn-primary text-sm">🤝 Request to collaborate</button>
          )}
        </div>
      </div>
    </div>
  );
}
