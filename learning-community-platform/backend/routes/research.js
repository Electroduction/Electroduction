import express from 'express';
import {
  getResearchPapers,
  getResearchPaper,
  createResearchPaper,
  updateResearchPaper,
  publishResearchPaper,
  deleteResearchPaper,
  getUserResearchPapers
} from '../controllers/researchController.js';
import { authenticateToken, optionalAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', optionalAuth, getResearchPapers);
router.get('/user', authenticateToken, getUserResearchPapers);
router.get('/:id', optionalAuth, getResearchPaper);

router.post('/', authenticateToken, createResearchPaper);
router.put('/:id', authenticateToken, updateResearchPaper);
router.post('/:id/publish', authenticateToken, publishResearchPaper);
router.delete('/:id', authenticateToken, deleteResearchPaper);

export default router;
