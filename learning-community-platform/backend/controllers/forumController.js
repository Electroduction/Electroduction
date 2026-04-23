import { dbRun, dbGet, dbAll } from '../config/database.js';

export const getPosts = async (req, res) => {
  try {
    const { topicId } = req.params;
    const { sort = 'recent' } = req.query;

    let orderBy = 'fp.created_at DESC';
    if (sort === 'popular') orderBy = 'fp.upvotes DESC';
    if (sort === 'discussed') orderBy = '(SELECT COUNT(*) FROM forum_comments WHERE post_id = fp.id) DESC';

    const posts = await dbAll(
      `SELECT fp.*, u.username, u.display_name, u.avatar_url, u.rank_level,
              (SELECT COUNT(*) FROM forum_comments WHERE post_id = fp.id) as comment_count
       FROM forum_posts fp
       JOIN users u ON fp.user_id = u.id
       WHERE fp.topic_id = ?
       ORDER BY fp.is_pinned DESC, ${orderBy}`,
      [topicId]
    );

    res.json({ posts });
  } catch (error) {
    console.error('Get posts error:', error);
    res.status(500).json({ error: 'Server error fetching posts' });
  }
};

export const getPost = async (req, res) => {
  try {
    const { id } = req.params;

    const post = await dbGet(
      `SELECT fp.*, u.username, u.display_name, u.avatar_url, u.rank_level
       FROM forum_posts fp
       JOIN users u ON fp.user_id = u.id
       WHERE fp.id = ?`,
      [id]
    );

    if (!post) {
      return res.status(404).json({ error: 'Post not found' });
    }

    // Increment view count
    await dbRun('UPDATE forum_posts SET view_count = view_count + 1 WHERE id = ?', [id]);

    res.json({ post });
  } catch (error) {
    console.error('Get post error:', error);
    res.status(500).json({ error: 'Server error fetching post' });
  }
};

export const createPost = async (req, res) => {
  try {
    const { topicId, title, content, isAiContent, aiLabel, postType } = req.body;

    if (!title || !content) {
      return res.status(400).json({ error: 'Title and content are required' });
    }

    const result = await dbRun(
      `INSERT INTO forum_posts (topic_id, user_id, title, content, is_ai_content, ai_label, post_type)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [topicId, req.user.id, title, content, isAiContent || 0, aiLabel || null, postType || 'discussion']
    );

    // Award karma for posting
    await dbRun('UPDATE users SET karma_points = karma_points + 5 WHERE id = ?', [req.user.id]);

    res.status(201).json({
      message: 'Post created successfully',
      postId: result.id
    });
  } catch (error) {
    console.error('Create post error:', error);
    res.status(500).json({ error: 'Server error creating post' });
  }
};

export const updatePost = async (req, res) => {
  try {
    const { id } = req.params;
    const { title, content, isAiContent, aiLabel } = req.body;

    // Verify ownership
    const post = await dbGet('SELECT user_id FROM forum_posts WHERE id = ?', [id]);
    if (!post) {
      return res.status(404).json({ error: 'Post not found' });
    }
    if (post.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to edit this post' });
    }

    await dbRun(
      `UPDATE forum_posts
       SET title = ?, content = ?, is_ai_content = ?, ai_label = ?, updated_at = datetime('now')
       WHERE id = ?`,
      [title, content, isAiContent || 0, aiLabel || null, id]
    );

    res.json({ message: 'Post updated successfully' });
  } catch (error) {
    console.error('Update post error:', error);
    res.status(500).json({ error: 'Server error updating post' });
  }
};

export const deletePost = async (req, res) => {
  try {
    const { id } = req.params;

    // Verify ownership
    const post = await dbGet('SELECT user_id FROM forum_posts WHERE id = ?', [id]);
    if (!post) {
      return res.status(404).json({ error: 'Post not found' });
    }
    if (post.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to delete this post' });
    }

    await dbRun('DELETE FROM forum_posts WHERE id = ?', [id]);

    res.json({ message: 'Post deleted successfully' });
  } catch (error) {
    console.error('Delete post error:', error);
    res.status(500).json({ error: 'Server error deleting post' });
  }
};

export const getComments = async (req, res) => {
  try {
    const { postId } = req.params;

    const comments = await dbAll(
      `SELECT fc.*, u.username, u.display_name, u.avatar_url, u.rank_level
       FROM forum_comments fc
       JOIN users u ON fc.user_id = u.id
       WHERE fc.post_id = ?
       ORDER BY fc.created_at ASC`,
      [postId]
    );

    res.json({ comments });
  } catch (error) {
    console.error('Get comments error:', error);
    res.status(500).json({ error: 'Server error fetching comments' });
  }
};

export const createComment = async (req, res) => {
  try {
    const { postId, content, parentCommentId, isAiContent, aiLabel } = req.body;

    if (!content) {
      return res.status(400).json({ error: 'Content is required' });
    }

    const result = await dbRun(
      `INSERT INTO forum_comments (post_id, user_id, parent_comment_id, content, is_ai_content, ai_label)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [postId, req.user.id, parentCommentId || null, content, isAiContent || 0, aiLabel || null]
    );

    // Award karma for commenting
    await dbRun('UPDATE users SET karma_points = karma_points + 2 WHERE id = ?', [req.user.id]);

    res.status(201).json({
      message: 'Comment created successfully',
      commentId: result.id
    });
  } catch (error) {
    console.error('Create comment error:', error);
    res.status(500).json({ error: 'Server error creating comment' });
  }
};

export const votePost = async (req, res) => {
  try {
    const { postId } = req.params;
    const { voteType } = req.body; // 'upvote' or 'downvote'

    if (!['upvote', 'downvote'].includes(voteType)) {
      return res.status(400).json({ error: 'Invalid vote type' });
    }

    // Check if already voted
    const existingVote = await dbGet(
      'SELECT * FROM votes WHERE user_id = ? AND target_type = ? AND target_id = ?',
      [req.user.id, 'post', postId]
    );

    if (existingVote) {
      if (existingVote.vote_type === voteType) {
        // Remove vote
        await dbRun('DELETE FROM votes WHERE id = ?', [existingVote.id]);

        if (voteType === 'upvote') {
          await dbRun('UPDATE forum_posts SET upvotes = upvotes - 1 WHERE id = ?', [postId]);
        } else {
          await dbRun('UPDATE forum_posts SET downvotes = downvotes - 1 WHERE id = ?', [postId]);
        }

        return res.json({ message: 'Vote removed', action: 'removed' });
      } else {
        // Change vote
        await dbRun('UPDATE votes SET vote_type = ? WHERE id = ?', [voteType, existingVote.id]);

        if (voteType === 'upvote') {
          await dbRun('UPDATE forum_posts SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', [postId]);
        } else {
          await dbRun('UPDATE forum_posts SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', [postId]);
        }

        return res.json({ message: 'Vote changed', action: 'changed' });
      }
    }

    // Add new vote
    await dbRun(
      'INSERT INTO votes (user_id, target_type, target_id, vote_type) VALUES (?, ?, ?, ?)',
      [req.user.id, 'post', postId, voteType]
    );

    if (voteType === 'upvote') {
      await dbRun('UPDATE forum_posts SET upvotes = upvotes + 1 WHERE id = ?', [postId]);

      // Award karma to post author
      const post = await dbGet('SELECT user_id FROM forum_posts WHERE id = ?', [postId]);
      if (post && post.user_id !== req.user.id) {
        await dbRun('UPDATE users SET karma_points = karma_points + 1 WHERE id = ?', [post.user_id]);
      }
    } else {
      await dbRun('UPDATE forum_posts SET downvotes = downvotes + 1 WHERE id = ?', [postId]);
    }

    res.json({ message: 'Vote added', action: 'added' });
  } catch (error) {
    console.error('Vote post error:', error);
    res.status(500).json({ error: 'Server error voting on post' });
  }
};

export const voteComment = async (req, res) => {
  try {
    const { commentId } = req.params;
    const { voteType } = req.body;

    if (!['upvote', 'downvote'].includes(voteType)) {
      return res.status(400).json({ error: 'Invalid vote type' });
    }

    // Check if already voted
    const existingVote = await dbGet(
      'SELECT * FROM votes WHERE user_id = ? AND target_type = ? AND target_id = ?',
      [req.user.id, 'comment', commentId]
    );

    if (existingVote) {
      if (existingVote.vote_type === voteType) {
        await dbRun('DELETE FROM votes WHERE id = ?', [existingVote.id]);

        if (voteType === 'upvote') {
          await dbRun('UPDATE forum_comments SET upvotes = upvotes - 1 WHERE id = ?', [commentId]);
        } else {
          await dbRun('UPDATE forum_comments SET downvotes = downvotes - 1 WHERE id = ?', [commentId]);
        }

        return res.json({ message: 'Vote removed', action: 'removed' });
      } else {
        await dbRun('UPDATE votes SET vote_type = ? WHERE id = ?', [voteType, existingVote.id]);

        if (voteType === 'upvote') {
          await dbRun('UPDATE forum_comments SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', [commentId]);
        } else {
          await dbRun('UPDATE forum_comments SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', [commentId]);
        }

        return res.json({ message: 'Vote changed', action: 'changed' });
      }
    }

    await dbRun(
      'INSERT INTO votes (user_id, target_type, target_id, vote_type) VALUES (?, ?, ?, ?)',
      [req.user.id, 'comment', commentId, voteType]
    );

    if (voteType === 'upvote') {
      await dbRun('UPDATE forum_comments SET upvotes = upvotes + 1 WHERE id = ?', [commentId]);

      const comment = await dbGet('SELECT user_id FROM forum_comments WHERE id = ?', [commentId]);
      if (comment && comment.user_id !== req.user.id) {
        await dbRun('UPDATE users SET karma_points = karma_points + 1 WHERE id = ?', [comment.user_id]);
      }
    } else {
      await dbRun('UPDATE forum_comments SET downvotes = downvotes + 1 WHERE id = ?', [commentId]);
    }

    res.json({ message: 'Vote added', action: 'added' });
  } catch (error) {
    console.error('Vote comment error:', error);
    res.status(500).json({ error: 'Server error voting on comment' });
  }
};
