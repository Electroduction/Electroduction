import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const LEVEL_BADGE = { beginner: 'bg-green-100 text-green-800', intermediate: 'bg-blue-100 text-blue-800', advanced: 'bg-purple-100 text-purple-800' };

export default function StudyGroups() {
  const { user } = useAuthStore();
  const [groups, setGroups] = useState([]);
  const [myGroups, setMyGroups] = useState([]);
  const [topics, setTopics] = useState([]);
  const [topicFilter, setTopicFilter] = useState('');
  const [tab, setTab] = useState('browse');
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [joining, setJoining] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', topicId: '', maxMembers: 10, meetingSchedule: '', skillLevel: 'beginner', isPrivate: false });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get('/topics').then(r => setTopics(r.data.topics || [])).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = topicFilter ? `?topicId=${topicFilter}` : '';
    Promise.all([
      api.get(`/study-groups${params}`).catch(() => ({ data: { groups: [] } })),
      user ? api.get('/study-groups/my').catch(() => ({ data: { groups: [] } })) : Promise.resolve({ data: { groups: [] } }),
    ]).then(([all, my]) => {
      setGroups(all.data.groups || []);
      setMyGroups(my.data.groups || []);
    }).finally(() => setLoading(false));
  }, [topicFilter, user]);

  const join = async (groupId) => {
    if (!user) { toast.error('Sign in to join groups'); return; }
    setJoining(groupId);
    try {
      await api.post(`/study-groups/${groupId}/join`);
      toast.success('Joined group!');
      setGroups(prev => prev.map(g => g.id === groupId ? {...g, member_count: g.member_count+1} : g));
      const my = await api.get('/study-groups/my');
      setMyGroups(my.data.groups || []);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to join group');
    } finally { setJoining(null); }
  };

  const leave = async (groupId) => {
    try {
      await api.delete(`/study-groups/${groupId}/leave`);
      toast.success('Left group');
      setMyGroups(prev => prev.filter(g => g.id !== groupId));
    } catch { toast.error('Failed to leave group'); }
  };

  const createGroup = async (e) => {
    e.preventDefault();
    if (!form.name || !form.topicId) { toast.error('Name and topic are required'); return; }
    setSubmitting(true);
    try {
      await api.post('/study-groups', form);
      toast.success('Study group created!');
      setShowCreate(false);
      setForm({ name: '', description: '', topicId: '', maxMembers: 10, meetingSchedule: '', skillLevel: 'beginner', isPrivate: false });
      const [all, my] = await Promise.all([api.get('/study-groups'), api.get('/study-groups/my')]);
      setGroups(all.data.groups || []);
      setMyGroups(my.data.groups || []);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create group');
    } finally { setSubmitting(false); }
  };

  const displayed = tab === 'browse' ? groups : myGroups;
  const memberIds = myGroups.map(g => g.id);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold">Study groups</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Collaborative cohort-based learning with fellow members</p>
        </div>
        {user && <button onClick={() => setShowCreate(true)} className="btn-primary">+ Create group</button>}
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex gap-2">
          {[['browse','All groups'],['mine','My groups']].map(([v,l]) => (
            <button key={v} onClick={() => setTab(v)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${tab === v ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
              {l} {v === 'mine' && myGroups.length > 0 ? `(${myGroups.length})` : ''}
            </button>
          ))}
        </div>
        <select value={topicFilter} onChange={e => setTopicFilter(e.target.value)} className="input max-w-xs">
          <option value="">All topics</option>
          {topics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="card text-center py-12 text-gray-400">Loading groups…</div>
      ) : displayed.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">👥</div>
          <p className="text-gray-500">{tab === 'mine' ? "You haven't joined any groups yet" : 'No groups found'}</p>
          {user && <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">Create a group</button>}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {displayed.map(g => {
            const isMember = memberIds.includes(g.id);
            const full = g.member_count >= g.max_members;
            return (
              <div key={g.id} className={`card ${isMember ? 'border-primary-300 dark:border-primary-600' : ''}`}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-lg truncate">{g.name}</h3>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span className="badge badge-common text-xs">{g.topic_name}</span>
                      <span className={`badge text-xs ${LEVEL_BADGE[g.skill_level] || 'badge-common'} dark:bg-opacity-20`}>{g.skill_level}</span>
                      {isMember && <span className="badge bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200 text-xs">✓ Joined</span>}
                    </div>
                  </div>
                </div>
                {g.description && <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">{g.description}</p>}
                {g.meeting_schedule && (
                  <p className="text-xs text-gray-500 mb-2">📅 {g.meeting_schedule}</p>
                )}
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span>👥 {g.member_count || 0}/{g.max_members} members</span>
                    <div className="w-24 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                      <div className="h-full bg-primary-500 rounded-full" style={{ width: `${Math.min(100, ((g.member_count||0)/(g.max_members||10))*100)}%` }} />
                    </div>
                  </div>
                  {isMember ? (
                    <button onClick={() => leave(g.id)} className="btn-secondary text-xs py-1 px-3">Leave</button>
                  ) : (
                    <button onClick={() => join(g.id)} disabled={joining === g.id || full}
                      className={`text-xs py-1 px-3 rounded-lg font-medium transition-colors ${full ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'btn-primary'}`}>
                      {joining === g.id ? 'Joining…' : full ? 'Full' : 'Join group'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Create a study group</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 text-2xl">&times;</button>
            </div>
            <form onSubmit={createGroup} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Group name</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="input" placeholder="e.g. Transformer architecture deep-dive" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Topic</label>
                <select value={form.topicId} onChange={e => setForm({...form, topicId: e.target.value})} className="input" required>
                  <option value="">Choose a topic…</option>
                  {topics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="input min-h-[80px]" placeholder="What will this group focus on? Goals, format, expectations…" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Skill level</label>
                  <select value={form.skillLevel} onChange={e => setForm({...form, skillLevel: e.target.value})} className="input">
                    {['beginner','intermediate','advanced'].map(l => <option key={l} value={l}>{l.charAt(0).toUpperCase()+l.slice(1)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max members</label>
                  <input type="number" min="2" max="50" value={form.maxMembers} onChange={e => setForm({...form, maxMembers: parseInt(e.target.value)})} className="input" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Meeting schedule (optional)</label>
                <input value={form.meetingSchedule} onChange={e => setForm({...form, meetingSchedule: e.target.value})} className="input" placeholder="e.g. Wednesdays 7pm PST via Discord" />
              </div>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.isPrivate} onChange={e => setForm({...form, isPrivate: e.target.checked})} />
                Private group (invite only)
              </label>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-primary">{submitting ? 'Creating…' : 'Create group'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
