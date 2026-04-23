import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getAllTopics = async (req, res) => {
  try {
    const topics = await dbAll('SELECT * FROM topics ORDER BY member_count DESC');
    res.json({ topics });
  } catch (error) {
    console.error('Get topics error:', error);
    res.status(500).json({ error: 'Server error fetching topics' });
  }
};

export const getTopic = async (req, res) => {
  try {
    const { id } = req.params;
    const topic = await dbGet('SELECT * FROM topics WHERE id = ?', [id]);

    if (!topic) {
      return res.status(404).json({ error: 'Topic not found' });
    }

    res.json({ topic });
  } catch (error) {
    console.error('Get topic error:', error);
    res.status(500).json({ error: 'Server error fetching topic' });
  }
};

export const joinTopic = async (req, res) => {
  try {
    const { topicId } = req.params;
    const { skillLevel } = req.body;

    // Check if already joined
    const existing = await dbGet(
      'SELECT id FROM user_topics WHERE user_id = ? AND topic_id = ?',
      [req.user.id, topicId]
    );

    if (existing) {
      return res.status(409).json({ error: 'Already joined this topic' });
    }

    // Join topic
    await dbRun(
      'INSERT INTO user_topics (user_id, topic_id, skill_level) VALUES (?, ?, ?)',
      [req.user.id, topicId, skillLevel || 'beginner']
    );

    // Update member count
    await dbRun(
      'UPDATE topics SET member_count = member_count + 1 WHERE id = ?',
      [topicId]
    );

    res.json({ message: 'Successfully joined topic' });
  } catch (error) {
    console.error('Join topic error:', error);
    res.status(500).json({ error: 'Server error joining topic' });
  }
};

export const leaveTopic = async (req, res) => {
  try {
    const { topicId } = req.params;

    const result = await dbRun(
      'DELETE FROM user_topics WHERE user_id = ? AND topic_id = ?',
      [req.user.id, topicId]
    );

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Not a member of this topic' });
    }

    // Update member count
    await dbRun(
      'UPDATE topics SET member_count = member_count - 1 WHERE id = ?',
      [topicId]
    );

    res.json({ message: 'Successfully left topic' });
  } catch (error) {
    console.error('Leave topic error:', error);
    res.status(500).json({ error: 'Server error leaving topic' });
  }
};

export const getUserTopics = async (req, res) => {
  try {
    const topics = await dbAll(
      `SELECT t.*, ut.skill_level, ut.joined_at
       FROM topics t
       JOIN user_topics ut ON t.id = ut.topic_id
       WHERE ut.user_id = ?
       ORDER BY ut.joined_at DESC`,
      [req.user.id]
    );

    res.json({ topics });
  } catch (error) {
    console.error('Get user topics error:', error);
    res.status(500).json({ error: 'Server error fetching user topics' });
  }
};
