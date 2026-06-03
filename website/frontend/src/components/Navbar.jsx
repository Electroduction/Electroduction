import { useState } from 'react';
import './Navbar.css';

const links = [
  { href: '#home', label: 'Home' },
  { href: '#projects', label: 'Projects' },
  { href: '#stats', label: 'Stats' },
  { href: '#leaderboard', label: 'Leaderboard' },
  { href: '#contact', label: 'Contact' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="container nav-inner">
        <a href="#home" className="nav-logo">
          <span className="logo-icon">⚡</span>
          <span>Electroduction</span>
        </a>

        <ul className={`nav-links ${open ? 'open' : ''}`}>
          {links.map(l => (
            <li key={l.href}>
              <a href={l.href} onClick={() => setOpen(false)}>{l.label}</a>
            </li>
          ))}
          <li>
            <a
              href="https://github.com/Electroduction/Electroduction"
              target="_blank"
              rel="noreferrer"
              className="nav-cta"
            >
              GitHub ↗
            </a>
          </li>
        </ul>

        <button
          className={`hamburger ${open ? 'active' : ''}`}
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          <span /><span /><span />
        </button>
      </div>
    </nav>
  );
}
