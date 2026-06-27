import express from 'express';
import {
  getAllTopics,
  getTopic,
  joinTopic,
  leaveTopic,
  getUserTopics
} from '../controllers/topicsController.js';
import { authenticateToken, optionalAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', optionalAuth, getAllTopics);
router.get('/user', authenticateToken, getUserTopics);
router.get('/:id', optionalAuth, getTopic);
router.post('/:topicId/join', authenticateToken, joinTopic);
router.delete('/:topicId/leave', authenticateToken, leaveTopic);

export default router;
