import express from 'express';
import {
  getStudyGroups,
  getStudyGroup,
  createStudyGroup,
  joinStudyGroup,
  leaveStudyGroup,
  getUserStudyGroups
} from '../controllers/studyGroupsController.js';
import { authenticateToken, optionalAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', optionalAuth, getStudyGroups);
router.get('/user', authenticateToken, getUserStudyGroups);
router.get('/:id', optionalAuth, getStudyGroup);
router.post('/', authenticateToken, createStudyGroup);
router.post('/:id/join', authenticateToken, joinStudyGroup);
router.delete('/:id/leave', authenticateToken, leaveStudyGroup);

export default router;
