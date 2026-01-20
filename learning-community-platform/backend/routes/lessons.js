import express from 'express';
import {
  getLessons,
  getLesson,
  createLesson,
  updateLesson,
  deleteLesson,
  startLesson,
  updateProgress,
  completeLesson
} from '../controllers/lessonsController.js';
import { authenticateToken, isTeacher, optionalAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', optionalAuth, getLessons);
router.get('/topics/:topicId', optionalAuth, getLessons);
router.get('/:id', optionalAuth, getLesson);

router.post('/', authenticateToken, isTeacher, createLesson);
router.put('/:id', authenticateToken, isTeacher, updateLesson);
router.delete('/:id', authenticateToken, isTeacher, deleteLesson);

router.post('/:lessonId/start', authenticateToken, startLesson);
router.put('/:lessonId/progress', authenticateToken, updateProgress);
router.post('/:lessonId/complete', authenticateToken, completeLesson);

export default router;
