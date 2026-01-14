import { useState, useEffect } from 'react'
import './App.css'
import Hero from './components/Hero'
import Projects from './components/Projects'
import GameStats from './components/GameStats'
import About from './components/About'
import Contact from './components/Contact'
import Navigation from './components/Navigation'

function App() {
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    // Check backend API connection
    const checkAPI = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/health')
        if (response.ok) {
          setApiStatus('connected')
        } else {
          setApiStatus('disconnected')
        }
      } catch (error) {
        setApiStatus('disconnected')
      }
    }
    checkAPI()
  }, [])

  return (
    <div className="app">
      <Navigation />
      <main>
        <Hero />
        <About />
        <Projects />
        <GameStats apiStatus={apiStatus} />
        <Contact />
      </main>
      <footer className="footer">
        <p>&copy; 2026 Kenny Situ. Built with React + FastAPI</p>
        <p className={`api-status ${apiStatus}`}>
          Backend: {apiStatus === 'connected' ? '🟢 Online' : '🔴 Offline'}
        </p>
      </footer>
    </div>
  )
}

export default App
