import express from 'express';
import {
  getPosts,
  getPost,
  createPost,
  updatePost,
  deletePost,
  getComments,
  createComment,
  votePost,
  voteComment
} from '../controllers/forumController.js';
import { authenticateToken, optionalAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/topics/:topicId/posts', optionalAuth, getPosts);
router.get('/posts/:id', optionalAuth, getPost);
router.post('/posts', authenticateToken, createPost);
router.put('/posts/:id', authenticateToken, updatePost);
router.delete('/posts/:id', authenticateToken, deletePost);

router.get('/posts/:postId/comments', optionalAuth, getComments);
router.post('/comments', authenticateToken, createComment);

router.post('/posts/:postId/vote', authenticateToken, votePost);
router.post('/comments/:commentId/vote', authenticateToken, voteComment);

export default router;
