import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { dbRun, dbGet } from '../config/database.js';
import dotenv from 'dotenv';

dotenv.config();

export const register = async (req, res) => {
  try {
    const { username, email, password, displayName } = req.body;

    // Validation
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'Username, email, and password are required' });
    }

    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }

    // Check if user exists
    const existingUser = await dbGet(
      'SELECT id FROM users WHERE username = ? OR email = ?',
      [username, email]
    );

    if (existingUser) {
      return res.status(409).json({ error: 'Username or email already exists' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const result = await dbRun(
      `INSERT INTO users (username, email, password, display_name, last_login)
       VALUES (?, ?, ?, ?, datetime('now'))`,
      [username, email, hashedPassword, displayName || username]
    );

    // Generate token
    const token = jwt.sign(
      { id: result.id, username, email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.status(201).json({
      message: 'User registered successfully',
      token,
      user: {
        id: result.id,
        username,
        email,
        displayName: displayName || username
      }
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ error: 'Server error during registration' });
  }
};

export const login = async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Find user
    const user = await dbGet(
      'SELECT * FROM users WHERE username = ? OR email = ?',
      [username, username]
    );

    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Verify password
    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Update last login and streak
    const lastLogin = new Date(user.last_login);
    const now = new Date();
    const daysDiff = Math.floor((now - lastLogin) / (1000 * 60 * 60 * 24));

    let newStreak = user.learning_streak;
    if (daysDiff === 1) {
      newStreak += 1;
    } else if (daysDiff > 1) {
      newStreak = 1;
    }

    await dbRun(
      `UPDATE users SET last_login = datetime('now'), learning_streak = ? WHERE id = ?`,
      [newStreak, user.id]
    );

    // Generate token
    const token = jwt.sign(
      {
        id: user.id,
        username: user.username,
        email: user.email,
        is_teacher: user.is_teacher
      },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    // Remove password from response
    delete user.password;

    res.json({
      message: 'Login successful',
      token,
      user: {
        ...user,
        learning_streak: newStreak
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Server error during login' });
  }
};

export const getProfile = async (req, res) => {
  try {
    const user = await dbGet(
      'SELECT id, username, email, display_name, bio, avatar_url, karma_points, rank_level, reward_points, learning_streak, is_teacher, created_at FROM users WHERE id = ?',
      [req.user.id]
    );

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Server error fetching profile' });
  }
};

export const updateProfile = async (req, res) => {
  try {
    const { displayName, bio, avatarUrl } = req.body;

    await dbRun(
      'UPDATE users SET display_name = ?, bio = ?, avatar_url = ?, updated_at = datetime("now") WHERE id = ?',
      [displayName, bio, avatarUrl, req.user.id]
    );

    const updatedUser = await dbGet(
      'SELECT id, username, email, display_name, bio, avatar_url, karma_points, rank_level, reward_points, learning_streak FROM users WHERE id = ?',
      [req.user.id]
    );

    res.json({ message: 'Profile updated successfully', user: updatedUser });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: 'Server error updating profile' });
  }
};
