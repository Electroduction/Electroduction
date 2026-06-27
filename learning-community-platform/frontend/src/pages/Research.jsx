import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

export default function Research() {
  const { user } = useAuthStore();
  const [papers, setPapers] = useState([]);
  const [filter, setFilter] = useState('published');
  const [collabOnly, setCollabOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', abstract: '', content: '', keywords: '', isAiContent: false, aiLabel: '', seekingCollaborators: false });
  const [submitting, setSubmitting] = useState(false);
  const [topics, setTopics] = useState([]);
  const [topicId, setTopicId] = useState('');

  useEffect(() => {
    api.get('/topics').then(r => setTopics(r.data.topics || [])).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ status: filter });
    if (collabOnly) params.set('seekingCollaborators', 'true');
    api.get(`/research?${params}`).then(r => setPapers(r.data.papers || [])).catch(() => {}).finally(() => setLoading(false));
  }, [filter, collabOnly]);

  const submitPaper = async (e) => {
    e.preventDefault();
    if (!form.title || !form.abstract) { toast.error('Title and abstract are required'); return; }
    setSubmitting(true);
    try {
      await api.post('/research', { ...form, topicId: topicId || undefined, keywords: form.keywords.split(',').map(k=>k.trim()).filter(Boolean) });
      toast.success('Paper published! +20 karma');
      setShowCreate(false);
      setForm({ title: '', abstract: '', content: '', keywords: '', isAiContent: false, aiLabel: '', seekingCollaborators: false });
      const r = await api.get(`/research?status=${filter}`);
      setPapers(r.data.papers || []);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to publish paper');
    } finally { setSubmitting(false); }
  };

  const requestCollab = async (paperId, e) => {
    e.preventDefault();
    if (!user) { toast.error('Sign in to collaborate'); return; }
    try {
      await api.post(`/research/${paperId}/collaborate`);
      toast.success('Collaboration request sent!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to send request');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold">Research</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Publish findings, find collaborators, and grow knowledge</p>
        </div>
        {user && <button onClick={() => setShowCreate(true)} className="btn-primary">+ Publish research</button>}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex gap-2">
          {[['published','Published'],['draft','Drafts'],['all','All']].map(([val,label]) => (
            <button key={val} onClick={() => setFilter(val)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${filter === val ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
              {label}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={collabOnly} onChange={e => setCollabOnly(e.target.checked)} className="w-4 h-4" />
          Seeking collaborators only
        </label>
      </div>

      {loading ? (
        <div className="card text-center py-12 text-gray-400">Loading research…</div>
      ) : papers.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">🔬</div>
          <p className="text-gray-500">No research papers found</p>
          {user && <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">Publish the first paper</button>}
        </div>
      ) : (
        <div className="grid gap-4">
          {papers.map(p => (
            <Link key={p.id} to={`/research/${p.id}`} className="block">
              <div className="card hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap gap-2 mb-2">
                      {p.is_ai_content ? (
                        <span className="badge bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">🤖 {p.ai_label || 'AI-Assisted'}</span>
                      ) : (
                        <span className="badge bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">✍️ Human-Created</span>
                      )}
                      {p.seeking_collaborators ? <span className="badge bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">🤝 Seeking collaborators</span> : null}
                      {p.topic_name && <span className="badge badge-common">{p.topic_name}</span>}
                    </div>
                    <h3 className="text-lg font-semibold mb-1">{p.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400 text-sm line-clamp-2 mb-2">{p.abstract}</p>
                    {p.keywords && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {(typeof p.keywords === 'string' ? p.keywords.split(',') : p.keywords).slice(0,4).map(k => (
                          <span key={k} className="badge badge-common text-xs">{k.trim()}</span>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="font-medium">{p.display_name || p.username}</span>
                      <span>📖 {p.view_count || 0} views</span>
                      <span>🔗 {p.citation_count || 0} citations</span>
                      <span>{new Date(p.published_at || p.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  {p.seeking_collaborators && user && p.user_id !== user.id && (
                    <button onClick={e => requestCollab(p.id, e)} className="btn-secondary text-sm whitespace-nowrap flex-shrink-0">
                      Request to collaborate
                    </button>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Publish research</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 text-2xl">&times;</button>
            </div>
            <form onSubmit={submitPaper} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} className="input" placeholder="Research paper title" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Topic (optional)</label>
                <select value={topicId} onChange={e => setTopicId(e.target.value)} className="input">
                  <option value="">None</option>
                  {topics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Abstract</label>
                <textarea value={form.abstract} onChange={e => setForm({...form, abstract: e.target.value})} className="input min-h-[100px]" placeholder="Brief summary of your research" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Full content (optional)</label>
                <textarea value={form.content} onChange={e => setForm({...form, content: e.target.value})} className="input min-h-[120px]" placeholder="Full research body, methodology, findings…" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Keywords (comma-separated)</label>
                <input value={form.keywords} onChange={e => setForm({...form, keywords: e.target.value})} className="input" placeholder="machine learning, transformer, NLP" />
              </div>
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={form.isAiContent} onChange={e => setForm({...form, isAiContent: e.target.checked})} />
                  AI-assisted content
                </label>
                {form.isAiContent && (
                  <select value={form.aiLabel} onChange={e => setForm({...form, aiLabel: e.target.value})} className="input">
                    <option value="">Select AI label…</option>
                    {['AI-Generated','AI-Assisted','Human-Created'].map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                )}
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={form.seekingCollaborators} onChange={e => setForm({...form, seekingCollaborators: e.target.checked})} />
                  Seeking collaborators
                </label>
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-primary">{submitting ? 'Publishing…' : 'Publish (+20 karma)'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
