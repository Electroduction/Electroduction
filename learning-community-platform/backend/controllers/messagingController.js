import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getMessages = async (req, res) => {
  try {
    const { userId } = req.params;

    const messages = await dbAll(
      `SELECT m.*,
              sender.username as sender_username, sender.display_name as sender_display_name, sender.avatar_url as sender_avatar,
              recipient.username as recipient_username, recipient.display_name as recipient_display_name, recipient.avatar_url as recipient_avatar
       FROM messages m
       JOIN users sender ON m.sender_id = sender.id
       JOIN users recipient ON m.recipient_id = recipient.id
       WHERE (m.sender_id = ? AND m.recipient_id = ?) OR (m.sender_id = ? AND m.recipient_id = ?)
       ORDER BY m.created_at ASC`,
      [req.user.id, userId, userId, req.user.id]
    );

    // Mark messages as read
    await dbRun(
      'UPDATE messages SET is_read = 1 WHERE sender_id = ? AND recipient_id = ? AND is_read = 0',
      [userId, req.user.id]
    );

    res.json({ messages });
  } catch (error) {
    console.error('Get messages error:', error);
    res.status(500).json({ error: 'Server error fetching messages' });
  }
};

export const sendMessage = async (req, res) => {
  try {
    const { recipientId, content } = req.body;

    if (!content || !recipientId) {
      return res.status(400).json({ error: 'Recipient and content are required' });
    }

    // Check if recipient exists
    const recipient = await dbGet('SELECT id FROM users WHERE id = ?', [recipientId]);
    if (!recipient) {
      return res.status(404).json({ error: 'Recipient not found' });
    }

    const result = await dbRun(
      'INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)',
      [req.user.id, recipientId, content]
    );

    // Create notification for recipient
    await dbRun(
      `INSERT INTO notifications (user_id, type, title, message, link)
       VALUES (?, ?, ?, ?, ?)`,
      [recipientId, 'message', 'New Message', 'You have a new message', `/messages/${req.user.id}`]
    );

    res.status(201).json({
      message: 'Message sent successfully',
      messageId: result.id
    });
  } catch (error) {
    console.error('Send message error:', error);
    res.status(500).json({ error: 'Server error sending message' });
  }
};

export const getConversations = async (req, res) => {
  try {
    const conversations = await dbAll(
      `SELECT DISTINCT
              CASE
                WHEN m.sender_id = ? THEN m.recipient_id
                ELSE m.sender_id
              END as user_id,
              u.username, u.display_name, u.avatar_url,
              (SELECT content FROM messages
               WHERE (sender_id = ? AND recipient_id = u.id) OR (sender_id = u.id AND recipient_id = ?)
               ORDER BY created_at DESC LIMIT 1) as last_message,
              (SELECT created_at FROM messages
               WHERE (sender_id = ? AND recipient_id = u.id) OR (sender_id = u.id AND recipient_id = ?)
               ORDER BY created_at DESC LIMIT 1) as last_message_time,
              (SELECT COUNT(*) FROM messages
               WHERE sender_id = u.id AND recipient_id = ? AND is_read = 0) as unread_count
       FROM messages m
       JOIN users u ON (CASE WHEN m.sender_id = ? THEN m.recipient_id ELSE m.sender_id END) = u.id
       WHERE m.sender_id = ? OR m.recipient_id = ?
       ORDER BY last_message_time DESC`,
      [req.user.id, req.user.id, req.user.id, req.user.id, req.user.id, req.user.id, req.user.id, req.user.id, req.user.id]
    );

    res.json({ conversations });
  } catch (error) {
    console.error('Get conversations error:', error);
    res.status(500).json({ error: 'Server error fetching conversations' });
  }
};

export const getUnreadCount = async (req, res) => {
  try {
    const result = await dbGet(
      'SELECT COUNT(*) as count FROM messages WHERE recipient_id = ? AND is_read = 0',
      [req.user.id]
    );

    res.json({ unreadCount: result.count });
  } catch (error) {
    console.error('Get unread count error:', error);
    res.status(500).json({ error: 'Server error fetching unread count' });
  }
};
