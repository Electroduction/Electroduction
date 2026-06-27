import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getLessons = async (req, res) => {
  try {
    const { topicId } = req.params;
    const { difficulty, sort = 'recent' } = req.query;

    let query = `
      SELECT l.*, u.username, u.display_name,
             (SELECT COUNT(*) FROM lesson_progress WHERE lesson_id = l.id AND is_completed = 1) as completion_count
      FROM lessons l
      JOIN users u ON l.teacher_id = u.id
      WHERE l.is_published = 1
    `;

    const params = [];

    if (topicId) {
      query += ' AND l.topic_id = ?';
      params.push(topicId);
    }

    if (difficulty) {
      query += ' AND l.difficulty_level = ?';
      params.push(difficulty);
    }

    if (sort === 'popular') {
      query += ' ORDER BY l.view_count DESC';
    } else if (sort === 'rated') {
      query += ' ORDER BY l.rating_avg DESC';
    } else {
      query += ' ORDER BY l.created_at DESC';
    }

    const lessons = await dbAll(query, params);
    res.json({ lessons });
  } catch (error) {
    console.error('Get lessons error:', error);
    res.status(500).json({ error: 'Server error fetching lessons' });
  }
};

export const getLesson = async (req, res) => {
  try {
    const { id } = req.params;

    const lesson = await dbGet(
      `SELECT l.*, u.username, u.display_name, u.avatar_url, t.name as topic_name
       FROM lessons l
       JOIN users u ON l.teacher_id = u.id
       JOIN topics t ON l.topic_id = t.id
       WHERE l.id = ?`,
      [id]
    );

    if (!lesson) {
      return res.status(404).json({ error: 'Lesson not found' });
    }

    // Increment view count
    await dbRun('UPDATE lessons SET view_count = view_count + 1 WHERE id = ?', [id]);

    // Get user progress if authenticated
    let progress = null;
    if (req.user) {
      progress = await dbGet(
        'SELECT * FROM lesson_progress WHERE user_id = ? AND lesson_id = ?',
        [req.user.id, id]
      );
    }

    res.json({ lesson, progress });
  } catch (error) {
    console.error('Get lesson error:', error);
    res.status(500).json({ error: 'Server error fetching lesson' });
  }
};

export const createLesson = async (req, res) => {
  try {
    const {
      topicId, title, description, content, difficultyLevel,
      estimatedDuration, isAiContent, aiLabel, offersCredit, creditType, creditHours
    } = req.body;

    if (!title || !content || !topicId) {
      return res.status(400).json({ error: 'Title, content, and topic are required' });
    }

    const result = await dbRun(
      `INSERT INTO lessons (topic_id, teacher_id, title, description, content, difficulty_level,
                            estimated_duration, is_ai_content, ai_label, offers_credit, credit_type, credit_hours)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [topicId, req.user.id, title, description, content, difficultyLevel || 'beginner',
       estimatedDuration || 0, isAiContent || 0, aiLabel || null, offersCredit || 0,
       creditType || null, creditHours || 0]
    );

    res.status(201).json({
      message: 'Lesson created successfully',
      lessonId: result.id
    });
  } catch (error) {
    console.error('Create lesson error:', error);
    res.status(500).json({ error: 'Server error creating lesson' });
  }
};

export const updateLesson = async (req, res) => {
  try {
    const { id } = req.params;
    const {
      title, description, content, difficultyLevel, estimatedDuration,
      isAiContent, aiLabel, offersCredit, creditType, creditHours, isPublished
    } = req.body;

    // Verify ownership
    const lesson = await dbGet('SELECT teacher_id FROM lessons WHERE id = ?', [id]);
    if (!lesson) {
      return res.status(404).json({ error: 'Lesson not found' });
    }
    if (lesson.teacher_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to edit this lesson' });
    }

    await dbRun(
      `UPDATE lessons
       SET title = ?, description = ?, content = ?, difficulty_level = ?, estimated_duration = ?,
           is_ai_content = ?, ai_label = ?, offers_credit = ?, credit_type = ?, credit_hours = ?,
           is_published = ?, updated_at = datetime('now')
       WHERE id = ?`,
      [title, description, content, difficultyLevel, estimatedDuration, isAiContent || 0,
       aiLabel || null, offersCredit || 0, creditType || null, creditHours || 0,
       isPublished !== undefined ? isPublished : 1, id]
    );

    res.json({ message: 'Lesson updated successfully' });
  } catch (error) {
    console.error('Update lesson error:', error);
    res.status(500).json({ error: 'Server error updating lesson' });
  }
};

export const deleteLesson = async (req, res) => {
  try {
    const { id } = req.params;

    // Verify ownership
    const lesson = await dbGet('SELECT teacher_id FROM lessons WHERE id = ?', [id]);
    if (!lesson) {
      return res.status(404).json({ error: 'Lesson not found' });
    }
    if (lesson.teacher_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to delete this lesson' });
    }

    await dbRun('DELETE FROM lessons WHERE id = ?', [id]);

    res.json({ message: 'Lesson deleted successfully' });
  } catch (error) {
    console.error('Delete lesson error:', error);
    res.status(500).json({ error: 'Server error deleting lesson' });
  }
};

export const startLesson = async (req, res) => {
  try {
    const { lessonId } = req.params;

    // Check if already started
    const existing = await dbGet(
      'SELECT * FROM lesson_progress WHERE user_id = ? AND lesson_id = ?',
      [req.user.id, lessonId]
    );

    if (existing) {
      return res.json({ message: 'Lesson already started', progress: existing });
    }

    await dbRun(
      'INSERT INTO lesson_progress (user_id, lesson_id) VALUES (?, ?)',
      [req.user.id, lessonId]
    );

    res.json({ message: 'Lesson started successfully' });
  } catch (error) {
    console.error('Start lesson error:', error);
    res.status(500).json({ error: 'Server error starting lesson' });
  }
};

export const updateProgress = async (req, res) => {
  try {
    const { lessonId } = req.params;
    const { progressPercentage, timeSpent } = req.body;

    await dbRun(
      `UPDATE lesson_progress
       SET progress_percentage = ?, time_spent = time_spent + ?
       WHERE user_id = ? AND lesson_id = ?`,
      [progressPercentage, timeSpent || 0, req.user.id, lessonId]
    );

    res.json({ message: 'Progress updated successfully' });
  } catch (error) {
    console.error('Update progress error:', error);
    res.status(500).json({ error: 'Server error updating progress' });
  }
};

export const completeLesson = async (req, res) => {
  try {
    const { lessonId } = req.params;
    const { rating, review } = req.body;

    await dbRun(
      `UPDATE lesson_progress
       SET is_completed = 1, progress_percentage = 100, completed_at = datetime('now'),
           rating = ?, review = ?
       WHERE user_id = ? AND lesson_id = ?`,
      [rating || null, review || null, req.user.id, lessonId]
    );

    // Award karma and reward points
    await dbRun(
      'UPDATE users SET karma_points = karma_points + 10, reward_points = reward_points + 5 WHERE id = ?',
      [req.user.id]
    );

    // Update lesson rating
    if (rating) {
      const stats = await dbGet(
        'SELECT AVG(rating) as avg_rating, COUNT(rating) as rating_count FROM lesson_progress WHERE lesson_id = ? AND rating IS NOT NULL',
        [lessonId]
      );

      await dbRun(
        'UPDATE lessons SET rating_avg = ?, rating_count = ? WHERE id = ?',
        [stats.avg_rating, stats.rating_count, lessonId]
      );
    }

    res.json({ message: 'Lesson completed successfully' });
  } catch (error) {
    console.error('Complete lesson error:', error);
    res.status(500).json({ error: 'Server error completing lesson' });
  }
};
