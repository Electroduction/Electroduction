import './Hero.css';

export default function Hero() {
  return (
    <section id="home" className="hero section">
      <div className="hero-bg-grid" aria-hidden="true" />
      <div className="container hero-content">
        <div className="hero-badge badge">Available for opportunities</div>
        <h1 className="hero-title">
          Hi, I'm <span className="gradient-text">Kenny Situ</span>
        </h1>
        <p className="hero-roles">
          Software Developer &nbsp;·&nbsp; Cybersecurity Professional &nbsp;·&nbsp; AI Builder
        </p>
        <p className="hero-desc">
          Building AI-powered applications at the intersection of cybersecurity, fintech, and
          creative technology. CSUSB Computer Science student turning ambitious ideas into
          production-ready software.
        </p>
        <div className="hero-actions">
          <a href="#projects" className="btn btn-primary">View Projects</a>
          <a href="#contact" className="btn btn-outline">Get In Touch</a>
        </div>
        <div className="hero-tech">
          {['Python', 'React', 'FastAPI', 'Docker', 'Machine Learning', 'Cybersecurity'].map(t => (
            <span key={t} className="tech-pill">{t}</span>
          ))}
        </div>
      </div>
    </section>
  );
}
