import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getResearchPapers = async (req, res) => {
  try {
    const { topicId, status = 'published', seekingCollaborators } = req.query;

    let query = `
      SELECT rp.*, u.username, u.display_name, u.avatar_url
      FROM research_papers rp
      JOIN users u ON rp.user_id = u.id
      WHERE 1=1
    `;

    const params = [];

    if (status !== 'all') {
      query += ' AND rp.status = ?';
      params.push(status);
    }

    if (topicId) {
      query += ' AND rp.topic_id = ?';
      params.push(topicId);
    }

    if (seekingCollaborators === 'true') {
      query += ' AND rp.seeking_collaborators = 1';
    }

    query += ' ORDER BY rp.published_at DESC, rp.created_at DESC';

    const papers = await dbAll(query, params);
    res.json({ papers });
  } catch (error) {
    console.error('Get research papers error:', error);
    res.status(500).json({ error: 'Server error fetching research papers' });
  }
};

export const getResearchPaper = async (req, res) => {
  try {
    const { id } = req.params;

    const paper = await dbGet(
      `SELECT rp.*, u.username, u.display_name, u.avatar_url, u.rank_level,
              t.name as topic_name
       FROM research_papers rp
       JOIN users u ON rp.user_id = u.id
       LEFT JOIN topics t ON rp.topic_id = t.id
       WHERE rp.id = ?`,
      [id]
    );

    if (!paper) {
      return res.status(404).json({ error: 'Research paper not found' });
    }

    // Increment view count
    await dbRun('UPDATE research_papers SET view_count = view_count + 1 WHERE id = ?', [id]);

    res.json({ paper });
  } catch (error) {
    console.error('Get research paper error:', error);
    res.status(500).json({ error: 'Server error fetching research paper' });
  }
};

export const createResearchPaper = async (req, res) => {
  try {
    const {
      topicId, title, abstract, content, isAiContent, aiLabel,
      collaborators, seekingCollaborators
    } = req.body;

    if (!title || !content) {
      return res.status(400).json({ error: 'Title and content are required' });
    }

    const result = await dbRun(
      `INSERT INTO research_papers (user_id, topic_id, title, abstract, content, is_ai_content,
                                     ai_label, collaborators, seeking_collaborators, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [req.user.id, topicId || null, title, abstract || '', content, isAiContent || 0,
       aiLabel || null, collaborators || null, seekingCollaborators || 0, 'draft']
    );

    res.status(201).json({
      message: 'Research paper created successfully',
      paperId: result.id
    });
  } catch (error) {
    console.error('Create research paper error:', error);
    res.status(500).json({ error: 'Server error creating research paper' });
  }
};

export const updateResearchPaper = async (req, res) => {
  try {
    const { id } = req.params;
    const {
      title, abstract, content, isAiContent, aiLabel,
      collaborators, seekingCollaborators, status
    } = req.body;

    // Verify ownership
    const paper = await dbGet('SELECT user_id FROM research_papers WHERE id = ?', [id]);
    if (!paper) {
      return res.status(404).json({ error: 'Research paper not found' });
    }
    if (paper.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to edit this paper' });
    }

    await dbRun(
      `UPDATE research_papers
       SET title = ?, abstract = ?, content = ?, is_ai_content = ?, ai_label = ?,
           collaborators = ?, seeking_collaborators = ?, status = ?,
           updated_at = datetime('now')
       WHERE id = ?`,
      [title, abstract, content, isAiContent || 0, aiLabel || null,
       collaborators || null, seekingCollaborators || 0, status || 'draft', id]
    );

    res.json({ message: 'Research paper updated successfully' });
  } catch (error) {
    console.error('Update research paper error:', error);
    res.status(500).json({ error: 'Server error updating research paper' });
  }
};

export const publishResearchPaper = async (req, res) => {
  try {
    const { id } = req.params;

    // Verify ownership
    const paper = await dbGet('SELECT user_id FROM research_papers WHERE id = ?', [id]);
    if (!paper) {
      return res.status(404).json({ error: 'Research paper not found' });
    }
    if (paper.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to publish this paper' });
    }

    await dbRun(
      `UPDATE research_papers
       SET status = 'published', published_at = datetime('now')
       WHERE id = ?`,
      [id]
    );

    // Award karma and reward points for publishing
    await dbRun(
      'UPDATE users SET karma_points = karma_points + 50, reward_points = reward_points + 20 WHERE id = ?',
      [req.user.id]
    );

    res.json({ message: 'Research paper published successfully' });
  } catch (error) {
    console.error('Publish research paper error:', error);
    res.status(500).json({ error: 'Server error publishing research paper' });
  }
};

export const deleteResearchPaper = async (req, res) => {
  try {
    const { id } = req.params;

    // Verify ownership
    const paper = await dbGet('SELECT user_id FROM research_papers WHERE id = ?', [id]);
    if (!paper) {
      return res.status(404).json({ error: 'Research paper not found' });
    }
    if (paper.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to delete this paper' });
    }

    await dbRun('DELETE FROM research_papers WHERE id = ?', [id]);

    res.json({ message: 'Research paper deleted successfully' });
  } catch (error) {
    console.error('Delete research paper error:', error);
    res.status(500).json({ error: 'Server error deleting research paper' });
  }
};

export const getUserResearchPapers = async (req, res) => {
  try {
    const papers = await dbAll(
      `SELECT * FROM research_papers
       WHERE user_id = ?
       ORDER BY created_at DESC`,
      [req.user.id]
    );

    res.json({ papers });
  } catch (error) {
    console.error('Get user research papers error:', error);
    res.status(500).json({ error: 'Server error fetching user research papers' });
  }
};
