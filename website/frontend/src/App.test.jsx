import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(document.querySelector('.app')).toBeInTheDocument()
  })

  it('displays the navigation component', () => {
    render(<App />)
    const navElements = screen.getAllByText('Kenny Situ')
    expect(navElements.length).toBeGreaterThan(0)
  })

  it('displays the hero section', () => {
    render(<App />)
    const softwareDevElements = screen.getAllByText(/Software Developer/i)
    expect(softwareDevElements.length).toBeGreaterThan(0)
  })

  it('displays the footer', () => {
    render(<App />)
    expect(screen.getByText(/© 2026 Kenny Situ/i)).toBeInTheDocument()
  })

  it('shows backend status', () => {
    render(<App />)
    expect(screen.getByText(/Backend:/i)).toBeInTheDocument()
  })
})
