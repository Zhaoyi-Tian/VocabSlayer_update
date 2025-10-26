-- openGauss 数据库初始化脚本
-- 创建词汇学习系统所需的所有表

-- ========================================
-- 1. 创建用户表
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 为用户名创建索引，提高查询速度
CREATE INDEX idx_users_username ON users(username);

-- ========================================
-- 2. 创建词汇表（全局共享）
-- ========================================
CREATE TABLE IF NOT EXISTS vocabulary (
    vocab_id SERIAL PRIMARY KEY,
    english VARCHAR(200),
    chinese VARCHAR(200),
    japanese VARCHAR(200),
    level INTEGER CHECK (level >= 1 AND level <= 3),  -- 难度等级 1-3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为等级创建索引，方便按难度筛选
CREATE INDEX idx_vocabulary_level ON vocabulary(level);

-- ========================================
-- 3. 创建用户学习记录表
-- ========================================
CREATE TABLE IF NOT EXISTS user_learning_records (
    record_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER NOT NULL REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    star INTEGER DEFAULT 0 CHECK (star >= 0 AND star <= 3),  -- 掌握程度 0-3 星
    last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_count INTEGER DEFAULT 0,  -- 复习次数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, vocab_id)  -- 每个用户对每个单词只有一条记录
);

-- 为用户ID创建索引
CREATE INDEX idx_learning_records_user ON user_learning_records(user_id);
-- 为单词ID创建索引
CREATE INDEX idx_learning_records_vocab ON user_learning_records(vocab_id);
-- 为复合查询创建索引
CREATE INDEX idx_learning_records_user_vocab ON user_learning_records(user_id, vocab_id);

-- ========================================
-- 4. 创建用户复习本表
-- ========================================
CREATE TABLE IF NOT EXISTS user_review_list (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER NOT NULL REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    weight DECIMAL(10, 2) DEFAULT 10.0,  -- 复习权重，越高越需要复习
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP,
    UNIQUE(user_id, vocab_id)
);

-- 为用户ID创建索引
CREATE INDEX idx_review_list_user ON user_review_list(user_id);
-- 为权重创建索引，方便按权重排序
CREATE INDEX idx_review_list_weight ON user_review_list(weight DESC);

-- ========================================
-- 5. 创建用户收藏本表
-- ========================================
CREATE TABLE IF NOT EXISTS user_bookmarks (
    bookmark_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER NOT NULL REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note TEXT,  -- 用户备注
    UNIQUE(user_id, vocab_id)
);

-- 为用户ID创建索引
CREATE INDEX idx_bookmarks_user ON user_bookmarks(user_id);

-- ========================================
-- 6. 创建用户每日统计表
-- ========================================
CREATE TABLE IF NOT EXISTS user_daily_stats (
    stat_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    wrong_answers INTEGER DEFAULT 0,
    accuracy DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE
            WHEN total_questions > 0 THEN (correct_answers::DECIMAL / total_questions * 100)
            ELSE 0
        END
    ) STORED,  -- 自动计算正确率
    study_duration INTEGER DEFAULT 0,  -- 学习时长（秒）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- 为用户ID和日期创建索引
CREATE INDEX idx_daily_stats_user_date ON user_daily_stats(user_id, date DESC);

-- ========================================
-- 7. 创建用户配置表
-- ========================================
CREATE TABLE IF NOT EXISTS user_config (
    config_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE UNIQUE,
    primary_color VARCHAR(20),
    api_key VARCHAR(255),
    theme VARCHAR(20) DEFAULT 'light',  -- light/dark
    main_language VARCHAR(20) DEFAULT 'Chinese',
    study_language VARCHAR(20) DEFAULT 'English',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 8. 创建答题历史表（可选，用于详细分析）
-- ========================================
CREATE TABLE IF NOT EXISTS answer_history (
    history_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER NOT NULL REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    question_type VARCHAR(20),  -- 'translation_to_target', 'translation_to_main', 'judge'
    is_correct BOOLEAN NOT NULL,
    time_spent INTEGER,  -- 答题耗时（秒）
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为用户ID和时间创建索引
CREATE INDEX idx_answer_history_user_time ON answer_history(user_id, answered_at DESC);

-- ========================================
-- 插入示例数据
-- ========================================

-- 插入测试用户
INSERT INTO users (username, password) VALUES
    ('admin', 'admin123'),  -- 注意：实际使用时应该加密密码
    ('test_user', 'test123')
ON CONFLICT (username) DO NOTHING;

-- 插入示例词汇（可选）
INSERT INTO vocabulary (english, chinese, japanese, level) VALUES
    ('hello', '你好', 'こんにちは', 1),
    ('world', '世界', '世界', 1),
    ('computer', '电脑', 'コンピュータ', 2),
    ('programming', '编程', 'プログラミング', 3)
ON CONFLICT DO NOTHING;

-- ========================================
-- 创建视图（方便查询）
-- ========================================

-- 用户学习概况视图
CREATE OR REPLACE VIEW user_learning_overview AS
SELECT
    u.username,
    COUNT(DISTINCT lr.vocab_id) as words_learned,
    COUNT(DISTINCT rl.vocab_id) as words_to_review,
    COUNT(DISTINCT b.vocab_id) as words_bookmarked,
    AVG(ds.accuracy) as avg_accuracy,
    SUM(ds.total_questions) as total_questions_answered
FROM users u
LEFT JOIN user_learning_records lr ON u.user_id = lr.user_id
LEFT JOIN user_review_list rl ON u.user_id = rl.user_id
LEFT JOIN user_bookmarks b ON u.user_id = b.user_id
LEFT JOIN user_daily_stats ds ON u.user_id = ds.user_id
GROUP BY u.username;

-- 词汇掌握情况视图
CREATE OR REPLACE VIEW vocabulary_mastery AS
SELECT
    v.vocab_id,
    v.english,
    v.chinese,
    v.japanese,
    v.level,
    COUNT(DISTINCT lr.user_id) as learned_by_users,
    AVG(lr.star) as avg_mastery_level
FROM vocabulary v
LEFT JOIN user_learning_records lr ON v.vocab_id = lr.vocab_id
GROUP BY v.vocab_id, v.english, v.chinese, v.japanese, v.level;

-- ========================================
-- 创建函数：自动更新用户配置时间戳
-- ========================================
CREATE OR REPLACE FUNCTION update_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_config_timestamp
BEFORE UPDATE ON user_config
FOR EACH ROW
EXECUTE FUNCTION update_config_timestamp();

-- ========================================
-- 授予权限（根据实际情况调整）
-- ========================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vocabulary_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vocabulary_app_user;

-- 完成提示
SELECT '数据库初始化完成！' as status;
