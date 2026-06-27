import { useState } from 'react';
import { sendContact } from '../api/client';
import './Contact.css';

const INITIAL = { name: '', email: '', subject: '', message: '' };

function validate(form) {
  const errs = {};
  if (!form.name.trim()) errs.name = 'Name is required.';
  if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) errs.email = 'Valid email required.';
  if (!form.subject.trim()) errs.subject = 'Subject is required.';
  if (form.message.trim().length < 10) errs.message = 'Message must be at least 10 characters.';
  return errs;
}

export default function Contact() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState('');
  const [serverError, setServerError] = useState('');

  const handle = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const submit = async (e) => {
    e.preventDefault();
    const errs = validate(form);
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSubmitting(true);
    setServerError('');
    setSuccess('');
    try {
      const res = await sendContact(form);
      setSuccess(res.message);
      setForm(INITIAL);
    } catch (err) {
      setServerError(err?.response?.data?.detail || 'Failed to send. Is the API running?');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section id="contact" className="section contact-section">
      <div className="container">
        <h2 className="section-title">Get In Touch</h2>
        <p className="section-subtitle">Have a project idea, opportunity, or just want to connect?</p>

        <div className="contact-layout">
          <div className="contact-info">
            <h3>Let's work together</h3>
            <p>I'm always open to discussing new opportunities in software development, cybersecurity, and AI.</p>
            <div className="contact-links">
              <a href="https://github.com/Electroduction/Electroduction" target="_blank" rel="noreferrer" className="contact-link">
                <span className="contact-link-icon">🐙</span>
                <div>
                  <div className="contact-link-title">GitHub</div>
                  <div className="contact-link-sub">Electroduction/Electroduction</div>
                </div>
              </a>
              <a href="https://www.linkedin.com/in/kenny-situ/" target="_blank" rel="noreferrer" className="contact-link">
                <span className="contact-link-icon">💼</span>
                <div>
                  <div className="contact-link-title">LinkedIn</div>
                  <div className="contact-link-sub">kenny-situ</div>
                </div>
              </a>
              <div className="contact-link">
                <span className="contact-link-icon">🎓</span>
                <div>
                  <div className="contact-link-title">Education</div>
                  <div className="contact-link-sub">CSUSB — IS&T (Cybersecurity)</div>
                </div>
              </div>
            </div>
          </div>

          <form className="contact-form card" onSubmit={submit} noValidate>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input id="name" name="name" value={form.name} onChange={handle} placeholder="Your name" />
                {errors.name && <span className="error-msg">{errors.name}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input id="email" name="email" type="email" value={form.email} onChange={handle} placeholder="you@example.com" />
                {errors.email && <span className="error-msg">{errors.email}</span>}
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="subject">Subject</label>
              <input id="subject" name="subject" value={form.subject} onChange={handle} placeholder="What's this about?" />
              {errors.subject && <span className="error-msg">{errors.subject}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="message">Message</label>
              <textarea id="message" name="message" value={form.message} onChange={handle} rows={5} placeholder="Your message…" />
              {errors.message && <span className="error-msg">{errors.message}</span>}
            </div>

            {serverError && <p className="error-msg">{serverError}</p>}
            {success && <p className="success-msg">✅ {success}</p>}

            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Sending…' : 'Send Message →'}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
