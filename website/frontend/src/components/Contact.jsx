import { useState } from 'react'
import './Contact.css'

function Contact() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  })
  const [status, setStatus] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('sending')

    try {
      const response = await fetch('http://localhost:8000/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setStatus('success')
        setFormData({ name: '', email: '', message: '' })
      } else {
        setStatus('error')
      }
    } catch (error) {
      setStatus('error')
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <section id="contact" className="contact">
      <div className="container">
        <h2 className="section-title">Get In Touch</h2>
        <div className="contact-content">
          <div className="contact-info">
            <h3>Let's Connect</h3>
            <p>
              I'm always interested in hearing about new opportunities,
              collaborations, or just chatting about technology.
            </p>
            <div className="contact-links">
              <a href="https://github.com/KennySitu" target="_blank" rel="noopener noreferrer" className="contact-link">
                <span className="icon">📧</span> GitHub
              </a>
              <a href="https://www.linkedin.com/in/kenny-situ/" target="_blank" rel="noopener noreferrer" className="contact-link">
                <span className="icon">💼</span> LinkedIn
              </a>
              <a href="https://drive.google.com/drive/folders/1KOyzP4kdgR71ya3HPVXrweMN9Op7SqWX" target="_blank" rel="noopener noreferrer" className="contact-link">
                <span className="icon">📁</span> Portfolio Drive
              </a>
            </div>
          </div>
          <form className="contact-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="message">Message</label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                rows="5"
                required
              ></textarea>
            </div>
            <button type="submit" className="btn btn-primary" disabled={status === 'sending'}>
              {status === 'sending' ? 'Sending...' : 'Send Message'}
            </button>
            {status === 'success' && <p className="form-status success">Message sent successfully!</p>}
            {status === 'error' && <p className="form-status error">Failed to send message. Please try again.</p>}
          </form>
        </div>
      </div>
    </section>
  )
}

export default Contact
