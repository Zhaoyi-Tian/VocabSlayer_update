---
typora-root-url: ./images
---

# VocabSlayer：基于 openGauss 的智能化词汇学习系统

## 北京大学鲲鹏创新大赛项目报告

**作者**：田照亿，杜浩嘉，张霖泽，桂诗清

**版本**：v1.0

**日期**：2025-11-15

## 一、项目概述

VocabSlayer（万词斩）是一款基于华为 openGauss 数据库构建的智能化词汇学习系统，采用 PyQt5 开发桌面前端，Python Flask 提供后端 API 服务，集成 AI 智能助手与科学复习算法，打造高效、个性化的词汇学习体验。系统支持多用户并发访问，提供词汇学习、自定义题库、学习统计和排行榜等核心功能，充分发挥 openGauss 数据库的高性能与兼容性优势，为用户构建全方位的词汇学习生态。

![image-20251118223945159](/image-20251118223945159.png)

![image-20251118224130971](/image-20251118224130971.png)

![image-20251118224750158](/../../../image-20251118224750158.png)

![image-20251118224810739](/image-20251118224810739.png)

<img src="/image-20251118224829040-1763477504731-2.png" alt="image-20251118224829040" />

![image-20251118224843343](/image-20251118224843343.png)

![image-20251118224904848](/image-20251118224904848.png)

### 一、数据库表结构总览

| 模块分类       | 表名                  | 核心用途                                                     | 关键字段                                                     |
| -------------- | --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 用户管理模块   | users                 | 存储用户基础信息，实现用户身份认证                           | user_id（主键）、username、password、created_at、last_login  |
| 词汇学习模块   | vocabulary            | 存储 606 条核心词汇，含多语言释义和难度分级                  | vocab_id（主键）、english、chinese、japanese、level          |
| 词汇学习模块   | user_learning_records | 记录用户对每个词汇的学习情况（星级、复习次数等）             | record_id（主键）、user_id（外键）、vocab_id（外键）、star、review_count |
| 词汇学习模块   | user_review_list      | 基于艾宾浩斯遗忘曲线，存储用户词汇复习权重和下次复习时间     | review_id（主键）、user_id（外键）、vocab_id（外键）、weight、next_review_time |
| 自定义题库模块 | user_custom_banks     | 存储用户创建的自定义题库信息（名称、文件来源、题目数量等）   | bank_id（主键）、user_id、bank_name、source_file、question_count |
| 自定义题库模块 | user_custom_questions | 存储自定义题库下的具体题目（题干、答案、题型、置信度）       | question_id（主键）、bank_id（外键）、question_text、answer_text、question_type |
| 排行榜模块     | leaderboards          | 存储用户总分、准确率、每日 / 每周 / 每月分数，实现排行榜展示 | id（主键）、user_id、username、score、accuracy、daily_score/weekly_score/monthly_score |
| 排行榜模块     | score_records         | 记录用户每次答题的分数、正确率、耗时等明细                   | id（主键）、user_id、bank_id（外键）、question_count、correct_count、time_spent、score |
|                |                       |                                                              | achievement_name、unlocked_at                                |

### 二、索引优化策略表

| 索引关联模块 | 索引名称                  | 关联表名              | 索引字段            | 优化目标                                        |
| ------------ | ------------------------- | --------------------- | ------------------- | ----------------------------------------------- |
| 词汇学习模块 | idx_vocabulary_level      | vocabulary            | level               | 快速筛选指定难度等级的词汇                      |
| 词汇学习模块 | idx_learning_records_user | user_learning_records | user_id             | 快速查询单个用户的所有词汇学习记录              |
| 词汇学习模块 | idx_review_list_user      | user_review_list      | user_id             | 快速查询单个用户的词汇复习列表                  |
| 排行榜模块   | idx_leaderboards_score    | leaderboards          | score（降序）       | 快速排序获取总分排行榜                          |
| 排行榜模块   | idx_leaderboards_daily    | leaderboards          | daily_score（降序） | 快速排序获取每日分数排行榜                      |
| 排行榜模块   | idx_score_records_user    | score_records         | user_id             | 快速查询单个用户的所有分数记录                  |
| 排行榜模块   | idx_score_records_created | score_records         | created_at          | 快速按时间筛选用户分数记录（如今日 / 本周记录） |
| 用户管理模块 | idx_users_username        | users                 | username            | 快速通过用户名查询用户信息（登录 / 验证场景）   |

### 三、核心功能 - 模块 - 表关联表

| 核心功能方向         | 所属模块       | 依赖表名              | 功能实现逻辑简述                                             |
| -------------------- | -------------- | --------------------- | ------------------------------------------------------------ |
| 用户注册 / 登录      | 用户管理模块   | users                 | 注册时插入用户信息，登录时校验 username+password，更新 last_login |
| 词汇基础查询         | 词汇学习模块   | vocabulary            | 按 level / 关键词查询词汇，返回多语言释义                    |
| 词汇学习轨迹记录     | 词汇学习模块   | user_learning_records | 用户学习词汇后，更新 star、review_count、last_reviewed       |
| 智能复习提醒         | 词汇学习模块   | user_review_list      | 根据 weight 和 next_review_time，推送待复习词汇              |
| 自定义题库创建       | 自定义题库模块 | user_custom_banks     | 用户上传文件 / 手动创建题库，记录题库基本信息                |
| 自定义题目管理       | 自定义题库模块 | user_custom_questions | 向指定题库添加 / 编辑题目，更新 question_count               |
| 总分排行榜展示       | 排行榜模块     | leaderboards          | 按 score 降序排序，展示用户排名                              |
| 每日 / 周 / 月榜展示 | 排行榜模块     | leaderboards          | 按 daily_score/weekly_score/monthly_score 降序排序           |
| 答题分数统计         | 排行榜模块     | score_records         | 记录每次答题数据，计算正确率、得分，并同步更新 leaderboards  |
| 成就徽章解锁         | 排行榜模块     | achievements          | 达到指定条件（如总分达标、答题次数达标），解锁对应徽章       |

## 二、系统架构设计

### 2.1 整体架构

系统采用三层架构设计，实现前后端分离与数据存储解耦：

```plaintext
┌─────────────────────────────────────────────────────────────┐
│                    VocabSlayer 应用架构                       │
├─────────────────────┬───────────────────┬───────────────────┤
│   前端应用层        │   业务逻辑层       │   数据存储层       │
│                     │                   │                   │
│ PyQt5 GUI         │ Python Backend     │   openGauss       │
│ Fluent Design     │ Flask API Server   │   数据库          │
│ Windows/Linux     │ 业务处理模块       │                   │
│                     │                   │                   │
└─────────────────────┴───────────────────┴───────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   辅助服务组件       │
                    │  - Redis缓存        │
                    │  - 排行榜服务(C++)   │
                    │  - AI集成(DeepSeek)  │
                    └──────────────────────┘
```

- **前端应用层**：基于 PyQt5 与 Fluent Design 风格，实现桌面端交互界面，包含用户系统、学习模块、数据统计和排行榜等功能组件。
- **业务逻辑层**：通过 Flask 构建 RESTful API，处理核心业务逻辑，包括用户认证、学习记录管理、分数计算和题库管理。
- **数据存储层**：采用 openGauss 数据库存储用户数据、词汇库和学习记录，利用其 PostgreSQL 兼容性和企业级特性保证数据安全与性能。
- **辅助服务**：集成 Redis 缓存提升排行榜查询效率，C++ 服务实现高性能排名计算，DeepSeek AI 提供智能学习支持。

### 2.2 数据库连接设计

系统通过`py-opengauss`驱动实现与数据库的高效连接，配置如下：

```python
# 数据库连接配置
DB_CONFIG = {
    'host': '10.129.211.118',
    'port': 5432,
    'database': 'vocabulary_db',
    'user': 'vocabuser',
    'password': 'OpenEuler123!'
}

# 连接管理函数
import py_opengauss

def get_db_connection():
    conn = py_opengauss.connect(**DB_CONFIG)
    return conn
```

## 三、数据库设计

### 3.1 核心数据表结构

#### 用户管理模块

```sql
-- 用户基础信息表
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
CREATE INDEX idx_users_username ON users(username);
```

#### 词汇学习模块

```sql
-- 词汇主表（606条词汇数据）
CREATE TABLE vocabulary (
    vocab_id SERIAL PRIMARY KEY,
    english VARCHAR(200) NOT NULL,
    chinese VARCHAR(200) NOT NULL,
    japanese VARCHAR(200),
    level INTEGER CHECK (level >= 1 AND level <= 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习记录表
CREATE TABLE user_learning_records (
    record_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    star INTEGER CHECK (star >= 0 AND star <= 3),
    last_reviewed TIMESTAMP,
    review_count INTEGER DEFAULT 0
);

-- 复习权重表（基于艾宾浩斯遗忘曲线）
CREATE TABLE user_review_list (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    weight DECIMAL(5,2) DEFAULT 1.00,
    next_review_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 自定义题库模块

```sql
-- 自定义题库表
CREATE TABLE user_custom_banks (
    bank_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bank_name VARCHAR(255) NOT NULL,
    source_file VARCHAR(255) NOT NULL,
    description TEXT,
    question_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 自定义题目表
CREATE TABLE user_custom_questions (
    question_id SERIAL PRIMARY KEY,
    bank_id INTEGER REFERENCES user_custom_banks(bank_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.90
);
```

#### 排行榜模块

```sql
-- 排行榜主表
CREATE TABLE leaderboards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL,
    score BIGINT NOT NULL DEFAULT 0,
    accuracy DECIMAL(5,2) DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    daily_score BIGINT DEFAULT 0,
    weekly_score BIGINT DEFAULT 0,
    monthly_score BIGINT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分数记录表
CREATE TABLE score_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bank_id INTEGER REFERENCES user_custom_banks(bank_id),
    question_count INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    time_spent INTEGER NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 成就徽章表
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(100) NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_type)
);
```

### 3.2 索引优化策略

为提升查询性能，设计了以下索引：

```sql
-- 词汇学习相关索引
CREATE INDEX idx_vocabulary_level ON vocabulary(level);
CREATE INDEX idx_learning_records_user ON user_learning_records(user_id);
CREATE INDEX idx_review_list_user ON user_review_list(user_id);

-- 排行榜相关索引
CREATE INDEX idx_leaderboards_score ON leaderboards(score DESC);
CREATE INDEX idx_leaderboards_daily ON leaderboards(daily_score DESC);
CREATE INDEX idx_score_records_user ON score_records(user_id);
CREATE INDEX idx_score_records_created ON score_records(created_at);
```

## 四、核心功能实现

### 4.1 用户认证与管理

```python
# 用户认证实现
def authenticate_user(username, password):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        if result and check_password(result[1], password):  # 密码哈希验证
            return result[0]
        return None
    finally:
        conn.close()
```

用户系统支持注册、登录、信息配置等功能，保存用户学习偏好（如语言、难度等级），并通过加密存储保证密码安全。

### 4.2 词汇学习与复习系统

#### 学习记录管理

```python
def save_learning_record(user_id, vocab_id, star):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_learning_records
            (user_id, vocab_id, star, last_reviewed)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (user_id, vocab_id, star))
        conn.commit()
    finally:
        conn.close()
```

#### 智能复习机制

基于艾宾浩斯遗忘曲线，系统通过`user_review_list`表动态调整复习权重和间隔：

- 根据答题正确率调整词汇权重（0.5-2.0）
- 自动计算下次复习时间
- 优先推送高权重（易错）词汇

### 4.3 自定义题库系统

支持用户上传 PDF、DOCX 等格式文件生成自定义题库，核心 API 如下：

```python
# 题库查询API
@app.route('/api/banks/<int:user_id>')
def get_banks(user_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_custom_banks WHERE user_id = %s", (user_id,))
        banks = cur.fetchall()
        return jsonify({'success': True, 'banks': format_banks(banks)})
    finally:
        conn.close()
```

通过 SSE（Server-Sent Events）实现文件上传进度实时推送，提升用户体验。

### 4.4 排行榜功能

#### 多维度排名

支持日榜、周榜、总榜及官方 / 自定义题库分类排名，通过 Redis 缓存热门数据：

```plaintext
# Redis缓存结构
leaderboard:daily:2025-11-15 -> SortedSet (user_id:score)
leaderboard:weekly:2025-W46 -> SortedSet
leaderboard:global -> SortedSet
```

#### 分数计算规则

```plaintext
基础分数 = (正确数 / 总题数) × 100 × 难度系数 × 时间系数
难度系数：简单(1.0)、中等(1.5)、困难(2.0)、专家(3.0)
时间系数 = max(0.5, 1 - (用时 - 预期时间) / 预期时间 × 0.5)
```

#### 排行榜 API 示例

```python
# 个人排名查询接口
@app.route('/api/leaderboard/me/<user_id>')
def get_personal_rank(user_id):
    # 从缓存或数据库获取用户在各榜单中的排名
    return jsonify({
        "success": True,
        "data": {
            "user_rank": {"daily": 15, "weekly": 23, "all": 156},
            "score_stats": {"daily_score": 7500, "total_score": 580000}
        }
    })
```

### 4.5 AI 智能助手

集成 DeepSeek AI 提供词汇学习辅助功能：

- 词汇释义与例句生成
- 学习计划个性化推荐
- 基于 Markdown 的富文本交互
- 自定义 API 密钥配置

## 五、技术特色

1. **国产化数据库集成**：基于 openGauss 构建核心数据存储，利用其高性能、高兼容性特性，支持多用户并发访问。
2. **科学学习算法**：结合艾宾浩斯遗忘曲线设计复习机制，动态调整学习内容优先级，提升记忆效率。
3. **高性能排行榜**：通过 C++ 服务实现千万级用户排名计算，Redis 缓存降低数据库压力，保证实时性（更新延迟 < 1s）。
4. **跨平台桌面应用**：基于 PyQt5 开发，支持 Windows/Linux 系统，Fluent Design 风格提供现代化用户体验。
5. **全链路数据安全**：密码加密存储、数据校验机制、API 限流保护，防止恶意攻击与数据泄露。

## 六、部署与性能

### 6.1 部署流程

1. **数据库初始化**：

```bash
gsql -d vocabulary_db -U vocabuser -p 5432 -f init_database.sql
```

1. **依赖安装**：

```bash
pip install py-opengauss==1.3.10 PyQt5==5.15.11 flask requests
```

1. **服务启动**：

```bash
# 启动API服务器
python api_server.py

# 启动排行榜服务
./leaderboard_service
```

### 6.2 性能表现

- 词汇表规模：606 条核心词汇
- 并发支持：单服务器支持 100 + 用户同时在线
- 响应速度：数据库查询 < 10ms，排行榜查询 < 100ms
- 数据同步：学习记录实时保存，排行榜增量更新

## 七、总结与展望

VocabSlayer 系统成功实现了 openGauss 数据库在教育类应用中的深度集成，通过 "学 - 练 - 复习 - 竞技" 全流程设计，为用户提供高效词汇学习解决方案。项目展示了国产化数据库在性能、兼容性方面的优势，同时结合 AI 技术与科学学习方法，具备较高的实用价值。

未来将扩展以下功能：

- 好友排行榜与学习社群
- 机器学习驱动的个性化学习路径
- 分布式部署支持更大规模用户
- 多语言学习扩展（日语、韩语等）

## 八、团队信息

**作者**：田照亿，杜浩嘉，张霖泽，桂诗清

**项目定位**：基于 openGauss 的智能化词汇学习平台

**技术亮点**：国产化数据库集成、科学学习算法、高性能排行榜系统