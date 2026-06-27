import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getNotifications = async (req, res) => {
  try {
    const { limit = 50, unreadOnly = false } = req.query;

    let query = 'SELECT * FROM notifications WHERE user_id = ?';
    if (unreadOnly === 'true') {
      query += ' AND is_read = 0';
    }
    query += ' ORDER BY created_at DESC LIMIT ?';

    const notifications = await dbAll(query, [req.user.id, parseInt(limit)]);

    res.json({ notifications });
  } catch (error) {
    console.error('Get notifications error:', error);
    res.status(500).json({ error: 'Server error fetching notifications' });
  }
};

export const markAsRead = async (req, res) => {
  try {
    const { id } = req.params;

    // Verify ownership
    const notification = await dbGet(
      'SELECT user_id FROM notifications WHERE id = ?',
      [id]
    );

    if (!notification) {
      return res.status(404).json({ error: 'Notification not found' });
    }

    if (notification.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized' });
    }

    await dbRun('UPDATE notifications SET is_read = 1 WHERE id = ?', [id]);

    res.json({ message: 'Notification marked as read' });
  } catch (error) {
    console.error('Mark notification error:', error);
    res.status(500).json({ error: 'Server error marking notification' });
  }
};

export const markAllAsRead = async (req, res) => {
  try {
    await dbRun('UPDATE notifications SET is_read = 1 WHERE user_id = ?', [req.user.id]);

    res.json({ message: 'All notifications marked as read' });
  } catch (error) {
    console.error('Mark all notifications error:', error);
    res.status(500).json({ error: 'Server error marking notifications' });
  }
};

export const getUnreadCount = async (req, res) => {
  try {
    const result = await dbGet(
      'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0',
      [req.user.id]
    );

    res.json({ unreadCount: result.count });
  } catch (error) {
    console.error('Get unread count error:', error);
    res.status(500).json({ error: 'Server error fetching unread count' });
  }
};

export const deleteNotification = async (req, res) => {
  try {
    const { id } = req.params;

    // Verify ownership
    const notification = await dbGet(
      'SELECT user_id FROM notifications WHERE id = ?',
      [id]
    );

    if (!notification) {
      return res.status(404).json({ error: 'Notification not found' });
    }

    if (notification.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized' });
    }

    await dbRun('DELETE FROM notifications WHERE id = ?', [id]);

    res.json({ message: 'Notification deleted' });
  } catch (error) {
    console.error('Delete notification error:', error);
    res.status(500).json({ error: 'Server error deleting notification' });
  }
};
