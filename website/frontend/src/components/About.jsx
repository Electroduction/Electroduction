import './About.css'

function About() {
  return (
    <section id="about" className="about">
      <div className="container">
        <h2 className="section-title">About Me</h2>
        <div className="about-content">
          <div className="about-text">
            <p>
              I'm a passionate software developer and cybersecurity professional with a
              strong foundation in building secure, scalable applications. Currently pursuing
              a triple major in Information Systems and Technology (Cybersecurity), Software
              Engineering, and Finance.
            </p>
            <p>
              My experience spans from developing complex Python applications and web services
              to implementing security solutions and creating engaging game experiences. I'm
              particularly interested in the intersection of AI, security, and interactive media.
            </p>
            <div className="skills">
              <h3>Technical Skills</h3>
              <div className="skill-tags">
                <span className="tag">Python</span>
                <span className="tag">JavaScript</span>
                <span className="tag">React</span>
                <span className="tag">FastAPI</span>
                <span className="tag">Cybersecurity</span>
                <span className="tag">Machine Learning</span>
                <span className="tag">Game Development</span>
                <span className="tag">MongoDB</span>
                <span className="tag">Docker</span>
                <span className="tag">Git</span>
              </div>
            </div>
          </div>
          <div className="about-education">
            <h3>Education</h3>
            <div className="education-item">
              <h4>Bachelor of Science in Information Systems and Technology</h4>
              <p>Cybersecurity Specialization - CSUSB</p>
            </div>
            <div className="education-item">
              <h4>Software Engineering</h4>
              <p>Study.com / WGU Transfer Program</p>
            </div>
            <div className="education-item">
              <h4>Finance</h4>
              <p>Georgia Tech Transfer Program</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default About
