import { dbRun, dbGet, dbAll } from '../config/database.js';

export const applyToBeTeacher = async (req, res) => {
  try {
    const { qualifications, experience, subjectAreas } = req.body;

    if (!qualifications || !experience || !subjectAreas) {
      return res.status(400).json({
        error: 'Qualifications, experience, and subject areas are required'
      });
    }

    // Check if already applied
    const existing = await dbGet(
      'SELECT id, status FROM teacher_applications WHERE user_id = ?',
      [req.user.id]
    );

    if (existing && existing.status === 'pending') {
      return res.status(409).json({ error: 'Application already pending' });
    }

    if (existing && existing.status === 'approved') {
      return res.status(409).json({ error: 'Already approved as teacher' });
    }

    const result = await dbRun(
      `INSERT INTO teacher_applications (user_id, qualifications, experience, subject_areas)
       VALUES (?, ?, ?, ?)`,
      [req.user.id, qualifications, experience, subjectAreas]
    );

    // Update user status
    await dbRun(
      'UPDATE users SET teacher_status = ? WHERE id = ?',
      ['pending', req.user.id]
    );

    res.status(201).json({
      message: 'Teacher application submitted successfully',
      applicationId: result.id
    });
  } catch (error) {
    console.error('Apply teacher error:', error);
    res.status(500).json({ error: 'Server error submitting application' });
  }
};

export const getMyApplication = async (req, res) => {
  try {
    const application = await dbGet(
      'SELECT * FROM teacher_applications WHERE user_id = ? ORDER BY submitted_at DESC LIMIT 1',
      [req.user.id]
    );

    if (!application) {
      return res.status(404).json({ error: 'No application found' });
    }

    res.json({ application });
  } catch (error) {
    console.error('Get application error:', error);
    res.status(500).json({ error: 'Server error fetching application' });
  }
};

export const contactUs = async (req, res) => {
  try {
    const { name, email, subject, message } = req.body;

    if (!name || !email || !subject || !message) {
      return res.status(400).json({ error: 'All fields are required' });
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email address' });
    }

    const result = await dbRun(
      'INSERT INTO contact_submissions (name, email, subject, message) VALUES (?, ?, ?, ?)',
      [name, email, subject, message]
    );

    res.status(201).json({
      message: 'Contact submission received successfully',
      submissionId: result.id
    });
  } catch (error) {
    console.error('Contact submission error:', error);
    res.status(500).json({ error: 'Server error submitting contact form' });
  }
};
