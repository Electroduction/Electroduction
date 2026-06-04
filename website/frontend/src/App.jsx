import { useState, useEffect } from 'react'
import './App.css'
import Hero from './components/Hero'
import Projects from './components/Projects'
import GameStats from './components/GameStats'
import About from './components/About'
import Contact from './components/Contact'
import Navigation from './components/Navigation'
import { API_URL } from './api'

function App() {
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    // Check backend API connection
    const checkAPI = async () => {
      try {
        const response = await fetch(`${API_URL}/api/health`)
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
