#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
适配 openGauss 的数据迁移工具
"""
import os
import sys
import json
import pandas as pd
import psycopg2
from datetime import datetime

class OpenGaussMigrator:
    """openGauss 数据迁移工具"""

    def __init__(self, db_config):
        self.db_config = db_config
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_dir = os.path.join(self.root_dir, 'server')
        self.user_dir = os.path.join(self.root_dir, 'user')
        self.conn = None
        self.cursor = None

    def connect_database(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def close_database(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ 数据库连接已关闭")

    def migrate_vocabulary(self):
        """迁移词汇表数据"""
        print("\n📚 开始迁移词汇表数据...")
        try:
            # 读取 Excel
            excel_path = os.path.join(self.server_dir, 'data.xlsx')
            df = pd.read_excel(excel_path, index_col=0)
            print(f"   读取到 {len(df)} 条词汇数据")

            # 先清空表（如果需要重新迁移）
            # self.cursor.execute("TRUNCATE TABLE vocabulary CASCADE")

            # 批量插入
            inserted_count = 0
            for idx, row in df.iterrows():
                try:
                    # 检查是否已存在
                    self.cursor.execute(
                        "SELECT vocab_id FROM vocabulary WHERE english = %s AND chinese = %s AND japanese = %s",
                        (row.get('English', ''), row.get('Chinese', ''), row.get('Japanese', ''))
                    )
                    if self.cursor.fetchone():
                        continue  # 已存在，跳过

                    # 插入新记录
                    self.cursor.execute(
                        """INSERT INTO vocabulary (english, chinese, japanese, level)
                           VALUES (%s, %s, %s, %s)""",
                        (row.get('English', ''), row.get('Chinese', ''),
                         row.get('Japanese', ''), int(row.get('level', 1)))
                    )
                    inserted_count += 1
                except Exception as e:
                    print(f"   警告: 插入词汇失败 (ID: {idx}): {e}")
                    continue

            self.conn.commit()
            print(f"✅ 词汇表迁移完成，插入 {inserted_count} 条新数据")
            return True

        except Exception as e:
            print(f"❌ 词汇表迁移失败: {e}")
            self.conn.rollback()
            return False

    def migrate_user_from_json(self, username):
        """从 JSON 文件迁移用户数据"""
        print(f"\n👤 开始迁移用户 '{username}' 的数据...")

        user_path = os.path.join(self.user_dir, username)
        if not os.path.exists(user_path):
            print(f"   ⚠️  用户目录不存在: {user_path}")
            return False

        # 确保用户存在
        user_id = self._ensure_user_exists(username)
        if not user_id:
            return False

        # 获取词汇 ID 映射
        vocab_mapping = self._get_vocab_id_mapping()

        # 迁移各项数据
        self._migrate_user_records_from_json(user_id, user_path, vocab_mapping)
        self._migrate_user_review_from_json(user_id, user_path, vocab_mapping)
        self._migrate_user_bookmarks_from_json(user_id, user_path, vocab_mapping)
        self._migrate_user_stats_from_json(user_id, user_path)

        return True

    def _ensure_user_exists(self, username, password='123456'):
        """确保用户存在"""
        try:
            self.cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = self.cursor.fetchone()

            if result:
                user_id = result[0]
                print(f"   用户 '{username}' 已存在 (ID: {user_id})")
            else:
                self.cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING user_id",
                    (username, password)
                )
                user_id = self.cursor.fetchone()[0]
                self.conn.commit()
                print(f"   创建新用户 '{username}' (ID: {user_id})")

            return user_id

        except Exception as e:
            print(f"❌ 用户处理失败: {e}")
            self.conn.rollback()
            return None

    def _get_vocab_id_mapping(self):
        """获取词汇 ID 映射"""
        self.cursor.execute("SELECT vocab_id, english, chinese, japanese FROM vocabulary")
        db_vocab = self.cursor.fetchall()

        mapping = {}
        for db_id, eng, chi, jpn in db_vocab:
            key = f"{eng}|{chi}|{jpn}"
            mapping[key] = db_id

        return mapping

    def _migrate_user_records_from_json(self, user_id, user_path, vocab_mapping):
        """从 JSON 迁移学习记录"""
        print("\n   📝 迁移学习记录...")
        try:
            record_file = os.path.join(user_path, 'record.json')
            if not os.path.exists(record_file):
                print("      ⚠️  record.json 不存在")
                return

            with open(record_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            words = data.get('words', {})
            count = 0

            for word_id, record in words.items():
                # 通过 word_id 找到对应的词汇
                # 需要从原始 Excel 获取完整信息
                try:
                    star = record.get('star', 0)
                    # 简单实现：通过 ID 直接映射
                    vocab_id = int(word_id)

                    # 检查是否存在
                    self.cursor.execute(
                        "SELECT record_id FROM user_learning_records WHERE user_id = %s AND vocab_id = %s",
                        (user_id, vocab_id)
                    )
                    if self.cursor.fetchone():
                        # 更新
                        self.cursor.execute(
                            "UPDATE user_learning_records SET star = %s WHERE user_id = %s AND vocab_id = %s",
                            (star, user_id, vocab_id)
                        )
                    else:
                        # 插入
                        self.cursor.execute(
                            "INSERT INTO user_learning_records (user_id, vocab_id, star) VALUES (%s, %s, %s)",
                            (user_id, vocab_id, star)
                        )
                    count += 1
                except Exception as e:
                    continue

            self.conn.commit()
            print(f"      ✅ 迁移 {count} 条学习记录")

        except Exception as e:
            print(f"      ❌ 学习记录迁移失败: {e}")
            self.conn.rollback()

    def _migrate_user_review_from_json(self, user_id, user_path, vocab_mapping):
        """从 JSON 迁移复习本"""
        print("\n   📖 迁移复习本...")
        try:
            review_file = os.path.join(user_path, 'review.json')
            if not os.path.exists(review_file):
                print("      ⚠️  review.json 不存在")
                return

            with open(review_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            words = data.get('words', [])
            count = 0

            for word in words:
                try:
                    word_id = word.get('id')
                    weight = word.get('weight', 10.0)

                    # 检查是否存在
                    self.cursor.execute(
                        "SELECT review_id FROM user_review_list WHERE user_id = %s AND vocab_id = %s",
                        (user_id, word_id)
                    )
                    if self.cursor.fetchone():
                        self.cursor.execute(
                            "UPDATE user_review_list SET weight = %s WHERE user_id = %s AND vocab_id = %s",
                            (weight, user_id, word_id)
                        )
                    else:
                        self.cursor.execute(
                            "INSERT INTO user_review_list (user_id, vocab_id, weight) VALUES (%s, %s, %s)",
                            (user_id, word_id, weight)
                        )
                    count += 1
                except Exception as e:
                    continue

            self.conn.commit()
            print(f"      ✅ 迁移 {count} 条复习记录")

        except Exception as e:
            print(f"      ❌ 复习本迁移失败: {e}")
            self.conn.rollback()

    def _migrate_user_bookmarks_from_json(self, user_id, user_path, vocab_mapping):
        """从 JSON 迁移收藏本"""
        print("\n   ⭐ 迁移收藏本...")
        try:
            book_file = os.path.join(user_path, 'book.json')
            if not os.path.exists(book_file):
                print("      ⚠️  book.json 不存在")
                return

            with open(book_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            words = data.get('words', [])
            count = 0

            for word in words:
                try:
                    word_id = word.get('id')

                    # 检查是否存在
                    self.cursor.execute(
                        "SELECT bookmark_id FROM user_bookmarks WHERE user_id = %s AND vocab_id = %s",
                        (user_id, word_id)
                    )
                    if not self.cursor.fetchone():
                        self.cursor.execute(
                            "INSERT INTO user_bookmarks (user_id, vocab_id) VALUES (%s, %s)",
                            (user_id, word_id)
                        )
                        count += 1
                except Exception as e:
                    continue

            self.conn.commit()
            print(f"      ✅ 迁移 {count} 条收藏记录")

        except Exception as e:
            print(f"      ❌ 收藏本迁移失败: {e}")
            self.conn.rollback()

    def _migrate_user_stats_from_json(self, user_id, user_path):
        """从 JSON 迁移每日统计"""
        print("\n   📊 迁移每日统计...")
        try:
            stats_file = os.path.join(user_path, 'day_stats.json')
            if not os.path.exists(stats_file):
                print("      ⚠️  day_stats.json 不存在")
                return

            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            daily_records = data.get('daily_records', {})
            count = 0

            for date_str, stats in daily_records.items():
                try:
                    total = stats.get('total', 0)
                    correct = stats.get('correct', 0)
                    wrong = stats.get('wrong', 0)

                    # 检查是否存在
                    self.cursor.execute(
                        "SELECT stat_id FROM user_daily_stats WHERE user_id = %s AND date = %s",
                        (user_id, date_str)
                    )
                    if self.cursor.fetchone():
                        self.cursor.execute(
                            """UPDATE user_daily_stats
                               SET total_questions = %s, correct_answers = %s, wrong_answers = %s
                               WHERE user_id = %s AND date = %s""",
                            (total, correct, wrong, user_id, date_str)
                        )
                    else:
                        self.cursor.execute(
                            """INSERT INTO user_daily_stats
                               (user_id, date, total_questions, correct_answers, wrong_answers)
                               VALUES (%s, %s, %s, %s, %s)""",
                            (user_id, date_str, total, correct, wrong)
                        )
                    count += 1
                except Exception as e:
                    continue

            self.conn.commit()
            print(f"      ✅ 迁移 {count} 条统计记录")

        except Exception as e:
            print(f"      ❌ 每日统计迁移失败: {e}")
            self.conn.rollback()

    def migrate_all(self):
        """执行完整迁移"""
        print("=" * 60)
        print("🚀 开始数据迁移到 openGauss")
        print("=" * 60)

        if not self.connect_database():
            return False

        try:
            # 1. 迁移词汇表
            self.migrate_vocabulary()

            # 2. 迁移所有用户数据
            if os.path.exists(self.user_dir):
                users = [d for d in os.listdir(self.user_dir)
                        if os.path.isdir(os.path.join(self.user_dir, d))]

                print(f"\n找到 {len(users)} 个用户: {', '.join(users)}")

                for username in users:
                    self.migrate_user_from_json(username)

            print("\n" + "=" * 60)
            print("✅ 数据迁移全部完成！")
            print("=" * 60)
            return True

        except Exception as e:
            print(f"\n❌ 迁移过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.close_database()


if __name__ == '__main__':
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'vocabulary_db',
        'user': 'openEuler',  # 根据实际情况修改
        'password': 'Qq13896842746'  # openGauss 默认可能不需要密码（本地连接）
    }

    print("\n配置信息:")
    print(f"  数据库: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

    # 执行迁移
    migrator = OpenGaussMigrator(db_config)
    migrator.migrate_all()
