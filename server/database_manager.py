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
        """从配置文件创建数据库实例"""
        if not os.path.exists(config_path):
            # 默认使用 Excel
            return ExcelDatabase()

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

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
