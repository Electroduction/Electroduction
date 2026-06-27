import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div className="footer-left">
          <span className="footer-logo">⚡ Electroduction</span>
          <p>Built with React + FastAPI + Docker</p>
        </div>
        <div className="footer-links">
          <a href="https://github.com/Electroduction/Electroduction" target="_blank" rel="noreferrer">GitHub</a>
          <a href="https://www.linkedin.com/in/kenny-situ/" target="_blank" rel="noreferrer">LinkedIn</a>
          <a href="#projects">Projects</a>
          <a href="#contact">Contact</a>
        </div>
        <p className="footer-copy">© {new Date().getFullYear()} Kenny Situ. All rights reserved.</p>
      </div>
    </footer>
  );
}
