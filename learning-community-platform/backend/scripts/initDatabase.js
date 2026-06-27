import db from '../config/database.js';

const initDatabase = () => {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      // Users table
      db.run(`
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username VARCHAR(50) UNIQUE NOT NULL,
          email VARCHAR(100) UNIQUE NOT NULL,
          password VARCHAR(255) NOT NULL,
          display_name VARCHAR(100),
          bio TEXT,
          avatar_url VARCHAR(255),
          karma_points INTEGER DEFAULT 0,
          rank_level VARCHAR(20) DEFAULT 'Bronze',
          reward_points INTEGER DEFAULT 0,
          learning_streak INTEGER DEFAULT 0,
          last_login DATETIME,
          is_teacher BOOLEAN DEFAULT 0,
          teacher_status VARCHAR(20) DEFAULT 'none',
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);

      // Topics/Subjects table
      db.run(`
        CREATE TABLE IF NOT EXISTS topics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name VARCHAR(100) NOT NULL,
          description TEXT,
          category VARCHAR(50),
          icon_url VARCHAR(255),
          color VARCHAR(20),
          created_by INTEGER,
          member_count INTEGER DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (created_by) REFERENCES users(id)
        )
      `);

      // User topic subscriptions
      db.run(`
        CREATE TABLE IF NOT EXISTS user_topics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          topic_id INTEGER NOT NULL,
          skill_level VARCHAR(20) DEFAULT 'beginner',
          joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
          UNIQUE(user_id, topic_id)
        )
      `);

      // Forum posts
      db.run(`
        CREATE TABLE IF NOT EXISTS forum_posts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          topic_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL,
          title VARCHAR(255) NOT NULL,
          content TEXT NOT NULL,
          is_ai_content BOOLEAN DEFAULT 0,
          ai_label VARCHAR(50),
          post_type VARCHAR(20) DEFAULT 'discussion',
          upvotes INTEGER DEFAULT 0,
          downvotes INTEGER DEFAULT 0,
          view_count INTEGER DEFAULT 0,
          is_pinned BOOLEAN DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Forum comments/replies
      db.run(`
        CREATE TABLE IF NOT EXISTS forum_comments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          post_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL,
          parent_comment_id INTEGER,
          content TEXT NOT NULL,
          is_ai_content BOOLEAN DEFAULT 0,
          ai_label VARCHAR(50),
          upvotes INTEGER DEFAULT 0,
          downvotes INTEGER DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (post_id) REFERENCES forum_posts(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (parent_comment_id) REFERENCES forum_comments(id) ON DELETE CASCADE
        )
      `);

      // Direct messages
      db.run(`
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          sender_id INTEGER NOT NULL,
          recipient_id INTEGER NOT NULL,
          content TEXT NOT NULL,
          is_read BOOLEAN DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Lessons/Courses
      db.run(`
        CREATE TABLE IF NOT EXISTS lessons (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          topic_id INTEGER NOT NULL,
          teacher_id INTEGER NOT NULL,
          title VARCHAR(255) NOT NULL,
          description TEXT,
          content TEXT NOT NULL,
          difficulty_level VARCHAR(20),
          estimated_duration INTEGER,
          is_ai_content BOOLEAN DEFAULT 0,
          ai_label VARCHAR(50),
          offers_credit BOOLEAN DEFAULT 0,
          credit_type VARCHAR(50),
          credit_hours DECIMAL(3,1),
          is_published BOOLEAN DEFAULT 0,
          view_count INTEGER DEFAULT 0,
          rating_avg DECIMAL(3,2) DEFAULT 0,
          rating_count INTEGER DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
          FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Lesson completion tracking
      db.run(`
        CREATE TABLE IF NOT EXISTS lesson_progress (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          lesson_id INTEGER NOT NULL,
          is_completed BOOLEAN DEFAULT 0,
          progress_percentage INTEGER DEFAULT 0,
          time_spent INTEGER DEFAULT 0,
          rating INTEGER,
          review TEXT,
          completed_at DATETIME,
          started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
          UNIQUE(user_id, lesson_id)
        )
      `);

      // Research publications
      db.run(`
        CREATE TABLE IF NOT EXISTS research_papers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          topic_id INTEGER,
          title VARCHAR(255) NOT NULL,
          abstract TEXT,
          content TEXT NOT NULL,
          is_ai_content BOOLEAN DEFAULT 0,
          ai_label VARCHAR(50),
          collaborators TEXT,
          seeking_collaborators BOOLEAN DEFAULT 0,
          status VARCHAR(20) DEFAULT 'draft',
          view_count INTEGER DEFAULT 0,
          citation_count INTEGER DEFAULT 0,
          published_at DATETIME,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
      `);

      // Badges/Achievements
      db.run(`
        CREATE TABLE IF NOT EXISTS badges (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name VARCHAR(100) NOT NULL,
          description TEXT,
          icon_url VARCHAR(255),
          price INTEGER DEFAULT 0,
          rarity VARCHAR(20) DEFAULT 'common',
          category VARCHAR(50),
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);

      // User badges
      db.run(`
        CREATE TABLE IF NOT EXISTS user_badges (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          badge_id INTEGER NOT NULL,
          is_displayed BOOLEAN DEFAULT 1,
          earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
          UNIQUE(user_id, badge_id)
        )
      `);

      // Rewards (purchasable items)
      db.run(`
        CREATE TABLE IF NOT EXISTS rewards (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name VARCHAR(100) NOT NULL,
          description TEXT,
          type VARCHAR(20),
          image_url VARCHAR(255),
          price INTEGER NOT NULL,
          is_active BOOLEAN DEFAULT 1,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);

      // User purchased rewards
      db.run(`
        CREATE TABLE IF NOT EXISTS user_rewards (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          reward_id INTEGER NOT NULL,
          purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (reward_id) REFERENCES rewards(id) ON DELETE CASCADE
        )
      `);

      // Teacher applications
      db.run(`
        CREATE TABLE IF NOT EXISTS teacher_applications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          qualifications TEXT NOT NULL,
          experience TEXT NOT NULL,
          subject_areas TEXT NOT NULL,
          status VARCHAR(20) DEFAULT 'pending',
          admin_notes TEXT,
          submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          reviewed_at DATETIME,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Contact submissions
      db.run(`
        CREATE TABLE IF NOT EXISTS contact_submissions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name VARCHAR(100) NOT NULL,
          email VARCHAR(100) NOT NULL,
          subject VARCHAR(255) NOT NULL,
          message TEXT NOT NULL,
          status VARCHAR(20) DEFAULT 'new',
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);

      // Study groups
      db.run(`
        CREATE TABLE IF NOT EXISTS study_groups (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          topic_id INTEGER NOT NULL,
          creator_id INTEGER NOT NULL,
          name VARCHAR(100) NOT NULL,
          description TEXT,
          is_private BOOLEAN DEFAULT 0,
          max_members INTEGER,
          member_count INTEGER DEFAULT 1,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
          FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Study group members
      db.run(`
        CREATE TABLE IF NOT EXISTS study_group_members (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          group_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL,
          role VARCHAR(20) DEFAULT 'member',
          joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (group_id) REFERENCES study_groups(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          UNIQUE(group_id, user_id)
        )
      `);

      // Notifications
      db.run(`
        CREATE TABLE IF NOT EXISTS notifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          type VARCHAR(50) NOT NULL,
          title VARCHAR(255) NOT NULL,
          message TEXT,
          link VARCHAR(255),
          is_read BOOLEAN DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // User votes tracking (for posts and comments)
      db.run(`
        CREATE TABLE IF NOT EXISTS votes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          target_type VARCHAR(20) NOT NULL,
          target_id INTEGER NOT NULL,
          vote_type VARCHAR(10) NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          UNIQUE(user_id, target_type, target_id)
        )
      `, (err) => {
        if (err) {
          console.error('Error creating tables:', err);
          reject(err);
        } else {
          console.log('All tables created successfully');
          insertSampleData();
        }
      });
    });

    // Insert sample data
    function insertSampleData() {
      db.serialize(() => {
        // Sample topics
        const topics = [
          ['Programming', 'Learn programming languages and software development', 'Technology', '/icons/programming.png', '#4CAF50'],
          ['Mathematics', 'From basic math to advanced calculus', 'STEM', '/icons/math.png', '#2196F3'],
          ['Languages', 'Learn new languages and improve communication', 'Language', '/icons/languages.png', '#FF9800'],
          ['Science', 'Physics, Chemistry, Biology and more', 'STEM', '/icons/science.png', '#9C27B0'],
          ['Art & Design', 'Creative skills and artistic expression', 'Creative', '/icons/art.png', '#E91E63'],
          ['Music', 'Music theory, instruments, and production', 'Creative', '/icons/music.png', '#F44336'],
          ['Business', 'Entrepreneurship, management, and marketing', 'Business', '/icons/business.png', '#009688'],
          ['History', 'World history and historical analysis', 'Humanities', '/icons/history.png', '#795548']
        ];

        const insertTopic = db.prepare('INSERT INTO topics (name, description, category, icon_url, color) VALUES (?, ?, ?, ?, ?)');
        topics.forEach(topic => insertTopic.run(topic));
        insertTopic.finalize();

        // Sample badges
        const badges = [
          ['Early Adopter', 'Joined the platform in its early days', '/badges/early.png', 100, 'legendary', 'special'],
          ['First Post', 'Created your first forum post', '/badges/firstpost.png', 0, 'common', 'milestone'],
          ['Knowledge Seeker', 'Completed 10 lessons', '/badges/seeker.png', 50, 'rare', 'achievement'],
          ['Master Teacher', 'Taught 100 students', '/badges/master.png', 500, 'epic', 'achievement'],
          ['Research Pioneer', 'Published your first research paper', '/badges/research.png', 200, 'rare', 'achievement'],
          ['Community Helper', 'Received 100 upvotes', '/badges/helper.png', 150, 'rare', 'social'],
          ['Streak Master', '30-day learning streak', '/badges/streak.png', 300, 'epic', 'achievement']
        ];

        const insertBadge = db.prepare('INSERT INTO badges (name, description, icon_url, price, rarity, category) VALUES (?, ?, ?, ?, ?, ?)');
        badges.forEach(badge => insertBadge.run(badge));
        insertBadge.finalize();

        // Sample rewards (emojis, images, etc.)
        const rewards = [
          ['Fire Emoji', 'Show your passion with a fire emoji', 'emoji', '🔥', 10, 1],
          ['Star Emoji', 'Highlight with a star', 'emoji', '⭐', 10, 1],
          ['Trophy Emoji', 'Celebrate achievements', 'emoji', '🏆', 15, 1],
          ['Brain Emoji', 'Show your intelligence', 'emoji', '🧠', 10, 1],
          ['Rocket Emoji', 'Blast off to success', 'emoji', '🚀', 15, 1],
          ['Custom Border: Gold', 'Golden profile border', 'border', '/borders/gold.png', 100, 1],
          ['Custom Border: Rainbow', 'Rainbow profile border', 'border', '/borders/rainbow.png', 150, 1],
          ['Animated Avatar Frame', 'Animated frame for your avatar', 'frame', '/frames/animated.gif', 200, 1]
        ];

        const insertReward = db.prepare('INSERT INTO rewards (name, description, type, image_url, price, is_active) VALUES (?, ?, ?, ?, ?, ?)');
        rewards.forEach(reward => insertReward.run(reward));
        insertReward.finalize(() => {
          console.log('Sample data inserted successfully');
          resolve();
        });
      });
    }
  });
};

// Run initialization
initDatabase()
  .then(() => {
    console.log('Database initialization completed');
    process.exit(0);
  })
  .catch(err => {
    console.error('Database initialization failed:', err);
    process.exit(1);
  });
