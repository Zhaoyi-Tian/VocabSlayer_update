# 用户数据存储系统说明

## 概述

VocabSlayer 现已支持多用户独立数据存储。每个用户的学习数据（收藏本、复习本、学习记录、每日统计等）都保存在独立的 JSON 文件中。

## 目录结构

```
user/
├── {username}/
│   ├── profile.json          # 用户配置信息
│   ├── book.json             # 收藏本
│   ├── review.json           # 复习本
│   ├── record.json           # 学习记录
│   ├── day_stats.json        # 每日统计
│   └── chat_history.json     # AI 聊天历史
```

## 数据文件格式

### 1. profile.json - 用户配置
```json
{
  "username": "用户名",
  "created_at": "2025-01-26 12:00:00",
  "last_login": "2025-01-26 15:30:00",
  "preferences": {
    "main_language": "Chinese",
    "study_language": "English",
    "default_level": 2
  }
}
```

### 2. book.json - 收藏本
```json
{
  "words": [
    {
      "id": 1,
      "Chinese": "你好",
      "English": "hello",
      "Japanese": "こんにちは",
      "level": 2,
      "added_at": "2025-01-26 12:00:00"
    }
  ]
}
```

### 3. review.json - 复习本
```json
{
  "words": [
    {
      "id": 2,
      "Chinese": "世界",
      "English": "world",
      "Japanese": "世界",
      "level": 2,
      "weight": 10.0,
      "added_at": "2025-01-26 12:00:00",
      "updated_at": "2025-01-26 14:30:00"
    }
  ]
}
```

**weight 说明：**
- 权重越大，表示该单词越需要复习
- 答对时权重 × 0.8
- 答错时权重 × 1.2

### 4. record.json - 学习记录
```json
{
  "words": {
    "1": {
      "id": 1,
      "star": 2,
      "correct_count": 5,
      "wrong_count": 1,
      "last_studied": "2025-01-26 14:30:00"
    }
  }
}
```

**字段说明：**
- `star`: 熟练度星级（0-3星）
- `correct_count`: 答对次数
- `wrong_count`: 答错次数
- `last_studied`: 最后学习时间

### 5. day_stats.json - 每日统计
```json
{
  "daily_records": {
    "2025-01-26": {
      "date": "2025-01-26",
      "correct": 15,
      "wrong": 3,
      "total": 18
    }
  }
}
```

## API 使用说明

### 初始化用户数据管理器

```python
from server.user_data_manager import UserDataManager

# 创建用户数据管理器
udm = UserDataManager("username")
```

### 收藏本操作

```python
# 添加到收藏本
word_data = {
    'id': 1,
    'Chinese': '你好',
    'English': 'hello',
    'Japanese': 'こんにちは',
    'level': 2
}
udm.add_to_book(word_data)

# 获取收藏本
books = udm.get_book_words()

# 检查是否在收藏本中
is_bookmarked = udm.is_in_book(1)

# 从收藏本移除
udm.remove_from_book(1)
```

### 复习本操作

```python
# 添加到复习本
udm.add_to_review(word_data, weight=10.0)

# 更新权重（答对）
udm.update_review_weight(word_id, 0.8)

# 更新权重（答错）
udm.update_review_weight(word_id, 1.2)

# 获取复习本
review_words = udm.get_review_words()
```

### 学习记录操作

```python
# 更新学习记录（答对）
udm.update_word_record(word_id, is_correct=True)

# 更新学习记录（答错）
udm.update_word_record(word_id, is_correct=False)

# 获取单词记录
record = udm.get_word_record(word_id)

# 获取所有记录
all_records = udm.get_all_records()
```

### 每日统计操作

```python
# 更新今日统计
udm.update_day_stats(correct=10, wrong=2)

# 获取今日统计
today_stats = udm.get_day_stats()

# 获取指定日期统计
stats = udm.get_day_stats("2025-01-26")

# 获取所有统计
all_stats = udm.get_all_day_stats()

# 获取统计摘要
summary = udm.get_stats_summary()
```

### 用户偏好设置

```python
# 获取用户配置
profile = udm.get_profile()

# 设置偏好
udm.set_preference('main_language', 'Chinese')
udm.set_preference('study_language', 'English')

# 获取偏好
main_lang = udm.get_preference('main_language', default='Chinese')
```

### 数据备份

```python
# 导出所有数据为备份文件
backup_file = udm.export_to_json()
print(f"数据已备份到: {backup_file}")
```

## VocabularyLearningSystem 集成

系统已更新以支持用户独立数据：

```python
from server.my_test import VocabularyLearningSystem

# 创建带用户名的学习系统
vls = VocabularyLearningSystem(username="tianzhaoyi")

# 所有操作自动保存到用户独立文件
vls.add_to_book(word)
vls.handle_correct_answer(word)
vls.handle_wrong_answer(word)
vls.update_day_stats()
```

## 优势

1. **数据隔离**: 每个用户的数据完全独立，互不干扰
2. **轻量高效**: JSON 格式比 Excel 更轻量，读写速度快
3. **易于扩展**: 可以方便地添加新字段和功能
4. **便于备份**: 每个用户目录可以独立备份和恢复
5. **向后兼容**: 如果不提供用户名，系统仍使用共享 Excel 文件

## 数据迁移

如果需要从旧的共享 Excel 格式迁移到新的用户独立格式，可以参考 `server/migrate_to_database.py` 中的逻辑。

## 注意事项

1. 用户名不应包含特殊字符或路径分隔符
2. JSON 文件会自动创建，无需手动初始化
3. 所有时间戳使用 "YYYY-MM-DD HH:MM:SS" 格式
4. 词库数据 (`data.xlsx`) 仍然是所有用户共享的
