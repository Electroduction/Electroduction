# Research Aggregator - Unified Knowledge Portal

A comprehensive research RSS feeds and data aggregation website system with specialized portals for different professional and academic fields.

## Features

### Core Features
- **RSS Feed Aggregation**: Live feeds from top industry sources
- **Hover Definition System**: Underlined glossary terms reveal detailed explanations on hover
- **Zero-to-Hero Guides**: Comprehensive walkthroughs with indexed navigation
- **Adjustable Content Length**: Control depth from 1-12 pages
- **Unified Search**: Search across all portals and content

### Portals Included

| Portal | Description | Key Topics |
|--------|-------------|------------|
| **Computer Science** | Algorithms, data structures, software engineering | Big O, OOP, System Design, AI/ML |
| **Cybersecurity** | Network security, penetration testing | CIA Triad, OWASP, Cryptography |
| **Finance** | Investment, market analysis | Financial Statements, Valuation, Risk |
| **Accounting** | GAAP, auditing, tax | (Coming Soon) |
| **Legal** | Contract law, litigation, compliance | Discovery, IP, Regulatory |
| **Human Resources** | Talent acquisition, employee relations | Recruiting, Performance, Compliance |
| **Electrical Trade** | Wiring, circuits, NEC codes | Ohm's Law, Circuits, Troubleshooting |
| **Plumbing** | Pipe systems, codes | (Coming Soon) |
| **HVAC** | Heating, ventilation, AC | (Coming Soon) |
| **Carpentry** | Woodworking, framing | (Coming Soon) |
| **Art & Design** | Visual arts, UX/UI | (Coming Soon) |
| **STEM** | Physics, Chemistry, Biology, Math | (Coming Soon) |

## Quick Start

### Running Locally

```bash
# Navigate to the project directory
cd research-aggregator

# Start a local server (Python 3)
python3 -m http.server 8080

# Open in browser
open http://localhost:8080
```

### Running Tests

```bash
# Run the test script
python3 test.py
```

## Project Structure

```
research-aggregator/
├── index.html              # Main dashboard
├── css/
│   └── main.css           # Complete stylesheet with themes
├── js/
│   └── core.js            # RSS aggregator & UI engine
├── portals/
│   ├── computer-science.html
│   ├── cybersecurity.html
│   ├── finance.html
│   ├── legal.html
│   ├── hr.html
│   ├── electrical.html
│   └── ... (more portals)
├── data/
│   ├── feeds-cs.json
│   ├── feeds-cybersecurity.json
│   └── ... (feed configs)
├── test.py                 # Verification script
└── README.md
```

## How the Definition System Works

1. **Glossary Terms**: Words/phrases are marked with `class="glossary-term"` and `data-term="term-id"`
2. **On Hover**: When you hover over an underlined term, a definition window appears on the right side
3. **Scrollable Window**: The definition window is scrollable while your mouse is over it
4. **Related Terms**: Click related terms to navigate to their definitions
5. **Disappears**: Window disappears when mouse leaves both the term and the window

## Content Length Control

The slider at the bottom adjusts how much content is shown:
- **1 page**: Executive summary only
- **6 pages**: Moderate depth (default)
- **12 pages**: Full comprehensive content

## Technologies Used

- **HTML5**: Semantic markup
- **CSS3**: Custom properties, Flexbox, Grid, animations
- **Vanilla JavaScript**: No frameworks, lightweight
- **RSS Parsing**: Built-in XML parsing with CORS proxy

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Limitations

- **RSS CORS**: Some feeds may be blocked due to CORS policies
- **Offline**: Requires internet connection for RSS feeds
- **Static**: This is a client-side only application

## Future Enhancements

- [ ] More portal pages (Accounting, Art, STEM subjects)
- [ ] Bookmark/save articles feature
- [ ] Dark/light theme toggle
- [ ] Export guides as PDF
- [ ] User notes and annotations
- [ ] Mobile app version

## License

MIT License - Feel free to use and modify.
