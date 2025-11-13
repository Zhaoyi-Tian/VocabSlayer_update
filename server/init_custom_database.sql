-- 自定义题库数据库表结构

-- 用户自定义题库表
CREATE TABLE user_custom_banks (
    bank_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    bank_name VARCHAR(200) NOT NULL,
    source_file VARCHAR(500),  -- 原始文件名
    description TEXT,
    question_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户自定义题目表
CREATE TABLE user_custom_questions (
    question_id SERIAL PRIMARY KEY,
    bank_id INTEGER REFERENCES user_custom_banks(bank_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'Q&A',  -- 题目类型：Q&A, Multiple Choice, etc.
    difficulty INTEGER DEFAULT 1 CHECK (difficulty >= 1 AND difficulty <= 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_generated BOOLEAN DEFAULT TRUE  -- 标记是否由用户生成或AI生成
);

-- 用户自定义题目答题记录表
CREATE TABLE user_custom_answers (
    answer_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES user_custom_questions(question_id) ON DELETE CASCADE,
    user_answer TEXT,
    is_correct BOOLEAN,
    answer_time INTEGER,  -- 答题用时（秒）
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为自定义题库表创建索引
CREATE INDEX idx_custom_banks_user ON user_custom_banks(user_id);
CREATE INDEX idx_custom_questions_bank ON user_custom_questions(bank_id);
CREATE INDEX idx_custom_answers_user ON user_custom_answers(user_id);
CREATE INDEX idx_custom_answers_question ON user_custom_answers(question_id);

-- 创建更新时间戳的触发器
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_custom_banks_updated_at
    BEFORE UPDATE ON user_custom_banks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();