# VocabSlayer openGauss 数据库部署完整说明

> **文档生成时间**: 2025-10-26
> **服务器系统**: openEuler Linux
> **数据库**: openGauss (端口 5432)
> **项目路径**: `/home/openEuler/openGauss/VocabSlayer_update`

---

## 📋 目录

1. [已完成的工作总结](#已完成的工作总结)
2. [服务器端还需要做的事情](#服务器端还需要做的事情)
3. [数据库结构详解](#数据库结构详解)
4. [客户端需要修改的内容](#客户端需要修改的内容)
5. [远程连接配置指南](#远程连接配置指南)
6. [常用数据库操作命令](#常用数据库操作命令)

---

## ✅ 已完成的工作总结

### 1. 数据库初始化 ✅

- **数据库名称**: `vocabulary_db`
- **字符编码**: UTF-8
- **状态**: 已创建并初始化

### 2. 数据库表结构 ✅

已创建 8 张核心表：

| 表名 | 用途 | 记录数 |
|-----|------|--------|
| `vocabulary` | 词汇库（全局共享） | 606 条 |
| `users` | 用户信息 | 5 个用户 |
| `user_learning_records` | 用户学习记录 | 18 条 |
| `user_review_list` | 用户复习本 | 4 条 |
| `user_bookmarks` | 用户收藏本 | 1 条 |
| `user_daily_stats` | 用户每日统计 | 1 条 |
| `user_config` | 用户配置 | 0 条 |
| `answer_history` | 答题历史记录 | 0 条 |

### 3. 数据迁移 ✅

**词汇数据迁移**:
- 从 `server/data.xlsx` 成功导入 **606 条词汇**
- 包含中文、英文、日文三种语言
- 按难度分级：Level 1 (114条)、Level 2 (194条)、Level 3 (298条)

**用户数据迁移**:
- 成功迁移 5 个用户：`tiamzhaoyi`, `tianhzhaoyi`, `tianzhaoyi111`, `tianzhaoyi1`, `tianzhaoyi`
- 主要用户 `tianzhaoyi` 数据完整：18条学习记录、4条复习单词、1条收藏、平均正确率50%

### 4. 代码适配 ✅

**修复文件**: `server/database_manager.py`
- ✅ 修复 openGauss 不支持 `ON CONFLICT` 语法的问题
- ✅ 改用 "先检查后插入/更新" 的兼容性方案
- ✅ 所有数据库操作测试通过（读取、写入、更新）

**配置文件**: `config.json`
```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "localhost",
    "port": 5432,
    "database": "vocabulary_db",
    "user": "openEuler",
    "password": "Qq13896842746"
  }
}
```

### 5. 测试验证 ✅

已通过的测试：
- ✅ 数据库连接
- ✅ 词汇查询（全部/按等级）
- ✅ 用户数据查询（学习记录、复习本、收藏本、每日统计）
- ✅ 数据写入和更新
- ✅ 事务提交

---

## 🔧 服务器端还需要做的事情

### 1. 配置 openGauss 允许远程连接 ⚠️ **重要**

当前 openGauss 只监听本地连接（127.0.0.1），需要配置允许远程 IP 访问。

#### 步骤 1: 修改 `postgresql.conf`

找到 openGauss 配置文件：
```bash
# 配置文件路径（根据实际情况调整）
cd /home/openEuler/openGauss/data/single_node

# 备份原配置
cp postgresql.conf postgresql.conf.backup

# 编辑配置文件
vi postgresql.conf
```

找到并修改以下配置：
```conf
# 监听所有 IP 地址（原来是 localhost）
listen_addresses = '*'

# 端口（默认已经是 5432）
port = 5432

# 最大连接数（可选，根据需要调整）
max_connections = 200
```

#### 步骤 2: 修改 `pg_hba.conf` 配置访问权限

编辑同目录下的 `pg_hba.conf`：
```bash
vi pg_hba.conf
```

在文件末尾添加（允许所有 IP 通过密码认证访问）：
```conf
# 允许所有 IPv4 地址访问
host    all             all             0.0.0.0/0               md5

# 或者只允许特定网段访问（更安全，例如 192.168.1.0/24）
host    all             all             192.168.1.0/24          md5
```

**重启 openGauss 使配置生效**:
```bash
# 停止数据库
gs_ctl stop -D /home/openEuler/openGauss/data/single_node

# 启动数据库
gs_ctl start -D /home/openEuler/openGauss/data/single_node
```

#### 步骤 3: 配置防火墙开放 5432 端口

```bash
# 如果使用 firewalld
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload

# 如果使用 iptables
sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT
sudo service iptables save

# 验证端口是否开放
sudo netstat -tlnp | grep 5432
```

预期输出应该看到：
```
tcp  0.0.0.0:5432  0.0.0.0:*  LISTEN  xxxxx/gaussdb
```

### 2. 创建远程访问专用用户（可选，推荐）

为了安全，建议创建一个专门用于远程访问的数据库用户：

```bash
gsql -d vocabulary_db -p 5432
```

在 gsql 中执行：
```sql
-- 创建新用户
CREATE USER vocabuser WITH PASSWORD 'YourSecurePassword123!';

-- 授予权限
GRANT CONNECT ON DATABASE vocabulary_db TO vocabuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vocabuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vocabuser;

-- 验证用户
\du
```

然后在远程客户端的 `config.json` 中使用：
```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "服务器IP",
    "port": 5432,
    "database": "vocabulary_db",
    "user": "vocabuser",
    "password": "YourSecurePassword123!"
  }
}
```

### 3. 设置数据库备份（推荐）

```bash
# 创建备份脚本
cat > /home/openEuler/backup_vocabulary.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/openEuler/db_backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

gs_dump -h localhost -p 5432 -U openEuler vocabulary_db \
  -f $BACKUP_DIR/vocabulary_db_$DATE.sql

# 只保留最近 7 天的备份
find $BACKUP_DIR -name "vocabulary_db_*.sql" -mtime +7 -delete

echo "备份完成: vocabulary_db_$DATE.sql"
EOF

# 添加执行权限
chmod +x /home/openEuler/backup_vocabulary.sh

# 设置定时任务（每天凌晨 2 点备份）
crontab -e
# 添加：
0 2 * * * /home/openEuler/backup_vocabulary.sh >> /home/openEuler/backup.log 2>&1
```

### 4. 性能优化（可选）

根据实际使用情况调整 `postgresql.conf`：
```conf
# 共享内存（建议为系统内存的 25%）
shared_buffers = 1GB

# 有效缓存大小（建议为系统内存的 50%）
effective_cache_size = 2GB

# 工作内存
work_mem = 16MB

# 维护工作内存
maintenance_work_mem = 256MB
```

---

## 📊 数据库结构详解

### ER 关系图

```
┌─────────────┐
│   users     │ (用户表)
│ - user_id   │ PK
│ - username  │ UNIQUE
│ - password  │
└──────┬──────┘
       │ 1:N
       ├──────────────────────┬──────────────────────┬──────────────────┐
       │                      │                      │                  │
       ▼                      ▼                      ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│user_learning │   │user_review   │   │user_bookmarks│   │user_daily    │
│  _records    │   │   _list      │   │              │   │   _stats     │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────────────┘
       │ N:1              │ N:1              │ N:1
       └──────────────────┴──────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │ vocabulary   │ (词汇表)
                  │ - vocab_id   │ PK
                  │ - english    │
                  │ - chinese    │
                  │ - japanese   │
                  │ - level      │
                  └──────────────┘
```

### 核心表结构详解

#### 1. users 表
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### 2. vocabulary 表
```sql
CREATE TABLE vocabulary (
    vocab_id SERIAL PRIMARY KEY,
    english VARCHAR(200),
    chinese VARCHAR(200),
    japanese VARCHAR(200),
    level INTEGER CHECK (level >= 1 AND level <= 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. user_learning_records 表
```sql
CREATE TABLE user_learning_records (
    record_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    star INTEGER DEFAULT 0 CHECK (star >= 0 AND star <= 3),
    last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    UNIQUE(user_id, vocab_id)
);
```

#### 4. user_review_list 表（复习本）
```sql
CREATE TABLE user_review_list (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    weight DECIMAL(10, 2) DEFAULT 10.0,  -- 权重越高越需要复习
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP,
    UNIQUE(user_id, vocab_id)
);
```

#### 5. user_bookmarks 表（收藏本）
```sql
CREATE TABLE user_bookmarks (
    bookmark_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id INTEGER REFERENCES vocabulary(vocab_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    UNIQUE(user_id, vocab_id)
);
```

#### 6. user_daily_stats 表（每日统计）
```sql
CREATE TABLE user_daily_stats (
    stat_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    wrong_answers INTEGER DEFAULT 0,
    accuracy DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_questions > 0
        THEN (correct_answers::DECIMAL / total_questions * 100)
        ELSE 0 END
    ) STORED,
    UNIQUE(user_id, date)
);
```

### 索引说明

```sql
-- 用户名索引（提高登录查询速度）
CREATE INDEX idx_users_username ON users(username);

-- 词汇等级索引（提高按难度筛选速度）
CREATE INDEX idx_vocabulary_level ON vocabulary(level);

-- 学习记录索引
CREATE INDEX idx_learning_records_user ON user_learning_records(user_id);
CREATE INDEX idx_learning_records_vocab ON user_learning_records(vocab_id);

-- 复习本权重索引（用于排序）
CREATE INDEX idx_review_list_weight ON user_review_list(weight DESC);

-- 每日统计日期索引
CREATE INDEX idx_daily_stats_user_date ON user_daily_stats(user_id, date DESC);
```

---

## 💻 客户端需要修改的内容

### 文件清单

需要在客户端设备上修改以下文件：

#### 1. `config.json` ⚠️ **必须修改**

将服务器 IP 地址替换为实际的服务器 IP：

```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "服务器的实际IP地址",  // 例如: "192.168.1.100"
    "port": 5432,
    "database": "vocabulary_db",
    "user": "openEuler",  // 或使用新创建的 vocabuser
    "password": "Qq13896842746"  // 对应的密码
  }
}
```

#### 2. `server/database_manager.py` ⚠️ **必须同步**

需要将服务器上修复后的版本同步到客户端，主要修改点：

- 移除了所有 `ON CONFLICT` 语法
- 改用 "先检查后插入/更新" 的兼容方案
- 涉及方法：
  - `update_user_record()`
  - `add_to_review_list()`
  - `add_bookmark()`
  - `update_daily_stats()`

**建议直接从服务器复制整个文件**：
```bash
# 在服务器上
scp /home/openEuler/openGauss/VocabSlayer_update/server/database_manager.py \
    用户@客户端IP:/path/to/VocabSlayer_update/server/
```

#### 3. 客户端依赖安装

确保客户端已安装：
```bash
pip install psycopg2-binary pandas openpyxl
```

#### 4. 测试连接脚本

在客户端运行测试（可选）：
```bash
python server/test_db_connection.py
```

### 客户端应用代码修改（如果有）

如果客户端代码中有硬编码的数据库配置，需要统一使用 `DatabaseFactory.from_config_file()` 方式：

```python
# 旧代码（不推荐）
db = ExcelDatabase()

# 新代码（推荐）
from server.database_manager import DatabaseFactory
db = DatabaseFactory.from_config_file('config.json')
```

---

## 🌐 远程连接配置指南

### 服务器端配置（必须完成）

#### 1. 获取服务器 IP 地址
```bash
# 查看本机 IP
ip addr show
# 或
ifconfig
```

找到类似 `192.168.x.x` 或公网 IP 的地址。

#### 2. 修改 openGauss 配置

**文件位置**: `/home/openEuler/openGauss/data/single_node/postgresql.conf`

```bash
# 编辑配置
vi /home/openEuler/openGauss/data/single_node/postgresql.conf

# 修改以下行：
listen_addresses = '*'
port = 5432
```

**文件位置**: `/home/openEuler/openGauss/data/single_node/pg_hba.conf`

```bash
# 编辑配置
vi /home/openEuler/openGauss/data/single_node/pg_hba.conf

# 在文件末尾添加：
host    vocabulary_db    openEuler    0.0.0.0/0    md5
# 或限制特定网段：
host    vocabulary_db    openEuler    192.168.1.0/24    md5
```

#### 3. 重启 openGauss
```bash
gs_ctl restart -D /home/openEuler/openGauss/data/single_node
```

#### 4. 验证监听状态
```bash
netstat -tlnp | grep 5432
```

应该看到：
```
tcp  0.0.0.0:5432  0.0.0.0:*  LISTEN
```

#### 5. 开放防火墙
```bash
# firewalld
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -I INPUT -p tcp --dport 5432 -j ACCEPT
sudo service iptables save
```

### 客户端配置

#### 1. 测试网络连通性
```bash
# 测试能否 ping 通服务器
ping 服务器IP

# 测试端口是否可达
telnet 服务器IP 5432
# 或
nc -zv 服务器IP 5432
```


#### 3. 测试连接
```python
python3 server/test_db_connection.py
```

### 常见问题排查

#### 问题 1: Connection refused
```
解决：检查服务器 openGauss 是否启动
gs_ctl status -D /home/openEuler/openGauss/data/single_node
```

#### 问题 2: Connection timed out
```
解决：检查防火墙是否开放 5432 端口
sudo firewall-cmd --list-ports
```

#### 问题 3: Authentication failed
```
解决：检查 pg_hba.conf 配置，确保有 md5 认证行
cat /home/openEuler/openGauss/data/single_node/pg_hba.conf | grep md5
```

#### 问题 4: no pg_hba.conf entry
```
解决：在 pg_hba.conf 中添加客户端 IP 的访问规则
host    vocabulary_db    openEuler    客户端IP/32    md5
```

---

## 🛠️ 常用数据库操作命令

### 基本操作

```bash
# 连接数据库
gsql -d vocabulary_db -p 5432

# 查看所有表
\dt

# 查看表结构
\d 表名

# 查看所有用户
\du

# 查看当前数据库
\c

# 退出
\q
```

### 数据查询

```sql
-- 查看词汇总数
SELECT COUNT(*) FROM vocabulary;

-- 查看各等级词汇数量
SELECT level, COUNT(*) as count
FROM vocabulary
GROUP BY level
ORDER BY level;

-- 查看所有用户及其学习情况
SELECT * FROM user_learning_overview;

-- 查看某用户的学习记录
SELECT v.english, v.chinese, lr.star, lr.last_reviewed
FROM user_learning_records lr
JOIN vocabulary v ON lr.vocab_id = v.vocab_id
JOIN users u ON lr.user_id = u.user_id
WHERE u.username = 'tianzhaoyi'
ORDER BY lr.last_reviewed DESC;

-- 查看某用户的复习本（按权重排序）
SELECT v.english, v.chinese, rl.weight
FROM user_review_list rl
JOIN vocabulary v ON rl.vocab_id = v.vocab_id
JOIN users u ON rl.user_id = u.user_id
WHERE u.username = 'tianzhaoyi'
ORDER BY rl.weight DESC;

-- 查看某用户的每日统计
SELECT date, total_questions, correct_answers, wrong_answers, accuracy
FROM user_daily_stats ds
JOIN users u ON ds.user_id = u.user_id
WHERE u.username = 'tianzhaoyi'
ORDER BY date DESC;
```

### 用户管理

```sql
-- 创建新用户
CREATE USER newuser WITH PASSWORD 'password123';

-- 授予权限
GRANT CONNECT ON DATABASE vocabulary_db TO newuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO newuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO newuser;

-- 修改用户密码
ALTER USER openEuler WITH PASSWORD 'newpassword';

-- 删除用户
DROP USER newuser;
```

### 数据备份与恢复

```bash
# 备份整个数据库
gs_dump -h localhost -p 5432 -U openEuler vocabulary_db > backup.sql

# 只备份数据（不含表结构）
gs_dump -h localhost -p 5432 -U openEuler --data-only vocabulary_db > data.sql

# 只备份表结构
gs_dump -h localhost -p 5432 -U openEuler --schema-only vocabulary_db > schema.sql

# 恢复数据库
gsql -d vocabulary_db -p 5432 -U openEuler -f backup.sql
```

### 性能监控

```sql
-- 查看数据库大小
SELECT pg_size_pretty(pg_database_size('vocabulary_db'));

-- 查看表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 查看当前连接
SELECT * FROM pg_stat_activity WHERE datname = 'vocabulary_db';

-- 查看慢查询（假设超过 1 秒）
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;
```

---

## 📝 快速参考

### 服务器信息

- **数据库名**: `vocabulary_db`
- **端口**: `5432`
- **用户名**: `openEuler`
- **密码**: `Qq13896842746`
- **数据路径**: `/home/openEuler/openGauss/data/single_node`

### 关键文件位置

```
/home/openEuler/openGauss/VocabSlayer_update/
├── config.json                          # 数据库配置
├── server/
│   ├── database_manager.py             # 数据库管理器（已修复）
│   ├── init_database.sql               # 数据库初始化脚本
│   ├── migrate_opengauss.py            # 数据迁移脚本
│   └── test_db_connection.py           # 连接测试脚本
└── user/                                # 用户数据目录（已迁移到数据库）

/home/openEuler/openGauss/data/single_node/
├── postgresql.conf                      # 主配置文件
└── pg_hba.conf                          # 访问控制配置
```

### 重要命令速查

```bash
# 启动数据库
gs_ctl start -D /home/openEuler/openGauss/data/single_node

# 停止数据库
gs_ctl stop -D /home/openEuler/openGauss/data/single_node

# 重启数据库
gs_ctl restart -D /home/openEuler/openGauss/data/single_node

# 查看数据库状态
gs_ctl status -D /home/openEuler/openGauss/data/single_node

# 连接数据库
gsql -d vocabulary_db -p 5432

# 备份数据库
gs_dump -h localhost -p 5432 -U openEuler vocabulary_db > backup_$(date +%Y%m%d).sql

# 测试 Python 连接
python3 server/test_db_connection.py
```

---

## 🎯 下一步行动清单



- [ ] 修改 `config.json` - 填写服务器 IP 和密码
- [ ] 测试网络连通性：`ping 服务器IP` 和 `telnet 服务器IP 5432`
- [ ] 运行连接测试：`python server/test_db_connection.py`
- [ ] 修改应用代码使用数据库（如果需要）
- [ ] 测试完整功能：登录、做题、查看统计

---

## 📞 技术支持

如遇到问题，按以下顺序排查：

1. **检查网络连通性** - ping、telnet
2. **检查数据库服务** - `gs_ctl status`
3. **检查配置文件** - postgresql.conf, pg_hba.conf
4. **检查防火墙** - firewall-cmd --list-ports
5. **查看数据库日志** - `/home/openEuler/openGauss/data/single_node/pg_log/`

---

**文档结束** 🎉

祝部署顺利！有任何问题随时联系。
