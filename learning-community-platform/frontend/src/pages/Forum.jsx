import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const AI_LABEL_COLORS = {
  'AI-Generated': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  'AI-Assisted': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'Human-Created': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

const RANK_COLORS = {
  Diamond: 'text-purple-600', Platinum: 'text-blue-600',
  Gold: 'text-yellow-600', Silver: 'text-gray-500', Bronze: 'text-amber-700',
};

export default function Forum() {
  const { user } = useAuthStore();
  const [searchParams] = useSearchParams();
  const topicId = searchParams.get('topic');

  const [posts, setPosts] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(topicId || '');
  const [sort, setSort] = useState('recent');
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', content: '', isAiContent: false, aiLabel: '', postType: 'discussion' });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get('/topics').then(r => setTopics(r.data.topics || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedTopic) { setLoading(false); setPosts([]); return; }
    setLoading(true);
    api.get(`/forum/topic/${selectedTopic}?sort=${sort}`)
      .then(r => setPosts(r.data.posts || []))
      .catch(() => toast.error('Failed to load posts'))
      .finally(() => setLoading(false));
  }, [selectedTopic, sort]);

  const upvote = async (postId) => {
    if (!user) { toast.error('Sign in to vote'); return; }
    try {
      await api.post(`/forum/${postId}/upvote`);
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, upvotes: p.upvotes + 1 } : p));
    } catch { toast.error('Could not upvote'); }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) { toast.error('Title and content are required'); return; }
    setSubmitting(true);
    try {
      await api.post('/forum', { ...form, topicId: selectedTopic });
      toast.success('Post created! +5 karma');
      setShowCreate(false);
      setForm({ title: '', content: '', isAiContent: false, aiLabel: '', postType: 'discussion' });
      const r = await api.get(`/forum/topic/${selectedTopic}?sort=${sort}`);
      setPosts(r.data.posts || []);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create post');
    } finally { setSubmitting(false); }
  };

  const timeAgo = (dt) => {
    const s = Math.floor((Date.now() - new Date(dt)) / 1000);
    if (s < 60) return `${s}s ago`;
    if (s < 3600) return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    return `${Math.floor(s/86400)}d ago`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Forum</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Community discussion and knowledge sharing</p>
        </div>
        {user && selectedTopic && (
          <button onClick={() => setShowCreate(true)} className="btn-primary">+ New post</button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <select value={selectedTopic} onChange={e => setSelectedTopic(e.target.value)}
          className="input max-w-xs">
          <option value="">Select a topic…</option>
          {topics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <div className="flex gap-2">
          {['recent','popular','discussed'].map(s => (
            <button key={s} onClick={() => setSort(s)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${sort === s ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
              {s.charAt(0).toUpperCase()+s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {!selectedTopic ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">💬</div>
          <p className="text-gray-500">Select a topic to view its forum</p>
          <p className="text-sm text-gray-400 mt-2">Or <Link to="/topics" className="text-primary-600">browse all topics</Link></p>
        </div>
      ) : loading ? (
        <div className="card text-center py-12"><div className="text-gray-400">Loading posts…</div></div>
      ) : posts.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">🌱</div>
          <p className="text-gray-500">No posts yet — be the first!</p>
          {user && <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">Start a discussion</button>}
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map(post => (
            <Link key={post.id} to={`/forum/post/${post.id}`} className="block">
              <div className="card hover:shadow-lg transition-shadow cursor-pointer">
                <div className="flex items-start gap-3">
                  <button onClick={e => { e.preventDefault(); upvote(post.id); }}
                    className="flex flex-col items-center gap-1 text-gray-400 hover:text-primary-600 min-w-[40px]">
                    <span className="text-lg">▲</span>
                    <span className="text-sm font-bold">{post.upvotes || 0}</span>
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {post.is_pinned ? <span className="badge bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">📌 Pinned</span> : null}
                      <span className="badge bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">{post.post_type || 'discussion'}</span>
                      {post.is_ai_content ? (
                        <span className={`badge ${AI_LABEL_COLORS[post.ai_label] || AI_LABEL_COLORS['AI-Assisted']}`}>
                          🤖 {post.ai_label || 'AI-Assisted'}
                        </span>
                      ) : null}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">{post.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400 text-sm line-clamp-2">{post.content}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span className={`font-medium ${RANK_COLORS[post.rank_level] || ''}`}>{post.display_name || post.username}</span>
                      <span>💬 {post.comment_count || 0} comments</span>
                      <span>👁 {post.view_count || 0} views</span>
                      <span>{timeAgo(post.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create post modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">New post</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
            </div>
            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Post type</label>
                <select value={form.postType} onChange={e => setForm({...form, postType: e.target.value})} className="input">
                  {['discussion','question','resource','study-group','announcement'].map(t => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1).replace('-',' ')}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input value={form.title} onChange={e => setForm({...form, title: e.target.value})}
                  className="input" placeholder="What's your post about?" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Content</label>
                <textarea value={form.content} onChange={e => setForm({...form, content: e.target.value})}
                  className="input min-h-[140px]" placeholder="Share your knowledge, question, or resource…" required />
              </div>
              <div className="flex items-center gap-3">
                <input type="checkbox" id="ai" checked={form.isAiContent} onChange={e => setForm({...form, isAiContent: e.target.checked})} />
                <label htmlFor="ai" className="text-sm">AI-assisted content</label>
                {form.isAiContent && (
                  <select value={form.aiLabel} onChange={e => setForm({...form, aiLabel: e.target.value})} className="input ml-2">
                    <option value="">Label…</option>
                    {Object.keys(AI_LABEL_COLORS).map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                )}
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-primary">{submitting ? 'Posting…' : 'Post (+5 karma)'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
