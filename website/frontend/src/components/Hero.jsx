import './Hero.css'

function Hero() {
  return (
    <section id="hero" className="hero">
      <div className="hero-content">
        <h1 className="hero-title">
          Hi, I'm <span className="highlight">Kenny Situ</span>
        </h1>
        <div className="hero-roles">
          <span className="role">Software Developer</span>
          <span className="separator">•</span>
          <span className="role">Cybersecurity Professional</span>
          <span className="separator">•</span>
          <span className="role">AI Tutor</span>
        </div>
        <p className="hero-description">
          Building innovative software solutions and exploring the intersection of
          cybersecurity, AI, and game development.
        </p>
        <div className="hero-cta">
          <a href="#projects" className="btn btn-primary">View Projects</a>
          <a href="#contact" className="btn btn-secondary">Get in Touch</a>
        </div>
        <div className="hero-stats">
          <div className="stat">
            <span className="stat-number">3+</span>
            <span className="stat-label">Years Experience</span>
          </div>
          <div className="stat">
            <span className="stat-number">15+</span>
            <span className="stat-label">Projects</span>
          </div>
          <div className="stat">
            <span className="stat-number">3</span>
            <span className="stat-label">Degrees</span>
          </div>
        </div>
      </div>
      <div className="hero-background">
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
      </div>
    </section>
  )
}

export default Hero
