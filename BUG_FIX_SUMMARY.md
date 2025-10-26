# Bug 修复总结

## 问题描述
新用户首次使用时出现 `IndexError` 和 `KeyError`，导致程序崩溃。

## 根本原因
新用户的学习记录（`df2`）、复习本（`df3`）等 DataFrame 为空，但代码尝试访问不存在的索引。

## 已修复的问题

### 1. **_choose_word 方法** ([my_test.py:139-167](server/my_test.py#L139-L167))
- ✅ 添加空词库检查
- ✅ 改用循环代替递归，避免栈溢出
- ✅ 自动为新单词创建0星记录
- ✅ 确保总能返回一个单词（最多尝试10次）

**修复前:**
```python
record1 = int(self.df2.iloc[id00]['star'])  # IndexError!
```

**修复后:**
```python
if id1 in self.df2.index:
    record1 = int(self.df2.loc[id1, 'star'])
else:
    record1 = 0
    self.df2.loc[id1] = {'star': 0}
```

### 2. **handle_correct_answer 方法** ([my_test.py:361-370](server/my_test.py#L361-L370))
- ✅ 检查单词是否在 df2 中，不存在则初始化
- ✅ 同步更新到用户数据管理器

**修复前:**
```python
current_star = self.df2.loc[idx, 'star']  # KeyError!
```

**修复后:**
```python
if idx not in self.df2.index:
    self.df2.loc[idx] = {'star': 0}
current_star = self.df2.loc[idx, 'star']
```

### 3. **handle_wrong_answer 方法** ([my_test.py:372-397](server/my_test.py#L372-L397))
- ✅ 检查单词是否已在复习本中
- ✅ 避免重复添加，已存在则增加权重
- ✅ 权重上限设为50，避免无限增长

**改进:**
```python
elif idx not in self.df3.index:
    # 只有不在复习本中才添加
    self.df3 = pd.concat([self.df3, new_row])
    self.df3.loc[idx, 'weight'] = 10
else:
    # 已在复习本中，增加权重
    self.df3.loc[idx, 'weight'] = min(self.df3.loc[idx, 'weight'] * 1.2, 50)
```

### 4. **choose_word 方法** ([my_test.py:168-194](server/my_test.py#L168-L194))
- ✅ 添加空复习本检查，抛出友好异常
- ✅ 添加权重归一化，防止除零错误
- ✅ 处理所有权重为0的边界情况

**修复后:**
```python
if n == 0:
    raise ValueError("复习本为空，无法选择单词")

# 防止除零
total = sum(weights)
if total == 0:
    weights = [1.0 / n] * n
else:
    weights = [w / total for w in weights]
```

### 5. **复习训练界面** ([Review_training.py:450-463](client/Review_training.py#L450-L463))
- ✅ 捕获 ValueError 异常
- ✅ 显示友好提示：复习本为空
- ✅ 自动返回开始界面

**改进:**
```python
try:
    question, self.options, self.answer, self.word = self.VLS.generate_review_question()
except ValueError as e:
    QMessageBox.information(
        self,
        "提示",
        "复习本为空！\n请先进行常规训练，答错的单词会自动加入复习本。"
    )
    self.parent._switch_page(0)
    return
```

### 6. **_load_user_data_to_df 方法** ([my_test.py:80-127](server/my_test.py#L80-L127))
- ✅ 正确设置空 DataFrame 的索引名称
- ✅ 使用 `dtype=int` 确保数据类型正确

## 测试场景

### ✅ 场景1：新用户首次使用
- 创建新用户
- 进入常规训练
- 选择难度和语言
- 开始答题
- **结果:** 正常生成题目，不会崩溃

### ✅ 场景2：新用户尝试复习训练
- 新用户直接点击"复习训练"
- **结果:** 显示提示框"复习本为空"，自动返回开始界面

### ✅ 场景3：答题过程
- 答对题目：星级增加，JSON 文件正确更新
- 答错题目：加入复习本，权重设为10
- 重复答错：权重增加（最多50）

### ✅ 场景4：数据持久化
- 答题数据保存到用户 JSON 文件
- 重新登录后数据正确加载
- 每日统计正确累计

## 防御性编程改进

1. **索引检查**: 所有 DataFrame 访问前都检查索引是否存在
2. **异常处理**: 关键方法添加 try-except，提供友好错误提示
3. **边界条件**: 处理空数据、零权重等边界情况
4. **避免递归**: 用循环代替递归，防止栈溢出
5. **数据同步**: DataFrame 和 JSON 双向同步，确保一致性

## 建议

### 短期改进
- ✅ 所有修复已完成并测试

### 长期优化
1. 考虑迁移到数据库（SQLite），避免 DataFrame 和 JSON 的复杂转换
2. 添加数据验证层，确保数据完整性
3. 实现数据备份和恢复功能
4. 添加单元测试覆盖关键逻辑

## 影响范围
- ✅ 不影响现有老用户（向后兼容）
- ✅ 修复新用户无法使用的问题
- ✅ 提升系统稳定性和用户体验
