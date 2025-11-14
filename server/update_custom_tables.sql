-- 更新自定义题库表结构
-- 添加新字段以支持文档处理功能

-- 更新 user_custom_banks 表
DO $$
BEGIN
    -- 添加 file_hash 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_banks' AND column_name='file_hash') THEN
        ALTER TABLE user_custom_banks ADD COLUMN file_hash VARCHAR(64);
        COMMENT ON COLUMN user_custom_banks.file_hash IS '文件MD5哈希值，用于检测重复上传';
    END IF;

    -- 添加 processing_status 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_banks' AND column_name='processing_status') THEN
        ALTER TABLE user_custom_banks ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending';
        COMMENT ON COLUMN user_custom_banks.processing_status IS '处理状态：pending/processing/completed/failed';
    END IF;

    -- 添加 processing_error 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_banks' AND column_name='processing_error') THEN
        ALTER TABLE user_custom_banks ADD COLUMN processing_error TEXT;
        COMMENT ON COLUMN user_custom_banks.processing_error IS '处理错误信息';
    END IF;

    -- 添加 total_chunks 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_banks' AND column_name='total_chunks') THEN
        ALTER TABLE user_custom_banks ADD COLUMN total_chunks INTEGER DEFAULT 0;
        COMMENT ON COLUMN user_custom_banks.total_chunks IS '文档分块总数';
    END IF;
END $$;

-- 更新 user_custom_questions 表
DO $$
BEGIN
    -- 添加 source_chunk_index 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_questions' AND column_name='source_chunk_index') THEN
        ALTER TABLE user_custom_questions ADD COLUMN source_chunk_index INTEGER;
        COMMENT ON COLUMN user_custom_questions.source_chunk_index IS '来源文本块索引';
    END IF;

    -- 添加 ai_generated 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_questions' AND column_name='ai_generated') THEN
        ALTER TABLE user_custom_questions ADD COLUMN ai_generated BOOLEAN DEFAULT TRUE;
        COMMENT ON COLUMN user_custom_questions.ai_generated IS '是否由AI生成';
    END IF;

    -- 添加 confidence_score 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_questions' AND column_name='confidence_score') THEN
        ALTER TABLE user_custom_questions ADD COLUMN confidence_score DECIMAL(3,2);
        COMMENT ON COLUMN user_custom_questions.confidence_score IS 'AI生成置信度分数(0-1)';
    END IF;
END $$;

-- 更新 user_custom_answers 表
DO $$
BEGIN
    -- 添加 answer_time 字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_custom_answers' AND column_name='answer_time') THEN
        ALTER TABLE user_custom_answers ADD COLUMN answer_time INTEGER DEFAULT 0;
        COMMENT ON COLUMN user_custom_answers.answer_time IS '答题时间（秒）';
    END IF;
END $$;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_custom_banks_file_hash ON user_custom_banks(file_hash);
CREATE INDEX IF NOT EXISTS idx_custom_banks_status ON user_custom_banks(processing_status);
CREATE INDEX IF NOT EXISTS idx_custom_questions_chunk_index ON user_custom_questions(source_chunk_index);
CREATE INDEX IF NOT EXISTS idx_custom_answers_question_id ON user_custom_answers(question_id);

-- 更新统计信息
ANALYZE user_custom_banks;
ANALYZE user_custom_questions;
ANALYZE user_custom_answers;