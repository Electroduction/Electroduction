import express from 'express';
import {
  applyToBeTeacher,
  getMyApplication,
  contactUs
} from '../controllers/teacherController.js';
import { authenticateToken } from '../middleware/auth.js';

const router = express.Router();

router.post('/apply', authenticateToken, applyToBeTeacher);
router.get('/application', authenticateToken, getMyApplication);
router.post('/contact', contactUs);

export default router;
