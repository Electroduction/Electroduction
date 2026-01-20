import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getRewards = async (req, res) => {
  try {
    const rewards = await dbAll('SELECT * FROM rewards WHERE is_active = 1 ORDER BY price ASC');
    res.json({ rewards });
  } catch (error) {
    console.error('Get rewards error:', error);
    res.status(500).json({ error: 'Server error fetching rewards' });
  }
};

export const purchaseReward = async (req, res) => {
  try {
    const { rewardId } = req.params;

    // Get reward details
    const reward = await dbGet('SELECT * FROM rewards WHERE id = ? AND is_active = 1', [rewardId]);
    if (!reward) {
      return res.status(404).json({ error: 'Reward not found' });
    }

    // Check if user has enough points
    const user = await dbGet('SELECT reward_points FROM users WHERE id = ?', [req.user.id]);
    if (user.reward_points < reward.price) {
      return res.status(400).json({ error: 'Insufficient reward points' });
    }

    // Purchase reward
    await dbRun(
      'INSERT INTO user_rewards (user_id, reward_id) VALUES (?, ?)',
      [req.user.id, rewardId]
    );

    // Deduct points
    await dbRun(
      'UPDATE users SET reward_points = reward_points - ? WHERE id = ?',
      [reward.price, req.user.id]
    );

    res.json({ message: 'Reward purchased successfully', reward });
  } catch (error) {
    console.error('Purchase reward error:', error);
    res.status(500).json({ error: 'Server error purchasing reward' });
  }
};

export const getUserRewards = async (req, res) => {
  try {
    const rewards = await dbAll(
      `SELECT r.*, ur.purchased_at
       FROM rewards r
       JOIN user_rewards ur ON r.id = ur.reward_id
       WHERE ur.user_id = ?
       ORDER BY ur.purchased_at DESC`,
      [req.user.id]
    );

    res.json({ rewards });
  } catch (error) {
    console.error('Get user rewards error:', error);
    res.status(500).json({ error: 'Server error fetching user rewards' });
  }
};

export const getBadges = async (req, res) => {
  try {
    const badges = await dbAll('SELECT * FROM badges ORDER BY rarity, price ASC');
    res.json({ badges });
  } catch (error) {
    console.error('Get badges error:', error);
    res.status(500).json({ error: 'Server error fetching badges' });
  }
};

export const purchaseBadge = async (req, res) => {
  try {
    const { badgeId } = req.params;

    // Get badge details
    const badge = await dbGet('SELECT * FROM badges WHERE id = ?', [badgeId]);
    if (!badge) {
      return res.status(404).json({ error: 'Badge not found' });
    }

    // Check if already owned
    const existing = await dbGet(
      'SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?',
      [req.user.id, badgeId]
    );
    if (existing) {
      return res.status(409).json({ error: 'Badge already owned' });
    }

    // Check if user has enough points
    const user = await dbGet('SELECT reward_points FROM users WHERE id = ?', [req.user.id]);
    if (user.reward_points < badge.price) {
      return res.status(400).json({ error: 'Insufficient reward points' });
    }

    // Purchase badge
    await dbRun(
      'INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)',
      [req.user.id, badgeId]
    );

    // Deduct points
    await dbRun(
      'UPDATE users SET reward_points = reward_points - ? WHERE id = ?',
      [badge.price, req.user.id]
    );

    res.json({ message: 'Badge purchased successfully', badge });
  } catch (error) {
    console.error('Purchase badge error:', error);
    res.status(500).json({ error: 'Server error purchasing badge' });
  }
};

export const getUserBadges = async (req, res) => {
  try {
    const badges = await dbAll(
      `SELECT b.*, ub.is_displayed, ub.earned_at
       FROM badges b
       JOIN user_badges ub ON b.id = ub.badge_id
       WHERE ub.user_id = ?
       ORDER BY ub.earned_at DESC`,
      [req.user.id]
    );

    res.json({ badges });
  } catch (error) {
    console.error('Get user badges error:', error);
    res.status(500).json({ error: 'Server error fetching user badges' });
  }
};

export const toggleBadgeDisplay = async (req, res) => {
  try {
    const { badgeId } = req.params;

    const userBadge = await dbGet(
      'SELECT * FROM user_badges WHERE user_id = ? AND badge_id = ?',
      [req.user.id, badgeId]
    );

    if (!userBadge) {
      return res.status(404).json({ error: 'Badge not owned' });
    }

    await dbRun(
      'UPDATE user_badges SET is_displayed = ? WHERE user_id = ? AND badge_id = ?',
      [!userBadge.is_displayed, req.user.id, badgeId]
    );

    res.json({ message: 'Badge display toggled', isDisplayed: !userBadge.is_displayed });
  } catch (error) {
    console.error('Toggle badge error:', error);
    res.status(500).json({ error: 'Server error toggling badge display' });
  }
};

export const getLeaderboard = async (req, res) => {
  try {
    const { type = 'karma', limit = 50 } = req.query;

    let orderBy = 'karma_points';
    if (type === 'rewards') orderBy = 'reward_points';
    if (type === 'streak') orderBy = 'learning_streak';

    const leaderboard = await dbAll(
      `SELECT id, username, display_name, avatar_url, rank_level, karma_points, reward_points, learning_streak
       FROM users
       ORDER BY ${orderBy} DESC
       LIMIT ?`,
      [parseInt(limit)]
    );

    res.json({ leaderboard });
  } catch (error) {
    console.error('Get leaderboard error:', error);
    res.status(500).json({ error: 'Server error fetching leaderboard' });
  }
};
