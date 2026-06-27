import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const RANK_CONFIG = {
  Diamond: { color: 'text-purple-600', bg: 'bg-purple-100 dark:bg-purple-900', icon: '💎' },
  Platinum: { color: 'text-blue-600',   bg: 'bg-blue-100 dark:bg-blue-900',   icon: '💠' },
  Gold:     { color: 'text-yellow-600', bg: 'bg-yellow-100 dark:bg-yellow-900', icon: '🥇' },
  Silver:   { color: 'text-gray-500',   bg: 'bg-gray-100 dark:bg-gray-700',   icon: '🥈' },
  Bronze:   { color: 'text-amber-700',  bg: 'bg-amber-100 dark:bg-amber-900', icon: '🥉' },
};

export default function Leaderboard() {
  const { user } = useAuthStore();
  const [board, setBoard] = useState([]);
  const [streaks, setStreaks] = useState([]);
  const [view, setView] = useState('karma');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get('/gamification/leaderboard').catch(() => ({ data: { users: [] } })),
      api.get('/gamification/streaks').catch(() => ({ data: { users: [] } })),
    ]).then(([lb, str]) => {
      setBoard(lb.data.users || lb.data.leaderboard || []);
      setStreaks(str.data.users || str.data.streaks || []);
    }).finally(() => setLoading(false));
  }, []);

  const displayed = view === 'karma' ? board : streaks;
  const valueKey = view === 'karma' ? 'karma_points' : 'learning_streak';
  const valueLabel = view === 'karma' ? 'karma' : 'day streak';
  const valueIcon = view === 'karma' ? '⭐' : '🔥';

  const positionIcon = (i) => i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Leaderboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Top members by karma and learning streaks</p>
      </div>

      <div className="flex gap-2">
        {[['karma','⭐ Karma'],['streak','🔥 Streaks']].map(([v,l]) => (
          <button key={v} onClick={() => setView(v)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${view === v ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
            {l}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card text-center py-12 text-gray-400">Loading leaderboard…</div>
      ) : displayed.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">🏆</div>
          <p className="text-gray-500">No data yet — start earning karma to appear here!</p>
        </div>
      ) : (
        <>
          {/* Top 3 podium */}
          {displayed.length >= 3 && (
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[1, 0, 2].map(i => {
                const member = displayed[i];
                if (!member) return null;
                const rank = RANK_CONFIG[member.rank_level] || RANK_CONFIG.Bronze;
                const isFirst = i === 0;
                return (
                  <div key={member.id || i} className={`card text-center ${isFirst ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700' : ''}`}>
                    <div className="text-3xl mb-2">{positionIcon(i)}</div>
                    <div className={`w-14 h-14 rounded-full ${rank.bg} flex items-center justify-center text-xl font-bold mx-auto mb-2 ${rank.color}`}>
                      {(member.display_name || member.username || '?')[0].toUpperCase()}
                    </div>
                    <div className="font-semibold truncate">{member.display_name || member.username}</div>
                    <div className={`text-sm font-medium mt-1 ${rank.color}`}>{rank.icon} {member.rank_level}</div>
                    <div className="text-lg font-bold mt-1">{valueIcon} {(member[valueKey] || 0).toLocaleString()}</div>
                    <div className="text-xs text-gray-400">{valueLabel}</div>
                    {user?.id === member.id && <div className="badge bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200 mt-2 mx-auto">You</div>}
                  </div>
                );
              })}
            </div>
          )}

          {/* Full list */}
          <div className="card p-0 overflow-hidden">
            {displayed.map((member, i) => {
              const rank = RANK_CONFIG[member.rank_level] || RANK_CONFIG.Bronze;
              const isMe = user?.id === member.id;
              return (
                <div key={member.id || i} className={`flex items-center gap-4 p-4 border-b dark:border-gray-700 last:border-none ${isMe ? 'bg-primary-50 dark:bg-primary-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-700'}`}>
                  <div className="w-8 text-center font-bold text-gray-500">{positionIcon(i)}</div>
                  <div className={`w-10 h-10 rounded-full ${rank.bg} flex items-center justify-center font-bold text-sm ${rank.color}`}>
                    {(member.display_name || member.username || '?')[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{member.display_name || member.username}</span>
                      {isMe && <span className="badge badge-rare text-xs">You</span>}
                    </div>
                    <div className={`text-xs ${rank.color}`}>{rank.icon} {member.rank_level}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold">{valueIcon} {(member[valueKey] || 0).toLocaleString()}</div>
                    <div className="text-xs text-gray-400">{valueLabel}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
