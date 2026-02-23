-- WeTube 데이터베이스 스키마 (SQLite)
-- 모든 테이블 생성문

-- ============================================
-- 1. 사용자 테이블 (users)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(80) NULL,
    profile_image VARCHAR(255) NULL,
    profile_image_public_id VARCHAR(255) NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ============================================
-- 2. 태그 테이블 (tags)
-- ============================================
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 태그 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags (name);

-- ============================================
-- 3. 비디오 테이블 (videos)
-- ============================================
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    video_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500) NULL,
    category VARCHAR(50) NULL,
    duration INTEGER NULL,
    views INTEGER NOT NULL DEFAULT 0,
    likes INTEGER NOT NULL DEFAULT 0,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_public_id VARCHAR(255) NULL,
    thumbnail_public_id VARCHAR(255) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 비디오 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_videos_category ON videos (category);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos (created_at);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos (user_id);

-- ============================================
-- 4. 댓글 테이블 (comments)
-- ============================================
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    parent_id INTEGER NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    dislikes INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- 댓글 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments (created_at);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments (user_id);
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments (video_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments (parent_id);

-- ============================================
-- 5. 비디오 좋아요 중간 테이블 (video_likes)
-- ============================================
CREATE TABLE IF NOT EXISTS video_likes (
    user_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, video_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- ============================================
-- 6. 댓글 좋아요 중간 테이블 (comment_likes)
-- ============================================
CREATE TABLE IF NOT EXISTS comment_likes (
    user_id INTEGER NOT NULL,
    comment_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, comment_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- ============================================
-- 7. 댓글 싫어요 중간 테이블 (comment_dislikes)
-- ============================================
CREATE TABLE IF NOT EXISTS comment_dislikes (
    user_id INTEGER NOT NULL,
    comment_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, comment_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- ============================================
-- 8. 구독 중간 테이블 (subscriptions)
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    subscriber_id INTEGER NOT NULL,
    subscribed_to_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (subscriber_id, subscribed_to_id),
    FOREIGN KEY (subscriber_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscribed_to_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (subscriber_id != subscribed_to_id)  -- 자기 자신을 구독할 수 없음
);

-- ============================================
-- 9. 비디오 태그 중간 테이블 (video_tags)
-- ============================================
CREATE TABLE IF NOT EXISTS video_tags (
    video_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id, tag_id),
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
