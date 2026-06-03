import { useState, useEffect } from 'react';
import { getProjects } from '../api/client';
import './Projects.css';

const CATEGORY_ICONS = {
  cybersecurity: '🔐',
  game: '🎮',
  fintech: '💹',
  ai: '🤖',
};

const CATEGORIES = [
  { key: null, label: 'All' },
  { key: 'ai', label: 'AI/ML' },
  { key: 'cybersecurity', label: 'Cybersecurity' },
  { key: 'fintech', label: 'FinTech' },
  { key: 'game', label: 'Game Dev' },
];

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeCategory, setActiveCategory] = useState(null);

  const fetchProjects = async (category) => {
    setLoading(true);
    setError('');
    try {
      const data = await getProjects(category);
      setProjects(data.projects);
    } catch {
      setError('Failed to load projects. Is the API running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(null); }, []);

  const handleFilter = (cat) => {
    setActiveCategory(cat);
    fetchProjects(cat);
  };

  return (
    <section id="projects" className="section">
      <div className="container">
        <h2 className="section-title">Projects</h2>
        <p className="section-subtitle">Production-ready applications across AI, security, and creative tech</p>

        <div className="filter-tabs">
          {CATEGORIES.map(c => (
            <button
              key={String(c.key)}
              className={`filter-tab ${activeCategory === c.key ? 'active' : ''}`}
              onClick={() => handleFilter(c.key)}
            >
              {c.label}
            </button>
          ))}
        </div>

        {loading && <div className="loading"><div className="spinner" /> Loading projects…</div>}
        {error && <p className="error-msg">{error}</p>}

        {!loading && !error && (
          <div className="projects-grid">
            {projects.map(p => (
              <article key={p.id} className="card project-card">
                <div className="project-header">
                  <span className="project-icon">{CATEGORY_ICONS[p.category] || '📁'}</span>
                  <span className="badge">{p.category}</span>
                </div>
                <h3 className="project-title">{p.title}</h3>
                <p className="project-desc">{p.description}</p>
                <ul className="project-highlights">
                  {p.highlights.map(h => (
                    <li key={h}><span className="check">✓</span> {h}</li>
                  ))}
                </ul>
                <div className="project-tech">
                  {p.tech.map(t => (
                    <span key={t} className="tech-tag">{t}</span>
                  ))}
                </div>
                <div className="project-footer">
                  <a href={p.github} target="_blank" rel="noreferrer" className="btn btn-outline btn-sm">
                    View on GitHub ↗
                  </a>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
