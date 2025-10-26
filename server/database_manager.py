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
        self.conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接到 openGauss 数据库"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            return True
        except ImportError:
            print("错误: 请安装 psycopg2 库: pip install psycopg2-binary")
            return False
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_vocabulary(self, level=None):
        """获取词汇数据"""
        if level:
            query = "SELECT * FROM vocabulary WHERE level = %s"
            self.cursor.execute(query, (level,))
        else:
            query = "SELECT * FROM vocabulary"
            self.cursor.execute(query)

        results = self.cursor.fetchall()
        return pd.DataFrame(results)

    def get_user_records(self, username):
        """获取用户学习记录"""
        query = """
            SELECT lr.*, v.english, v.chinese, v.japanese, v.level
            FROM user_learning_records lr
            JOIN users u ON lr.user_id = u.user_id
            JOIN vocabulary v ON lr.vocab_id = v.vocab_id
            WHERE u.username = %s
        """
        self.cursor.execute(query, (username,))
        results = self.cursor.fetchall()
        return pd.DataFrame(results)

    def get_review_list(self, username):
        """获取用户复习本"""
        query = """
            SELECT rl.*, v.english, v.chinese, v.japanese, v.level
            FROM user_review_list rl
            JOIN users u ON rl.user_id = u.user_id
            JOIN vocabulary v ON rl.vocab_id = v.vocab_id
            WHERE u.username = %s
        """
        self.cursor.execute(query, (username,))
        results = self.cursor.fetchall()
        return pd.DataFrame(results)

    def get_bookmarks(self, username):
        """获取用户收藏本"""
        query = """
            SELECT b.*, v.english, v.chinese, v.japanese, v.level
            FROM user_bookmarks b
            JOIN users u ON b.user_id = u.user_id
            JOIN vocabulary v ON b.vocab_id = v.vocab_id
            WHERE u.username = %s
        """
        self.cursor.execute(query, (username,))
        results = self.cursor.fetchall()
        return pd.DataFrame(results)

    def get_daily_stats(self, username):
        """获取用户每日统计"""
        query = """
            SELECT ds.*
            FROM user_daily_stats ds
            JOIN users u ON ds.user_id = u.user_id
            WHERE u.username = %s
            ORDER BY ds.date
        """
        self.cursor.execute(query, (username,))
        results = self.cursor.fetchall()
        return pd.DataFrame(results)

    def _get_user_id(self, username):
        """获取用户 ID"""
        query = "SELECT user_id FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        return result['user_id'] if result else None

    def update_user_record(self, username, vocab_id, star):
        """更新用户学习记录"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = "SELECT record_id FROM user_learning_records WHERE user_id = %s AND vocab_id = %s"
        self.cursor.execute(check_query, (user_id, vocab_id))

        if self.cursor.fetchone():
            # 更新
            update_query = """
                UPDATE user_learning_records
                SET star = %s, last_reviewed = CURRENT_TIMESTAMP
                WHERE user_id = %s AND vocab_id = %s
            """
            self.cursor.execute(update_query, (star, user_id, vocab_id))
        else:
            # 插入
            insert_query = """
                INSERT INTO user_learning_records (user_id, vocab_id, star, last_reviewed)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(insert_query, (user_id, vocab_id, star))

        self.conn.commit()

    def add_to_review_list(self, username, vocab_id, weight=10.0):
        """添加到复习本"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = "SELECT review_id FROM user_review_list WHERE user_id = %s AND vocab_id = %s"
        self.cursor.execute(check_query, (user_id, vocab_id))

        if not self.cursor.fetchone():
            # 不存在才插入
            insert_query = """
                INSERT INTO user_review_list (user_id, vocab_id, weight)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(insert_query, (user_id, vocab_id, weight))
            self.conn.commit()

    def update_review_weight(self, username, vocab_id, weight):
        """更新复习权重"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        query = """
            UPDATE user_review_list
            SET weight = %s
            WHERE user_id = %s AND vocab_id = %s
        """
        self.cursor.execute(query, (weight, user_id, vocab_id))
        self.conn.commit()

    def add_bookmark(self, username, vocab_id):
        """添加收藏"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = "SELECT bookmark_id FROM user_bookmarks WHERE user_id = %s AND vocab_id = %s"
        self.cursor.execute(check_query, (user_id, vocab_id))

        if not self.cursor.fetchone():
            # 不存在才插入
            insert_query = """
                INSERT INTO user_bookmarks (user_id, vocab_id)
                VALUES (%s, %s)
            """
            self.cursor.execute(insert_query, (user_id, vocab_id))
            self.conn.commit()

    def update_daily_stats(self, username, date, total, correct, wrong):
        """更新每日统计"""
        user_id = self._get_user_id(username)
        if not user_id:
            return

        # 先检查是否存在
        check_query = "SELECT stat_id FROM user_daily_stats WHERE user_id = %s AND date = %s"
        self.cursor.execute(check_query, (user_id, date))

        if self.cursor.fetchone():
            # 更新（累加）
            update_query = """
                UPDATE user_daily_stats
                SET total_questions = total_questions + %s,
                    correct_answers = correct_answers + %s,
                    wrong_answers = wrong_answers + %s
                WHERE user_id = %s AND date = %s
            """
            self.cursor.execute(update_query, (total, correct, wrong, user_id, date))
        else:
            # 插入
            insert_query = """
                INSERT INTO user_daily_stats (user_id, date, total_questions, correct_answers, wrong_answers)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(insert_query, (user_id, date, total, correct, wrong))

        self.conn.commit()


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
