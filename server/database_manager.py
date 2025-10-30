# -*- coding: utf-8 -*-
"""
数据库管理模块 - 支持多种数据库后端
"""
import os
import json
from abc import ABC, abstractmethod
import pandas as pd


class DatabaseInterface(ABC):
    """数据库接口抽象类"""

    @abstractmethod
    def connect(self):
        """连接数据库"""
        pass

    @abstractmethod
    def close(self):
        """关闭连接"""
        pass

    @abstractmethod
    def get_vocabulary(self, level=None):
        """获取词汇数据"""
        pass

    @abstractmethod
    def get_user_records(self, username):
        """获取用户学习记录"""
        pass

    @abstractmethod
    def get_review_list(self, username):
        """获取用户复习本"""
        pass

    @abstractmethod
    def get_bookmarks(self, username):
        """获取用户收藏本"""
        pass

    @abstractmethod
    def get_daily_stats(self, username):
        """获取用户每日统计"""
        pass

    @abstractmethod
    def update_user_record(self, username, vocab_id, star):
        """更新用户学习记录"""
        pass

    @abstractmethod
    def add_to_review_list(self, username, vocab_id, weight=10.0):
        """添加到复习本"""
        pass

    @abstractmethod
    def update_review_weight(self, username, vocab_id, weight):
        """更新复习权重"""
        pass

    @abstractmethod
    def add_bookmark(self, username, vocab_id):
        """添加收藏"""
        pass

    @abstractmethod
    def update_daily_stats(self, username, date, total, correct, wrong):
        """更新每日统计"""
        pass


class ExcelDatabase(DatabaseInterface):
    """Excel 文件数据库实现（兼容现有系统）"""

    def __init__(self, data_dir='server'):
        self.data_dir = data_dir
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_dir = os.path.join(self.root_dir, data_dir)
        self.df_vocab = None
        self.df_records = None
        self.df_review = None
        self.df_bookmarks = None
        self.df_daily = None

    def connect(self):
        """加载 Excel 文件"""
        try:
            self.df_vocab = pd.read_excel(os.path.join(self.server_dir, 'data.xlsx'), index_col=0)
            self.df_records = pd.read_excel(os.path.join(self.server_dir, 'record.xlsx'), index_col=0, sheet_name='Sheet1')
            self.df_review = pd.read_excel(os.path.join(self.server_dir, 'review.xlsx'), index_col=0, sheet_name='Sheet1')
            self.df_bookmarks = pd.read_excel(os.path.join(self.server_dir, 'book.xlsx'), index_col=0, sheet_name='Sheet1')
            self.df_daily = pd.read_excel(os.path.join(self.server_dir, 'day_record.xlsx'), index_col=0, sheet_name='Sheet1')
            return True
        except Exception as e:
            print(f"Excel 数据加载失败: {e}")
            return False

    def close(self):
        """保存所有更改"""
        self._save_all()

    def _save_all(self):
        """保存所有 Excel 文件"""
        try:
            self.df_vocab.to_excel(os.path.join(self.server_dir, 'data.xlsx'), index=True)
            self.df_records.to_excel(os.path.join(self.server_dir, 'record.xlsx'), index=True)
            self.df_review.to_excel(os.path.join(self.server_dir, 'review.xlsx'), index=True)
            self.df_bookmarks.to_excel(os.path.join(self.server_dir, 'book.xlsx'), index=True)
            self.df_daily.to_excel(os.path.join(self.server_dir, 'day_record.xlsx'), index=True)
        except Exception as e:
            print(f"Excel 数据保存失败: {e}")

    def get_vocabulary(self, level=None):
        """获取词汇数据"""
        if level:
            return self.df_vocab[self.df_vocab['level'] == level]
        return self.df_vocab

    def get_user_records(self, username):
        """获取用户学习记录（Excel 版本不区分用户）"""
        return self.df_records

    def get_review_list(self, username):
        """获取用户复习本"""
        return self.df_review

    def get_bookmarks(self, username):
        """获取用户收藏本"""
        return self.df_bookmarks

    def get_daily_stats(self, username):
        """获取用户每日统计"""
        return self.df_daily

    def update_user_record(self, username, vocab_id, star):
        """更新用户学习记录"""
        if vocab_id in self.df_records.index:
            self.df_records.loc[vocab_id, 'star'] = star
            self._save_all()

    def add_to_review_list(self, username, vocab_id, weight=10.0):
        """添加到复习本"""
        if vocab_id not in self.df_review.index:
            new_row = self.df_vocab.loc[[vocab_id]]
            self.df_review = pd.concat([self.df_review, new_row])
            self.df_review.loc[vocab_id, 'weight'] = weight
            self._save_all()

    def update_review_weight(self, username, vocab_id, weight):
        """更新复习权重"""
        if vocab_id in self.df_review.index:
            self.df_review.loc[vocab_id, 'weight'] = weight
            self._save_all()

    def add_bookmark(self, username, vocab_id):
        """添加收藏"""
        if vocab_id not in self.df_bookmarks.index:
            new_row = self.df_vocab.loc[[vocab_id]]
            if self.df_bookmarks.empty:
                self.df_bookmarks = new_row
            else:
                self.df_bookmarks = pd.concat([self.df_bookmarks, new_row])
            self._save_all()

    def update_daily_stats(self, username, date, total, correct, wrong):
        """更新每日统计"""
        if date not in self.df_daily.index:
            self.df_daily.loc[date] = [total, correct, wrong]
        else:
            self.df_daily.loc[date, 'total'] += total
            self.df_daily.loc[date, 'ac'] += correct
            self.df_daily.loc[date, 'wa'] += wrong
        self._save_all()


class OpenGaussDatabase(DatabaseInterface):
    """openGauss 数据库实现"""

    def __init__(self, host='localhost', port=5432, database='vocabulary_db',
                 user='opengauss', password='password'):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self):
        """连接到 openGauss 数据库"""
        try:
            import py_opengauss

            # 构建连接字符串
            conn_str = f'opengauss://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
            self.conn = py_opengauss.open(conn_str)
            return True
        except ImportError:
            print("错误: 请安装 py_opengauss 库")
            return False
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def get_vocabulary(self, level=None):
        """获取词汇数据"""
        if level:
            query = self.conn.prepare("SELECT vocab_id, english, chinese, japanese, level, created_at FROM vocabulary WHERE level = $1")
            results = query(level)
        else:
            query = self.conn.prepare("SELECT vocab_id, english, chinese, japanese, level, created_at FROM vocabulary")
            results = query()

        # 转换为DataFrame并设置列名
        df = pd.DataFrame(results, columns=['vocab_id', 'english', 'chinese', 'japanese', 'level', 'created_at'])
        return df

    def get_user_records(self, username):
        """获取用户学习记录"""
        query = self.conn.prepare("""
            SELECT lr.record_id, lr.user_id, lr.vocab_id, lr.star, lr.last_reviewed, lr.review_count,
                   v.english, v.chinese, v.japanese, v.level
            FROM user_learning_records lr
            JOIN users u ON lr.user_id = u.user_id
            JOIN vocabulary v ON lr.vocab_id = v.vocab_id
            WHERE u.username = $1
        """)
        results = query(username)
        df = pd.DataFrame(results, columns=['record_id', 'user_id', 'vocab_id', 'star', 'last_reviewed', 'review_count',
                                             'english', 'chinese', 'japanese', 'level'])
        return df

    def get_review_list(self, username):
        """获取用户复习本"""
        query = self.conn.prepare("""
            SELECT rl.review_id, rl.user_id, rl.vocab_id, rl.weight, rl.added_at, rl.last_reviewed,
                   v.english, v.chinese, v.japanese, v.level
            FROM user_review_list rl
            JOIN users u ON rl.user_id = u.user_id
            JOIN vocabulary v ON rl.vocab_id = v.vocab_id
            WHERE u.username = $1
        """)
        results = query(username)
        df = pd.DataFrame(results, columns=['review_id', 'user_id', 'vocab_id', 'weight', 'added_at', 'last_reviewed',
                                             'english', 'chinese', 'japanese', 'level'])
        return df

    def get_bookmarks(self, username):
        """获取用户收藏本"""
        query = self.conn.prepare("""
            SELECT b.bookmark_id, b.user_id, b.vocab_id, b.added_at, b.note,
                   v.english, v.chinese, v.japanese, v.level
            FROM user_bookmarks b
            JOIN users u ON b.user_id = u.user_id
            JOIN vocabulary v ON b.vocab_id = v.vocab_id
            WHERE u.username = $1
        """)
        results = query(username)
        df = pd.DataFrame(results, columns=['bookmark_id', 'user_id', 'vocab_id', 'added_at', 'note',
                                             'english', 'chinese', 'japanese', 'level'])
        return df

    def get_daily_stats(self, username):
        """获取用户每日统计"""
        query = self.conn.prepare("""
            SELECT ds.stat_id, ds.user_id, ds.date, ds.total_questions, ds.correct_answers, ds.wrong_answers
            FROM user_daily_stats ds
            JOIN users u ON ds.user_id = u.user_id
            WHERE u.username = $1
            ORDER BY ds.date
        """)
        results = query(username)
        df = pd.DataFrame(results, columns=['stat_id', 'user_id', 'date', 'total_questions', 'correct_answers', 'wrong_answers'])
        return df

    def _get_user_id(self, username):
        """获取用户 ID"""
        query = self.conn.prepare("SELECT user_id FROM users WHERE username = $1")
        result = query(username)
        return result[0]['user_id'] if result else None

    def _create_user(self, username, password):
        """创建新用户"""
        try:
            insert_query = self.conn.prepare("""
                INSERT INTO users (username, password)
                VALUES ($1, $2)
            """)
            insert_query(username, password)
            print(f"[DEBUG] User {username} created successfully")
        except Exception as e:
            print(f"[ERROR] Failed to create user {username}: {e}")

    def update_user_record(self, username, vocab_id, star):
        """更新用户学习记录"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = self.conn.prepare("SELECT record_id FROM user_learning_records WHERE user_id = $1 AND vocab_id = $2")
        existing = check_query(user_id, vocab_id)

        if existing:
            # 更新
            update_query = self.conn.prepare("""
                UPDATE user_learning_records
                SET star = $1, last_reviewed = CURRENT_TIMESTAMP, review_count = review_count + 1
                WHERE user_id = $2 AND vocab_id = $3
            """)
            update_query(star, user_id, vocab_id)
        else:
            # 插入
            insert_query = self.conn.prepare("""
                INSERT INTO user_learning_records (user_id, vocab_id, star, last_reviewed, review_count)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP, 1)
            """)
            insert_query(user_id, vocab_id, star)

    def add_to_review_list(self, username, vocab_id, weight=10.0):
        """添加到复习本"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = self.conn.prepare("SELECT review_id FROM user_review_list WHERE user_id = $1 AND vocab_id = $2")
        existing = check_query(user_id, vocab_id)

        if not existing:
            # 不存在才插入
            insert_query = self.conn.prepare("""
                INSERT INTO user_review_list (user_id, vocab_id, weight)
                VALUES ($1, $2, $3)
            """)
            insert_query(user_id, vocab_id, weight)

    def update_review_weight(self, username, vocab_id, weight):
        """更新复习权重"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        query = self.conn.prepare("""
            UPDATE user_review_list
            SET weight = $1, last_reviewed = CURRENT_TIMESTAMP
            WHERE user_id = $2 AND vocab_id = $3
        """)
        query(weight, user_id, vocab_id)

    def add_bookmark(self, username, vocab_id):
        """添加收藏"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = self.conn.prepare("SELECT bookmark_id FROM user_bookmarks WHERE user_id = $1 AND vocab_id = $2")
        existing = check_query(user_id, vocab_id)

        if not existing:
            # 不存在才插入
            insert_query = self.conn.prepare("""
                INSERT INTO user_bookmarks (user_id, vocab_id)
                VALUES ($1, $2)
            """)
            insert_query(user_id, vocab_id)

    def update_daily_stats(self, username, date, total, correct, wrong):
        """更新每日统计"""
        user_id = self._get_user_id(username)
        if not user_id:
            # 用户不存在，先创建用户
            print(f"[DEBUG] User {username} not found in database, creating...")
            self._create_user(username, "default_password")  # 使用默认密码
            user_id = self._get_user_id(username)
            if not user_id:
                print(f"[ERROR] Failed to create user {username}")
                return

        # 确保日期是字符串格式 'YYYY-MM-DD'
        if hasattr(date, 'strftime'):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = str(date)

        # 先检查是否存在 - 直接在SQL中嵌入日期字符串
        check_sql = f"SELECT stat_id FROM user_daily_stats WHERE user_id = $1 AND date = '{date_str}'"
        check_query = self.conn.prepare(check_sql)
        existing = check_query(user_id)

        if existing:
            # 更新（累加）
            update_sql = f"""
                UPDATE user_daily_stats
                SET total_questions = total_questions + $1,
                    correct_answers = correct_answers + $2,
                    wrong_answers = wrong_answers + $3
                WHERE user_id = $4 AND date = '{date_str}'
            """
            update_query = self.conn.prepare(update_sql)
            update_query(total, correct, wrong, user_id)
        else:
            # 插入
            insert_sql = f"""
                INSERT INTO user_daily_stats (user_id, date, total_questions, correct_answers, wrong_answers)
                VALUES ($1, '{date_str}', $2, $3, $4)
            """
            insert_query = self.conn.prepare(insert_sql)
            insert_query(user_id, total, correct, wrong)

    def get_ranking_data(self):
        """获取所有用户的排行榜数据"""
        try:
            query = self.conn.prepare("""
                SELECT
                    u.username,

                    -- 今日数据
                    COALESCE(today.total_questions, 0) as today_questions,
                    COALESCE(today.accuracy, 0) as today_accuracy,

                    -- 历史总数据
                    COALESCE(total.total_questions, 0) as total_questions,
                    COALESCE(total.avg_accuracy, 0) as total_accuracy,

                    -- 学习单词数
                    COALESCE(words.words_learned, 0) as words_learned,

                    -- 总积分
                    COALESCE(config.total_score, 0) as total_score,

                    -- 学习天数
                    COALESCE(days.study_days, 0) as study_days

                FROM users u

                -- 今日统计
                LEFT JOIN (
                    SELECT user_id, total_questions,
                           CASE WHEN total_questions > 0
                                THEN (correct_answers::float / total_questions * 100)
                                ELSE 0
                           END as accuracy
                    FROM user_daily_stats
                    WHERE date = CURRENT_DATE
                ) today ON u.user_id = today.user_id

                -- 历史总统计
                LEFT JOIN (
                    SELECT user_id,
                           SUM(total_questions) as total_questions,
                           CASE WHEN SUM(total_questions) > 0
                                THEN (SUM(correct_answers)::float / SUM(total_questions) * 100)
                                ELSE 0
                           END as avg_accuracy
                    FROM user_daily_stats
                    GROUP BY user_id
                ) total ON u.user_id = total.user_id

                -- 学习单词统计
                LEFT JOIN (
                    SELECT user_id,
                           COUNT(DISTINCT vocab_id) as words_learned
                    FROM user_learning_records
                    GROUP BY user_id
                ) words ON u.user_id = words.user_id

                -- 总积分
                LEFT JOIN (
                    SELECT user_id, total_score
                    FROM user_config
                ) config ON u.user_id = config.user_id

                -- 学习天数统计
                LEFT JOIN (
                    SELECT user_id,
                           COUNT(DISTINCT date) as study_days
                    FROM user_daily_stats
                    WHERE total_questions > 0
                    GROUP BY user_id
                ) days ON u.user_id = days.user_id

                ORDER BY u.username
            """)

            result = query()
            ranking_list = []

            for row in result:
                user_stats = {
                    'username': row['username'],
                    'today_questions': int(row['today_questions']) if row['today_questions'] else 0,
                    'today_accuracy': float(row['today_accuracy']) if row['today_accuracy'] else 0.0,
                    'total_questions': int(row['total_questions']) if row['total_questions'] else 0,
                    'total_accuracy': float(row['total_accuracy']) if row['total_accuracy'] else 0.0,
                    'words_learned': int(row['words_learned']) if row['words_learned'] else 0,
                    'total_score': float(row['total_score']) if row['total_score'] else 0.0,
                    'study_days': int(row['study_days']) if row['study_days'] else 0,
                }
                ranking_list.append(user_stats)

            return ranking_list

        except Exception as e:
            print(f"[ERROR] Failed to get ranking data: {e}")
            return []

    def get_user_config(self, username):
        """获取用户配置"""
        user_id = self._get_user_id(username)
        if not user_id:
            return None

        # 先检查哪些字段存在
        try:
            check_columns = self.conn.prepare("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user_config'
            """)
            result = check_columns()
            existing_columns = [r['column_name'] for r in result]

            # 构建查询语句，只查询存在的字段
            select_fields = ['api_key']  # api_key 是必须的

            if 'api_endpoint' in existing_columns:
                select_fields.append('api_endpoint')
            if 'api_model' in existing_columns:
                select_fields.append('api_model')
            if 'deepseek_chat_history' in existing_columns:
                select_fields.append('deepseek_chat_history')
            if 'total_score' in existing_columns:
                select_fields.append('total_score')
            if 'difficulty' in existing_columns:
                select_fields.append('difficulty')
            if 'target_score' in existing_columns:
                select_fields.append('target_score')

            select_fields.extend(['primary_color', 'theme', 'main_language', 'study_language'])

            query_sql = f"""
                SELECT {', '.join(select_fields)}
                FROM user_config
                WHERE user_id = $1
            """
            query = self.conn.prepare(query_sql)
            result = query(user_id)

            if result and len(result) > 0:
                # 安全地获取字段值
                row = result[0]
                config = {
                    'api_key': row['api_key'] if row['api_key'] else '',
                    'api_endpoint': row['api_endpoint'] if 'api_endpoint' in select_fields and row['api_endpoint'] else 'https://api.deepseek.com',
                    'api_model': row['api_model'] if 'api_model' in select_fields and row['api_model'] else 'deepseek-chat',
                    'chat_history': row['deepseek_chat_history'] if 'deepseek_chat_history' in select_fields and row['deepseek_chat_history'] else '[]',
                    'total_score': float(row['total_score']) if 'total_score' in select_fields and row['total_score'] is not None else 0.0,
                    'primary_color': row['primary_color'],
                    'theme': row['theme'],
                    'main_language': row['main_language'],
                    'study_language': row['study_language'],
                    'difficulty': int(row['difficulty']) if 'difficulty' in select_fields and row['difficulty'] is not None else 1,
                    'target_score': int(row['target_score']) if 'target_score' in select_fields and row['target_score'] is not None else 10000
                }
                return config
        except Exception as e:
            print(f"[ERROR] Failed to get user config: {e}")

        return None

    def save_user_config(self, username, api_key=None, api_endpoint=None, api_model=None,
                        chat_history=None, primary_color=None, theme=None, total_score=None,
                        main_language=None, study_language=None, difficulty=None, target_score=None):
        """保存用户配置"""
        user_id = self._get_user_id(username)
        if not user_id:
            print(f"[ERROR] User {username} not found")
            return False

        try:
            # 先检查哪些字段存在
            check_columns = self.conn.prepare("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user_config'
            """)
            result = check_columns()
            existing_columns = [r['column_name'] for r in result]

            # 检查是否已存在配置
            check_query = self.conn.prepare("SELECT user_id FROM user_config WHERE user_id = $1")
            existing = check_query(user_id)

            if existing:
                # 更新配置 - 只更新非 None 且字段存在的字段
                update_parts = []
                params = []
                param_count = 1

                if api_key is not None and 'api_key' in existing_columns:
                    update_parts.append(f"api_key = ${param_count}")
                    params.append(api_key)
                    param_count += 1

                if api_endpoint is not None and 'api_endpoint' in existing_columns:
                    update_parts.append(f"api_endpoint = ${param_count}")
                    params.append(api_endpoint)
                    param_count += 1

                if api_model is not None and 'api_model' in existing_columns:
                    update_parts.append(f"api_model = ${param_count}")
                    params.append(api_model)
                    param_count += 1

                if chat_history is not None and 'deepseek_chat_history' in existing_columns:
                    update_parts.append(f"deepseek_chat_history = ${param_count}")
                    params.append(chat_history)
                    param_count += 1

                if total_score is not None and 'total_score' in existing_columns:
                    update_parts.append(f"total_score = ${param_count}")
                    params.append(total_score)
                    param_count += 1

                if primary_color is not None and 'primary_color' in existing_columns:
                    update_parts.append(f"primary_color = ${param_count}")
                    params.append(primary_color)
                    param_count += 1

                if theme is not None and 'theme' in existing_columns:
                    update_parts.append(f"theme = ${param_count}")
                    params.append(theme)
                    param_count += 1

                if main_language is not None and 'main_language' in existing_columns:
                    update_parts.append(f"main_language = ${param_count}")
                    params.append(main_language)
                    param_count += 1

                if study_language is not None and 'study_language' in existing_columns:
                    update_parts.append(f"study_language = ${param_count}")
                    params.append(study_language)
                    param_count += 1

                if difficulty is not None and 'difficulty' in existing_columns:
                    update_parts.append(f"difficulty = ${param_count}")
                    params.append(difficulty)
                    param_count += 1

                if target_score is not None and 'target_score' in existing_columns:
                    update_parts.append(f"target_score = ${param_count}")
                    params.append(target_score)
                    param_count += 1

                if update_parts:
                    if 'updated_at' in existing_columns:
                        update_parts.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(user_id)

                    update_sql = f"""
                        UPDATE user_config
                        SET {', '.join(update_parts)}
                        WHERE user_id = ${param_count}
                    """
                    update_query = self.conn.prepare(update_sql)
                    update_query(*params)
            else:
                # 插入新配置 - 只插入存在的字段
                insert_fields = ['user_id']
                insert_values = ['$1']
                insert_params = [user_id]
                param_count = 2

                if 'api_key' in existing_columns:
                    insert_fields.append('api_key')
                    insert_values.append(f'${param_count}')
                    insert_params.append(api_key or '')
                    param_count += 1

                if 'api_endpoint' in existing_columns:
                    insert_fields.append('api_endpoint')
                    insert_values.append(f'${param_count}')
                    insert_params.append(api_endpoint or 'https://api.deepseek.com')
                    param_count += 1

                if 'api_model' in existing_columns:
                    insert_fields.append('api_model')
                    insert_values.append(f'${param_count}')
                    insert_params.append(api_model or 'deepseek-chat')
                    param_count += 1

                if 'deepseek_chat_history' in existing_columns:
                    insert_fields.append('deepseek_chat_history')
                    insert_values.append(f'${param_count}')
                    insert_params.append(chat_history or '[]')
                    param_count += 1

                if 'total_score' in existing_columns:
                    insert_fields.append('total_score')
                    insert_values.append(f'${param_count}')
                    insert_params.append(total_score or 0.0)
                    param_count += 1

                if 'primary_color' in existing_columns:
                    insert_fields.append('primary_color')
                    insert_values.append(f'${param_count}')
                    insert_params.append(primary_color or '#4080FF')
                    param_count += 1

                if 'theme' in existing_columns:
                    insert_fields.append('theme')
                    insert_values.append(f'${param_count}')
                    insert_params.append(theme or 'light')
                    param_count += 1

                if 'main_language' in existing_columns:
                    insert_fields.append('main_language')
                    insert_values.append(f'${param_count}')
                    insert_params.append(main_language or 'Chinese')
                    param_count += 1

                if 'study_language' in existing_columns:
                    insert_fields.append('study_language')
                    insert_values.append(f'${param_count}')
                    insert_params.append(study_language or 'English')
                    param_count += 1

                if 'difficulty' in existing_columns:
                    insert_fields.append('difficulty')
                    insert_values.append(f'${param_count}')
                    insert_params.append(difficulty or 1)
                    param_count += 1

                if 'target_score' in existing_columns:
                    insert_fields.append('target_score')
                    insert_values.append(f'${param_count}')
                    insert_params.append(target_score or 10000)
                    param_count += 1

                insert_sql = f"""
                    INSERT INTO user_config ({', '.join(insert_fields)})
                    VALUES ({', '.join(insert_values)})
                """
                insert_query = self.conn.prepare(insert_sql)
                insert_query(*insert_params)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to save user config: {e}")
            return False


class DatabaseFactory:
    """数据库工厂类 - 根据配置创建相应的数据库实例"""

    @staticmethod
    def create_database(db_type='excel', **kwargs):
        """
        创建数据库实例

        Args:
            db_type: 数据库类型 ('excel', 'opengauss', 'mock')
            **kwargs: 数据库连接参数

        Returns:
            DatabaseInterface 实例
        """
        if db_type == 'excel':
            return ExcelDatabase(**kwargs)
        elif db_type == 'opengauss':
            return OpenGaussDatabase(**kwargs)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

    @staticmethod
    def from_config_file(config_path='config.json'):
        """从配置文件创建数据库实例（已废弃，改为从 db_config 模块读取）"""
        # 不再读取 config.json，改为从 db_config 模块获取配置
        from server.db_config import get_database_config
        config = get_database_config()

        db_type = config.get('database_type', 'excel')
        db_config = config.get('database_config', {})

        return DatabaseFactory.create_database(db_type, **db_config)


# 使用示例
if __name__ == '__main__':
    # 方式1: 使用 Excel 数据库
    db = DatabaseFactory.create_database('excel')
    db.connect()
    vocab = db.get_vocabulary(level=1)
    print(f"Level 1 词汇数量: {len(vocab)}")
    db.close()

    # 方式2: 使用 openGauss 数据库
    # db = DatabaseFactory.create_database(
    #     'opengauss',
    #     host='192.168.1.100',
    #     port=5432,
    #     database='vocabulary_db',
    #     user='opengauss',
    #     password='password'
    # )
    # db.connect()
    # vocab = db.get_vocabulary(level=1)
    # db.close()

    # 方式3: 从配置文件读取
    # db = DatabaseFactory.from_config_file('config.json')
    # db.connect()
    # vocab = db.get_vocabulary()
    # db.close()
