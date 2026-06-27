import { useState, useEffect } from 'react';
import { getLeaderboard } from '../api/client';
import './Leaderboard.css';

const MEDALS = { 1: '🥇', 2: '🥈', 3: '🥉' };

export default function Leaderboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getLeaderboard(10)
      .then(setData)
      .catch(() => setError('Failed to load leaderboard. Is the API running?'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section id="leaderboard" className="section">
      <div className="container">
        <h2 className="section-title">EchoFrontier Leaderboard</h2>
        <p className="section-subtitle">Top players in the AI-powered game engine</p>

        {loading && <div className="loading"><div className="spinner" /> Loading leaderboard…</div>}
        {error && <p className="error-msg">{error}</p>}

        {data && (
          <div className="lb-wrapper">
            <div className="lb-info">
              <span className="badge">🎮 {data.total_players} total players</span>
              <span className="lb-updated">Updated: {new Date(data.last_updated).toLocaleString()}</span>
            </div>

            <div className="lb-table">
              <div className="lb-header lb-row">
                <span>Rank</span>
                <span>Player</span>
                <span>Score</span>
                <span>Level</span>
                <span>Games</span>
              </div>

              {data.leaderboard.map(entry => (
                <div key={entry.rank} className={`lb-row lb-entry rank-${entry.rank <= 3 ? entry.rank : 'rest'}`}>
                  <span className="lb-rank">
                    {MEDALS[entry.rank] || `#${entry.rank}`}
                  </span>
                  <span className="lb-name">{entry.name}</span>
                  <span className="lb-score">{entry.score.toLocaleString()}</span>
                  <span className="lb-level">Lvl {entry.level}</span>
                  <span className="lb-games">{entry.games}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
