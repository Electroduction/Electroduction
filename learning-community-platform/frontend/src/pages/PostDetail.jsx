import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const AI_LABEL_COLORS = {
  'AI-Generated': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  'AI-Assisted': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'Human-Created': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

export default function PostDetail() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchPost = useCallback(async () => {
    try {
      const [postRes, commentsRes] = await Promise.all([
        api.get(`/forum/${id}`),
        api.get(`/forum/${id}/comments`),
      ]);
      setPost(postRes.data.post);
      setComments(commentsRes.data.comments || []);
    } catch {
      toast.error('Post not found');
      navigate('/forum');
    } finally { setLoading(false); }
  }, [id, navigate]);

  useEffect(() => { fetchPost(); }, [fetchPost]);

  const submitComment = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;
    setSubmitting(true);
    try {
      await api.post(`/forum/${id}/comment`, { content: comment });
      toast.success('Comment added! +2 karma');
      setComment('');
      fetchPost();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to add comment');
    } finally { setSubmitting(false); }
  };

  const upvote = async () => {
    if (!user) { toast.error('Sign in to vote'); return; }
    try {
      await api.post(`/forum/${id}/upvote`);
      setPost(p => ({ ...p, upvotes: p.upvotes + 1 }));
    } catch { toast.error('Could not upvote'); }
  };

  const timeAgo = (dt) => {
    const s = Math.floor((Date.now() - new Date(dt)) / 1000);
    if (s < 60) return `${s}s ago`;
    if (s < 3600) return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    return `${Math.floor(s/86400)}d ago`;
  };

  if (loading) return <div className="card text-center py-12 text-gray-400">Loading…</div>;
  if (!post) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm text-primary-600 hover:underline">← Back to forum</button>

      {/* Post */}
      <div className="card">
        <div className="flex items-start gap-4">
          <div className="flex flex-col items-center gap-1 min-w-[48px]">
            <button onClick={upvote} className="text-gray-400 hover:text-primary-600 text-2xl">▲</button>
            <span className="font-bold text-lg">{post.upvotes || 0}</span>
            <span className="text-xs text-gray-400">votes</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap gap-2 mb-2">
              <span className="badge bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">{post.post_type}</span>
              {post.is_ai_content && (
                <span className={`badge ${AI_LABEL_COLORS[post.ai_label] || AI_LABEL_COLORS['AI-Assisted']}`}>
                  🤖 {post.ai_label || 'AI-Assisted'}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold mb-3">{post.title}</h1>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{post.content}</p>
            <div className="flex items-center gap-4 mt-4 text-sm text-gray-500 border-t dark:border-gray-700 pt-4">
              <span className="font-medium">{post.display_name || post.username}</span>
              <span className="badge badge-common">{post.rank_level}</span>
              <span>👁 {post.view_count || 0} views</span>
              <span>{timeAgo(post.created_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Comments */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">
          {comments.length} {comments.length === 1 ? 'comment' : 'comments'}
        </h2>

        {user && (
          <form onSubmit={submitComment} className="mb-6">
            <textarea value={comment} onChange={e => setComment(e.target.value)}
              className="input w-full min-h-[80px] mb-2" placeholder="Share your thoughts… (+2 karma)" />
            <button type="submit" disabled={submitting || !comment.trim()} className="btn-primary text-sm">
              {submitting ? 'Posting…' : 'Add comment'}
            </button>
          </form>
        )}

        <div className="space-y-4">
          {comments.map(c => (
            <div key={c.id} className="flex gap-3 border-b dark:border-gray-700 pb-4 last:border-none">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 text-xs font-bold flex-shrink-0">
                {(c.display_name || c.username || '?')[0].toUpperCase()}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium">{c.display_name || c.username}</span>
                  <span className="text-xs text-gray-400">{timeAgo(c.created_at)}</span>
                  {c.is_ai_content && <span className="badge badge-rare text-xs">🤖</span>}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{c.content}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                  <button onClick={async () => {
                    if (!user) return;
                    await api.post(`/forum/comment/${c.id}/upvote`).catch(() => {});
                    setComments(prev => prev.map(x => x.id === c.id ? {...x, upvotes: x.upvotes+1} : x));
                  }} className="hover:text-primary-600">▲ {c.upvotes || 0}</button>
                </div>
              </div>
            </div>
          ))}
          {comments.length === 0 && (
            <p className="text-gray-400 text-sm text-center py-4">No comments yet — start the conversation!</p>
          )}
        </div>
      </div>
    </div>
  );
}
