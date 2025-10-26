# openGauss 数据库迁移指南

## 📖 概述

本指南将帮助你将现有的 Excel 数据迁移到 openGauss 数据库，实现多用户数据隔离和更好的性能。

## 🎯 为什么要迁移到数据库？

- ✅ **多用户支持**: Excel 无法有效隔离不同用户的数据
- ✅ **性能提升**: 数据库查询比 Excel 快得多
- ✅ **数据安全**: 支持事务、备份、恢复
- ✅ **并发访问**: 多个用户同时使用不会产生冲突
- ✅ **可扩展性**: 轻松应对数据量增长

## 📋 前置准备

### 1. 安装 openGauss

#### 方式一：使用 Docker（推荐，最简单）

```bash
# 拉取镜像
docker pull enmotech/opengauss:latest

# 启动容器
docker run --name opengauss \
  -p 5432:5432 \
  -e GS_PASSWORD=YourPassword123! \
  -d enmotech/opengauss:latest

# 检查容器状态
docker ps
```

#### 方式二：本地安装

访问 [openGauss 官网](https://opengauss.org/zh/download/) 下载安装包并按照文档安装。

### 2. 安装 Python 依赖

```bash
# 安装数据库驱动
pip install psycopg2-binary

# 如果需要批量操作优化
pip install pandas openpyxl
```

### 3. 测试数据库连接

```bash
# 使用 Docker 进入容器
docker exec -it opengauss bash

# 连接数据库
gsql -d postgres -U gaussdb -W

# 输入密码后，如果看到 postgres=# 提示符，说明连接成功
```

## 🚀 迁移步骤

### 步骤 1: 初始化数据库

```bash
# 1. 创建数据库
docker exec -it opengauss gsql -d postgres -U gaussdb -c "CREATE DATABASE vocabulary_db;"

# 2. 执行初始化脚本
docker exec -i opengauss gsql -d vocabulary_db -U gaussdb < server/init_database.sql
```

或者手动执行：
```bash
# 进入容器
docker exec -it opengauss bash

# 连接到数据库
gsql -d vocabulary_db -U gaussdb -W

# 在 gsql 中执行
\i /path/to/init_database.sql
```

### 步骤 2: 配置数据库连接

复制配置文件模板：
```bash
cp config.json.example config.json
```

编辑 `config.json`：
```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "localhost",
    "port": 5432,
    "database": "vocabulary_db",
    "user": "gaussdb",
    "password": "YourPassword123!"
  }
}
```

### 步骤 3: 执行数据迁移

```bash
# 运行迁移工具
python server/migrate_to_database.py
```

按照提示输入：
- 数据库地址 (默认 localhost)
- 数据库端口 (默认 5432)
- 数据库名称 (默认 vocabulary_db)
- 数据库用户名 (gaussdb)
- 数据库密码
- 迁移用户名 (例如: your_username)

### 步骤 4: 验证数据迁移

```bash
# 进入数据库
docker exec -it opengauss gsql -d vocabulary_db -U gaussdb

# 检查数据
SELECT COUNT(*) FROM vocabulary;        -- 检查词汇数量
SELECT COUNT(*) FROM users;             -- 检查用户数量
SELECT * FROM user_learning_overview;  -- 查看用户学习概况
```

### 步骤 5: 切换应用到数据库模式

修改 `config.json`，将 `database_type` 改为 `opengauss`：

```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "localhost",
    "port": 5432,
    "database": "vocabulary_db",
    "user": "gaussdb",
    "password": "YourPassword123!"
  }
}
```

## 🔄 远程数据库连接（数据库在其他系统）

### 方式一：直接远程连接

修改 `config.json`：
```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "192.168.1.100",  // 远程服务器 IP
    "port": 5432,
    "database": "vocabulary_db",
    "user": "remote_user",
    "password": "remote_password"
  }
}
```

**注意**: 需要确保：
1. 远程服务器防火墙开放 5432 端口
2. openGauss 配置允许远程连接 (修改 `pg_hba.conf`)

### 方式二：SSH 隧道连接（更安全）

```bash
# 在本地建立 SSH 隧道
ssh -L 5432:localhost:5432 user@remote_server_ip

# 保持终端运行，在另一个终端运行应用
python client/main.py
```

配置文件使用本地端口：
```json
{
  "database_type": "opengauss",
  "database_config": {
    "host": "localhost",
    "port": 5432,
    "database": "vocabulary_db",
    "user": "gaussdb",
    "password": "password"
  }
}
```

### 方式三：使用 Python SSH 隧道

安装依赖：
```bash
pip install sshtunnel
```

在代码中使用（已在 `database_manager.py` 中实现）：
```python
from database_manager import DatabaseFactory

# 会自动处理 SSH 隧道
db = DatabaseFactory.from_config_file('config.json')
db.connect()
```

## 🔧 常用数据库操作

### 查看用户学习数据

```sql
-- 查看某个用户的学习进度
SELECT * FROM user_learning_overview WHERE username = 'your_username';

-- 查看用户复习本
SELECT v.english, v.chinese, r.weight
FROM user_review_list r
JOIN vocabulary v ON r.vocab_id = v.vocab_id
JOIN users u ON r.user_id = u.user_id
WHERE u.username = 'your_username'
ORDER BY r.weight DESC;

-- 查看用户每日统计
SELECT date, total_questions, accuracy
FROM user_daily_stats ds
JOIN users u ON ds.user_id = u.user_id
WHERE u.username = 'your_username'
ORDER BY date DESC
LIMIT 30;
```

### 备份数据

```bash
# 备份整个数据库
docker exec opengauss gs_dump -U gaussdb vocabulary_db > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i opengauss gsql -U gaussdb vocabulary_db < backup_20231201.sql
```

### 清理测试数据

```sql
-- 删除测试用户及其所有数据（级联删除）
DELETE FROM users WHERE username = 'test_user';

-- 清空某个表
TRUNCATE TABLE answer_history;
```

## 🐛 常见问题

### 1. 连接超时

**问题**: `could not connect to server: Connection timed out`

**解决**:
- 检查防火墙是否开放 5432 端口
- 检查 `pg_hba.conf` 是否允许远程连接
- 使用 SSH 隧道

### 2. 认证失败

**问题**: `FATAL: password authentication failed`

**解决**:
- 检查用户名和密码是否正确
- 检查 `pg_hba.conf` 中的认证方式
- 尝试重置密码

### 3. 权限不足

**问题**: `ERROR: permission denied for table xxx`

**解决**:
```sql
-- 授予用户权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

### 4. 迁移后数据不一致

**解决**:
```bash
# 重新运行迁移脚本
python server/migrate_to_database.py

# 或者手动检查
SELECT COUNT(*) FROM vocabulary;  -- 应该与 Excel 行数一致
```

## 📊 性能优化建议

1. **创建索引**: 已在 `init_database.sql` 中创建
2. **使用连接池**: 高并发场景下使用 SQLAlchemy 连接池
3. **批量操作**: 使用 `execute_batch` 而不是逐条插入
4. **定期清理**: 定期清理旧的答题历史数据

## 🔐 安全建议

1. **不要硬编码密码**: 使用环境变量或配置文件
2. **使用强密码**: 包含大小写字母、数字、特殊字符
3. **限制远程访问**: 只允许特定 IP 连接
4. **定期备份**: 设置自动备份任务
5. **加密密码**: 用户密码应使用 bcrypt 等算法加密

## 📞 获取帮助

如果遇到问题：
1. 查看日志: `docker logs opengauss`
2. 查看 openGauss 文档: https://docs.opengauss.org/
3. 检查数据库连接配置

## 🎉 下一步

数据迁移完成后，你可以：
1. 修改 `VocabularyLearningSystem` 类使用数据库
2. 实现更复杂的用户权限管理
3. 添加数据分析和统计功能
4. 实现数据同步功能

---

**祝你迁移顺利！** 🚀
