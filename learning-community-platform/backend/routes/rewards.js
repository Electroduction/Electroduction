import express from 'express';
import {
  getRewards,
  purchaseReward,
  getUserRewards,
  getBadges,
  purchaseBadge,
  getUserBadges,
  toggleBadgeDisplay,
  getLeaderboard
} from '../controllers/rewardsController.js';
import { authenticateToken } from '../middleware/auth.js';

const router = express.Router();

router.get('/rewards', getRewards);
router.post('/rewards/:rewardId/purchase', authenticateToken, purchaseReward);
router.get('/rewards/user', authenticateToken, getUserRewards);

router.get('/badges', getBadges);
router.post('/badges/:badgeId/purchase', authenticateToken, purchaseBadge);
router.get('/badges/user', authenticateToken, getUserBadges);
router.put('/badges/:badgeId/toggle', authenticateToken, toggleBadgeDisplay);

router.get('/leaderboard', getLeaderboard);

export default router;
