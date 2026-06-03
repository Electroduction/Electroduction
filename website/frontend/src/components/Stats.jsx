import { useState, useEffect } from 'react';
import { getStats } from '../api/client';
import './Stats.css';

const STAT_DEFS = [
  { key: 'projects', label: 'Projects Built', icon: '🚀', suffix: '' },
  { key: 'tests_passing', label: 'Tests Passing', icon: '✅', suffix: '' },
  { key: 'test_pass_rate', label: 'Pass Rate', icon: '📊', suffix: '%' },
  { key: 'lines_of_code', label: 'Lines of Code', icon: '💻', suffix: '+' },
  { key: 'technologies', label: 'Technologies', icon: '⚙️', suffix: '+' },
  { key: 'hours_developed', label: 'Dev Hours', icon: '⏱️', suffix: '+' },
];

function AnimatedNumber({ value, suffix }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = value;
    const steps = 40;
    const inc = end / steps;
    const interval = setInterval(() => {
      start += inc;
      if (start >= end) { setDisplay(end); clearInterval(interval); }
      else { setDisplay(Math.floor(start)); }
    }, 30);
    return () => clearInterval(interval);
  }, [value]);
  return <>{display.toLocaleString()}{suffix}</>;
}

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => setError('Failed to load stats. Is the API running?'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section id="stats" className="section stats-section">
      <div className="container">
        <h2 className="section-title">By The Numbers</h2>
        <p className="section-subtitle">Metrics from the Electroduction portfolio</p>

        {loading && <div className="loading"><div className="spinner" /> Loading stats…</div>}
        {error && <p className="error-msg">{error}</p>}

        {stats && (
          <div className="stats-grid">
            {STAT_DEFS.map(({ key, label, icon, suffix }) => (
              <div key={key} className="stat-card card">
                <div className="stat-icon">{icon}</div>
                <div className="stat-value">
                  <AnimatedNumber value={stats[key]} suffix={suffix} />
                </div>
                <div className="stat-label">{label}</div>
              </div>
            ))}
          </div>
        )}

        <div className="skills-section">
          <h3 className="skills-heading">Core Technologies</h3>
          <div className="skills-bars">
            {[
              { name: 'Python', pct: 95 },
              { name: 'Machine Learning / AI', pct: 85 },
              { name: 'Cybersecurity', pct: 88 },
              { name: 'React / JavaScript', pct: 78 },
              { name: 'FastAPI / Backend', pct: 82 },
              { name: 'Docker / DevOps', pct: 70 },
            ].map(s => (
              <div key={s.name} className="skill-bar-row">
                <div className="skill-bar-label">
                  <span>{s.name}</span><span>{s.pct}%</span>
                </div>
                <div className="skill-bar-track">
                  <div className="skill-bar-fill" style={{ width: `${s.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
