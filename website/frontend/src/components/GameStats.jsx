import { useState, useEffect } from 'react'
import './GameStats.css'

function GameStats({ apiStatus }) {
  const [stats, setStats] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      if (apiStatus !== 'connected') {
        setLoading(false)
        return
      }

      try {
        const [statsRes, leaderboardRes] = await Promise.all([
          fetch('http://localhost:8000/api/game/stats'),
          fetch('http://localhost:8000/api/game/leaderboard')
        ])

        if (statsRes.ok) {
          const statsData = await statsRes.json()
          setStats(statsData)
        }

        if (leaderboardRes.ok) {
          const leaderboardData = await leaderboardRes.json()
          setLeaderboard(leaderboardData)
        }
      } catch (error) {
        console.error('Error fetching game data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [apiStatus])

  if (apiStatus !== 'connected') {
    return (
      <section id="game-stats" className="game-stats">
        <div className="container">
          <h2 className="section-title">Electroduction Game Stats</h2>
          <div className="stats-offline">
            <p>Connect to the backend to view live game statistics</p>
            <p className="hint">Start the backend server to see player stats and leaderboards</p>
          </div>
        </div>
      </section>
    )
  }

  if (loading) {
    return (
      <section id="game-stats" className="game-stats">
        <div className="container">
          <h2 className="section-title">Electroduction Game Stats</h2>
          <div className="loading">Loading game data...</div>
        </div>
      </section>
    )
  }

  return (
    <section id="game-stats" className="game-stats">
      <div className="container">
        <h2 className="section-title">Electroduction Game Stats</h2>

        {stats && (
          <div className="stats-overview">
            <div className="stat-card">
              <div className="stat-value">{stats.total_players || 0}</div>
              <div className="stat-label">Total Players</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.total_runs || 0}</div>
              <div className="stat-label">Game Runs</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.highest_level || 0}</div>
              <div className="stat-label">Highest Level</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.bosses_defeated || 0}</div>
              <div className="stat-label">Bosses Defeated</div>
            </div>
          </div>
        )}

        {leaderboard.length > 0 && (
          <div className="leaderboard">
            <h3>Top Players</h3>
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Player</th>
                  <th>Score</th>
                  <th>Level</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry, index) => (
                  <tr key={index} className={index < 3 ? `top-${index + 1}` : ''}>
                    <td className="rank">{index + 1}</td>
                    <td>{entry.player_name}</td>
                    <td>{entry.score}</td>
                    <td>{entry.level}</td>
                    <td>{new Date(entry.date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}

export default GameStats
