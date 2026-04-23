import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getStudyGroups = async (req, res) => {
  try {
    const { topicId } = req.query;

    let query = `
      SELECT sg.*, u.username as creator_username, u.display_name as creator_name,
             t.name as topic_name
      FROM study_groups sg
      JOIN users u ON sg.creator_id = u.id
      JOIN topics t ON sg.topic_id = t.id
      WHERE sg.is_private = 0
    `;

    const params = [];

    if (topicId) {
      query += ' AND sg.topic_id = ?';
      params.push(topicId);
    }

    query += ' ORDER BY sg.created_at DESC';

    const groups = await dbAll(query, params);

    res.json({ groups });
  } catch (error) {
    console.error('Get study groups error:', error);
    res.status(500).json({ error: 'Server error fetching study groups' });
  }
};

export const getStudyGroup = async (req, res) => {
  try {
    const { id } = req.params;

    const group = await dbGet(
      `SELECT sg.*, u.username as creator_username, u.display_name as creator_name,
              t.name as topic_name
       FROM study_groups sg
       JOIN users u ON sg.creator_id = u.id
       JOIN topics t ON sg.topic_id = t.id
       WHERE sg.id = ?`,
      [id]
    );

    if (!group) {
      return res.status(404).json({ error: 'Study group not found' });
    }

    // Get members
    const members = await dbAll(
      `SELECT u.id, u.username, u.display_name, u.avatar_url, u.rank_level,
              sgm.role, sgm.joined_at
       FROM study_group_members sgm
       JOIN users u ON sgm.user_id = u.id
       WHERE sgm.group_id = ?
       ORDER BY sgm.joined_at ASC`,
      [id]
    );

    res.json({ group, members });
  } catch (error) {
    console.error('Get study group error:', error);
    res.status(500).json({ error: 'Server error fetching study group' });
  }
};

export const createStudyGroup = async (req, res) => {
  try {
    const { topicId, name, description, isPrivate, maxMembers } = req.body;

    if (!name || !topicId) {
      return res.status(400).json({ error: 'Name and topic are required' });
    }

    const result = await dbRun(
      `INSERT INTO study_groups (topic_id, creator_id, name, description, is_private, max_members)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [topicId, req.user.id, name, description || '', isPrivate || 0, maxMembers || 50]
    );

    // Add creator as admin member
    await dbRun(
      'INSERT INTO study_group_members (group_id, user_id, role) VALUES (?, ?, ?)',
      [result.id, req.user.id, 'admin']
    );

    res.status(201).json({
      message: 'Study group created successfully',
      groupId: result.id
    });
  } catch (error) {
    console.error('Create study group error:', error);
    res.status(500).json({ error: 'Server error creating study group' });
  }
};

export const joinStudyGroup = async (req, res) => {
  try {
    const { id } = req.params;

    // Check if group exists and has space
    const group = await dbGet('SELECT * FROM study_groups WHERE id = ?', [id]);
    if (!group) {
      return res.status(404).json({ error: 'Study group not found' });
    }

    if (group.max_members && group.member_count >= group.max_members) {
      return res.status(400).json({ error: 'Study group is full' });
    }

    // Check if already a member
    const existing = await dbGet(
      'SELECT id FROM study_group_members WHERE group_id = ? AND user_id = ?',
      [id, req.user.id]
    );

    if (existing) {
      return res.status(409).json({ error: 'Already a member of this group' });
    }

    // Join group
    await dbRun(
      'INSERT INTO study_group_members (group_id, user_id) VALUES (?, ?)',
      [id, req.user.id]
    );

    // Update member count
    await dbRun(
      'UPDATE study_groups SET member_count = member_count + 1 WHERE id = ?',
      [id]
    );

    res.json({ message: 'Successfully joined study group' });
  } catch (error) {
    console.error('Join study group error:', error);
    res.status(500).json({ error: 'Server error joining study group' });
  }
};

export const leaveStudyGroup = async (req, res) => {
  try {
    const { id } = req.params;

    const membership = await dbGet(
      'SELECT * FROM study_group_members WHERE group_id = ? AND user_id = ?',
      [id, req.user.id]
    );

    if (!membership) {
      return res.status(404).json({ error: 'Not a member of this group' });
    }

    // Don't allow admin/creator to leave if there are other members
    if (membership.role === 'admin') {
      const memberCount = await dbGet(
        'SELECT COUNT(*) as count FROM study_group_members WHERE group_id = ?',
        [id]
      );

      if (memberCount.count > 1) {
        return res.status(400).json({
          error: 'Transfer admin role to another member before leaving'
        });
      }
    }

    // Leave group
    await dbRun(
      'DELETE FROM study_group_members WHERE group_id = ? AND user_id = ?',
      [id, req.user.id]
    );

    // Update member count
    await dbRun(
      'UPDATE study_groups SET member_count = member_count - 1 WHERE id = ?',
      [id]
    );

    res.json({ message: 'Successfully left study group' });
  } catch (error) {
    console.error('Leave study group error:', error);
    res.status(500).json({ error: 'Server error leaving study group' });
  }
};

export const getUserStudyGroups = async (req, res) => {
  try {
    const groups = await dbAll(
      `SELECT sg.*, t.name as topic_name, sgm.role, sgm.joined_at
       FROM study_groups sg
       JOIN topics t ON sg.topic_id = t.id
       JOIN study_group_members sgm ON sg.id = sgm.group_id
       WHERE sgm.user_id = ?
       ORDER BY sgm.joined_at DESC`,
      [req.user.id]
    );

    res.json({ groups });
  } catch (error) {
    console.error('Get user study groups error:', error);
    res.status(500).json({ error: 'Server error fetching user study groups' });
  }
};
