import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const RARITY_STYLE = {
  legendary: 'badge-legendary', epic: 'badge-epic', rare: 'badge-rare', common: 'badge-common',
};

export default function RewardsShop() {
  const { user, updateUser } = useAuthStore();
  const [rewards, setRewards] = useState([]);
  const [badges, setBadges] = useState([]);
  const [myRewards, setMyRewards] = useState([]);
  const [tab, setTab] = useState('rewards');
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get('/gamification/rewards').catch(() => ({ data: { rewards: [] } })),
      api.get('/gamification/badges').catch(() => ({ data: { badges: [] } })),
      user ? api.get('/gamification/my-rewards').catch(() => ({ data: { rewards: [] } })) : Promise.resolve({ data: { rewards: [] } }),
    ]).then(([r, b, my]) => {
      setRewards(r.data.rewards || []);
      setBadges(b.data.badges || []);
      setMyRewards((my.data.rewards || []).map(r => r.id));
    }).finally(() => setLoading(false));
  }, [user]);

  const purchase = async (item, type) => {
    if (!user) { toast.error('Sign in to purchase'); return; }
    if ((user.reward_points || 0) < item.price) { toast.error(`Not enough points — need ${item.price - (user.reward_points||0)} more`); return; }
    setBuying(item.id);
    try {
      if (type === 'badge') {
        await api.post(`/gamification/badges/${item.id}/purchase`);
      } else {
        await api.post(`/gamification/rewards/${item.id}/purchase`);
      }
      toast.success(`${item.name} purchased!`);
      updateUser({ reward_points: (user.reward_points||0) - item.price });
      setMyRewards(prev => [...prev, item.id]);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Purchase failed');
    } finally { setBuying(null); }
  };

  const REWARD_ICONS = { 'Profile Border': '🎨', 'Custom Emoji': '😎', 'Avatar Frame': '🖼️', 'Name Badge': '🏷️' };
  const getIcon = (name) => REWARD_ICONS[name] || '✨';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Rewards shop</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Spend your reward points on profile perks and badges</p>
      </div>

      {user && (
        <div className="card bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/30 dark:to-purple-900/30 border-primary-200 dark:border-primary-700">
          <div className="flex items-center gap-4">
            <div className="text-3xl">⭐</div>
            <div>
              <div className="text-2xl font-bold">{(user.karma_points || 0).toLocaleString()} karma</div>
              <div className="text-gray-600 dark:text-gray-400 text-sm">Your rank: <span className="font-medium">{user.rank_level || 'Bronze'}</span></div>
            </div>
            <div className="ml-auto text-right">
              <div className="text-2xl font-bold text-purple-600">{(user.reward_points || 0).toLocaleString()} pts</div>
              <div className="text-gray-500 text-sm">available to spend</div>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {[['rewards','🎁 Perks'],['badges','🏅 Badges']].map(([v,l]) => (
          <button key={v} onClick={() => setTab(v)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === v ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
            {l}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card text-center py-12 text-gray-400">Loading shop…</div>
      ) : tab === 'rewards' ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {rewards.length === 0 ? (
            <div className="col-span-3 card text-center py-12 text-gray-400">No rewards available yet</div>
          ) : rewards.map(r => {
            const owned = myRewards.includes(r.id);
            return (
              <div key={r.id} className={`card flex flex-col items-center text-center ${owned ? 'border-green-300 dark:border-green-600 bg-green-50 dark:bg-green-900/20' : ''}`}>
                <div className="text-4xl mb-3">{getIcon(r.name)}</div>
                <div className="font-semibold mb-1">{r.name}</div>
                {r.description && <p className="text-sm text-gray-500 mb-3 leading-relaxed">{r.description}</p>}
                <div className="flex items-center gap-1 text-purple-600 font-bold text-lg mb-4">
                  ⭐ {r.price?.toLocaleString()} pts
                </div>
                {owned ? (
                  <span className="badge bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">✓ Owned</span>
                ) : (
                  <button onClick={() => purchase(r, 'reward')} disabled={buying === r.id || !user}
                    className="btn-primary w-full">{buying === r.id ? 'Purchasing…' : 'Purchase'}</button>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {badges.length === 0 ? (
            <div className="col-span-3 card text-center py-12 text-gray-400">No badges available yet</div>
          ) : badges.map(b => {
            const owned = myRewards.includes(b.id);
            return (
              <div key={b.id} className={`card flex flex-col items-center text-center ${owned ? 'border-green-300 dark:border-green-600 bg-green-50 dark:bg-green-900/20' : ''}`}>
                {b.icon_url ? (
                  <div className="text-4xl mb-3">{b.icon_url}</div>
                ) : (
                  <div className="text-4xl mb-3">🏅</div>
                )}
                <div className={`badge ${RARITY_STYLE[b.rarity] || 'badge-common'} mb-2`}>{b.rarity}</div>
                <div className="font-semibold mb-1">{b.name}</div>
                {b.description && <p className="text-xs text-gray-500 mb-3">{b.description}</p>}
                {b.price > 0 ? (
                  <>
                    <div className="text-purple-600 font-bold mb-3">⭐ {b.price?.toLocaleString()} pts</div>
                    {owned ? (
                      <span className="badge bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">✓ Owned</span>
                    ) : (
                      <button onClick={() => purchase(b, 'badge')} disabled={buying === b.id || !user}
                        className="btn-primary w-full text-sm">{buying === b.id ? 'Purchasing…' : 'Purchase'}</button>
                    )}
                  </>
                ) : <span className="badge badge-common">Earned by achievement</span>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
