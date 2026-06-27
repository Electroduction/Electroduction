import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const RANK_CONFIG = {
  Diamond: { icon: '💎', color: 'text-purple-600', bg: 'bg-purple-100 dark:bg-purple-900' },
  Platinum: { icon: '💠', color: 'text-blue-600', bg: 'bg-blue-100 dark:bg-blue-900' },
  Gold: { icon: '🥇', color: 'text-yellow-600', bg: 'bg-yellow-100 dark:bg-yellow-900' },
  Silver: { icon: '🥈', color: 'text-gray-500', bg: 'bg-gray-100 dark:bg-gray-700' },
  Bronze: { icon: '🥉', color: 'text-amber-700', bg: 'bg-amber-100 dark:bg-amber-900' },
};

export default function Profile() {
  const { username } = useParams();
  const { user, updateUser } = useAuthStore();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ display_name: '', bio: '' });
  const [saving, setSaving] = useState(false);

  const isOwnProfile = !username || username === user?.username;

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        if (isOwnProfile) {
          const r = await api.get('/auth/profile');
          setProfile(r.data.user);
          setForm({ display_name: r.data.user.display_name || '', bio: r.data.user.bio || '' });
        } else {
          const r = await api.get(`/auth/user/${username}`);
          setProfile(r.data.user);
        }
      } catch {
        toast.error('User not found');
        navigate('/');
      } finally { setLoading(false); }
    };
    fetch();
  }, [username, isOwnProfile, navigate]);

  const saveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const r = await api.put('/auth/profile', form);
      const updated = r.data.user || { ...profile, ...form };
      setProfile(updated);
      updateUser(updated);
      setEditing(false);
      toast.success('Profile updated!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save profile');
    } finally { setSaving(false); }
  };

  const sendMessage = () => {
    if (!user) { toast.error('Sign in to send messages'); navigate('/login'); return; }
    navigate(`/messages/${profile.id}`);
  };

  if (!user && isOwnProfile) return (
    <div className="card text-center py-12">
      <p className="text-gray-500">Sign in to view your profile</p>
      <button onClick={() => navigate('/login')} className="btn-primary mt-4">Sign in</button>
    </div>
  );

  if (loading) return <div className="card text-center py-12 text-gray-400">Loading profile…</div>;
  if (!profile) return null;

  const rank = RANK_CONFIG[profile.rank_level] || RANK_CONFIG.Bronze;
  const initials = (profile.display_name || profile.username || '?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);

  const KARMA_THRESHOLDS = { Bronze: 0, Silver: 1000, Gold: 5000, Platinum: 10000, Diamond: 25000 };
  const NEXT_RANK = { Bronze: 'Silver', Silver: 'Gold', Gold: 'Platinum', Platinum: 'Diamond', Diamond: null };
  const nextRank = NEXT_RANK[profile.rank_level];
  const nextThresh = nextRank ? KARMA_THRESHOLDS[nextRank] : null;
  const currentThresh = KARMA_THRESHOLDS[profile.rank_level] || 0;
  const progress = nextThresh ? Math.min(100, ((profile.karma_points - currentThresh) / (nextThresh - currentThresh)) * 100) : 100;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Profile card */}
      <div className="card">
        <div className="flex items-start gap-6">
          <div className={`w-20 h-20 rounded-full ${rank.bg} flex items-center justify-center text-2xl font-bold ${rank.color} flex-shrink-0`}>
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            {editing ? (
              <form onSubmit={saveProfile} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Display name</label>
                  <input value={form.display_name} onChange={e => setForm({...form, display_name: e.target.value})} className="input" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Bio</label>
                  <textarea value={form.bio} onChange={e => setForm({...form, bio: e.target.value})} className="input min-h-[80px]" placeholder="Tell the community about yourself…" />
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={saving} className="btn-primary text-sm">{saving ? 'Saving…' : 'Save changes'}</button>
                  <button type="button" onClick={() => setEditing(false)} className="btn-secondary text-sm">Cancel</button>
                </div>
              </form>
            ) : (
              <>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-2xl font-bold">{profile.display_name || profile.username}</h1>
                  <span className={`text-sm font-medium ${rank.color}`}>{rank.icon} {profile.rank_level}</span>
                </div>
                <p className="text-gray-500 text-sm mb-2">@{profile.username}</p>
                {profile.bio && <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">{profile.bio}</p>}
                <div className="flex items-center gap-3">
                  {isOwnProfile ? (
                    <button onClick={() => setEditing(true)} className="btn-secondary text-sm">Edit profile</button>
                  ) : (
                    <button onClick={sendMessage} className="btn-primary text-sm">Send message</button>
                  )}
                  {profile.is_teacher && <span className="badge bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">🎓 Verified teacher</span>}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Karma', value: (profile.karma_points||0).toLocaleString(), icon: '⭐' },
          { label: 'Reward pts', value: (profile.reward_points||0).toLocaleString(), icon: '🏆' },
          { label: 'Day streak', value: profile.learning_streak || 0, icon: '🔥' },
          { label: 'Rank', value: profile.rank_level, icon: rank.icon },
        ].map(s => (
          <div key={s.label} className="card text-center">
            <div className="text-2xl mb-1">{s.icon}</div>
            <div className="font-bold text-lg">{s.value}</div>
            <div className="text-xs text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Rank progress */}
      {nextRank && (
        <div className="card">
          <h2 className="font-semibold mb-3">Progress to {nextRank}</h2>
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>{rank.icon} {profile.rank_level}</span>
            <span>{RANK_CONFIG[nextRank]?.icon} {nextRank}</span>
          </div>
          <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden mb-2">
            <div className="h-full bg-primary-500 rounded-full transition-all" style={{ width: `${Math.max(2, progress)}%` }} />
          </div>
          <p className="text-xs text-gray-500 text-right">{(profile.karma_points||0).toLocaleString()} / {nextThresh?.toLocaleString()} karma</p>
        </div>
      )}

      {/* Member since */}
      <div className="card">
        <h2 className="font-semibold mb-2">Member since</h2>
        <p className="text-gray-600 dark:text-gray-400">{new Date(profile.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
      </div>
    </div>
  );
}
