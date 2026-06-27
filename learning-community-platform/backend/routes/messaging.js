import express from 'express';
import {
  getMessages,
  sendMessage,
  getConversations,
  getUnreadCount
} from '../controllers/messagingController.js';
import { authenticateToken } from '../middleware/auth.js';

const router = express.Router();

router.get('/conversations', authenticateToken, getConversations);
router.get('/:userId', authenticateToken, getMessages);
router.post('/', authenticateToken, sendMessage);
router.get('/unread/count', authenticateToken, getUnreadCount);

export default router;
