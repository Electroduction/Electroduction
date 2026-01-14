import './Projects.css'

function Projects() {
  const projects = [
    {
      title: "Electroduction - AAA Roguelike Game",
      description: "A professional-grade roguelike game featuring advanced combat systems, procedural dungeon generation, particle effects, and complete game mechanics. Built with Python and Pygame.",
      tech: ["Python", "Pygame", "Game Design", "Audio System"],
      highlights: [
        "Advanced combat and ability system",
        "Procedural dungeon generation",
        "Boss battles and enemy AI",
        "Particle effects and screen shake",
        "Shop and progression systems"
      ],
      github: "https://github.com/Electroduction/Electroduction"
    },
    {
      title: "IT Capstone: Secure Website Setup",
      description: "Complete website setup with comprehensive security implementation and ongoing maintenance.",
      tech: ["Web Security", "Linux", "SSL/TLS", "Firewall"],
      link: "https://docs.google.com/document/d/1ZJRpx_zMxTA050lJfydK9I8Q8G-CvEMZdKdaIRWPRYU/edit"
    },
    {
      title: "Alpine Heights Store",
      description: "Full e-commerce website design and implementation.",
      tech: ["Web Design", "E-commerce", "UX/UI"],
      link: "https://alpineheights.store/"
    },
    {
      title: "Project Mapper - Tkinter App",
      description: "Advanced code relationship analyzer with visual project mapping capabilities.",
      tech: ["Python", "Tkinter", "Code Analysis", "Visualization"],
      highlights: [
        "Automated code structure analysis",
        "Dependency mapping",
        "Interactive visualization"
      ]
    },
    {
      title: "Python Data Scraper",
      description: "Web scraping tool built with Selenium and WebDriver for automated data collection.",
      tech: ["Python", "Selenium", "WebDriver", "Automation"]
    },
    {
      title: "Machine Learning Projects",
      description: "Various ML applications developed after completing Google ML and AI courses.",
      tech: ["Machine Learning", "AI", "Python", "TensorFlow"]
    }
  ]

  return (
    <section id="projects" className="projects">
      <div className="container">
        <h2 className="section-title">Featured Projects</h2>
        <div className="projects-grid">
          {projects.map((project, index) => (
            <div key={index} className="project-card">
              <div className="project-header">
                <h3>{project.title}</h3>
              </div>
              <p className="project-description">{project.description}</p>
              {project.highlights && (
                <ul className="project-highlights">
                  {project.highlights.map((highlight, i) => (
                    <li key={i}>{highlight}</li>
                  ))}
                </ul>
              )}
              <div className="project-tech">
                {project.tech.map((tech, i) => (
                  <span key={i} className="tech-tag">{tech}</span>
                ))}
              </div>
              <div className="project-links">
                {project.github && (
                  <a href={project.github} target="_blank" rel="noopener noreferrer" className="project-link">
                    GitHub →
                  </a>
                )}
                {project.link && (
                  <a href={project.link} target="_blank" rel="noopener noreferrer" className="project-link">
                    View Project →
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Projects
