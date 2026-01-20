import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import rateLimit from 'express-rate-limit';
import { createServer } from 'http';
import { Server } from 'socket.io';

// Import routes
import authRoutes from './routes/auth.js';
import topicsRoutes from './routes/topics.js';
import forumRoutes from './routes/forum.js';
import rewardsRoutes from './routes/rewards.js';
import lessonsRoutes from './routes/lessons.js';
import researchRoutes from './routes/research.js';
import messagingRoutes from './routes/messaging.js';
import teacherRoutes from './routes/teacher.js';
import notificationsRoutes from './routes/notifications.js';
import studyGroupsRoutes from './routes/studyGroups.js';

dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    methods: ['GET', 'POST']
  }
});

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Server is running' });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/topics', topicsRoutes);
app.use('/api/forum', forumRoutes);
app.use('/api/gamification', rewardsRoutes);
app.use('/api/lessons', lessonsRoutes);
app.use('/api/research', researchRoutes);
app.use('/api/messages', messagingRoutes);
app.use('/api/teacher', teacherRoutes);
app.use('/api/notifications', notificationsRoutes);
app.use('/api/study-groups', studyGroupsRoutes);

// Google Ads placeholder endpoint
app.get('/api/ads/config', (req, res) => {
  res.json({
    enabled: true,
    adClient: 'ca-pub-xxxxxxxxxxxxxxxxx', // Replace with actual Google AdSense client ID
    adSlots: {
      sidebar: '1234567890',
      footer: '0987654321',
      inContent: '1357924680'
    }
  });
});

// Socket.IO for real-time messaging
const userSockets = new Map(); // Map user IDs to socket IDs

io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  // Join user's personal room
  socket.on('join', (userId) => {
    userSockets.set(userId, socket.id);
    socket.join(`user:${userId}`);
    console.log(`User ${userId} joined their room`);
  });

  // Send message
  socket.on('send_message', (data) => {
    const { recipientId, message } = data;
    io.to(`user:${recipientId}`).emit('new_message', message);
  });

  // Join topic room for real-time forum updates
  socket.on('join_topic', (topicId) => {
    socket.join(`topic:${topicId}`);
    console.log(`Socket ${socket.id} joined topic ${topicId}`);
  });

  // Leave topic room
  socket.on('leave_topic', (topicId) => {
    socket.leave(`topic:${topicId}`);
  });

  // New forum post notification
  socket.on('new_post', (data) => {
    const { topicId, post } = data;
    io.to(`topic:${topicId}`).emit('post_created', post);
  });

  // New comment notification
  socket.on('new_comment', (data) => {
    const { postId, comment } = data;
    io.to(`post:${postId}`).emit('comment_created', comment);
  });

  // Disconnect
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
    // Remove user from map
    for (const [userId, socketId] of userSockets.entries()) {
      if (socketId === socket.id) {
        userSockets.delete(userId);
        break;
      }
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

const PORT = process.env.PORT || 5000;

httpServer.listen(PORT, () => {
  console.log(`
    ╔═══════════════════════════════════════════╗
    ║   Learning Community Platform Backend    ║
    ║   Server running on port ${PORT}            ║
    ║   Environment: ${process.env.NODE_ENV || 'development'}              ║
    ╚═══════════════════════════════════════════╝
  `);
});

export { io, userSockets };
