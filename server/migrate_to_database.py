#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel 数据迁移到 openGauss 数据库工具
"""
import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime


class ExcelToOpenGaussMigrator:
    """Excel 数据迁移工具"""

    def __init__(self, db_config, excel_dir='server'):
        """
        初始化迁移工具

        Args:
            db_config: 数据库连接配置字典
            excel_dir: Excel 文件所在目录
        """
        self.db_config = db_config
        self.excel_dir = excel_dir
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_dir = os.path.join(self.root_dir, excel_dir)
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

            # 准备插入数据
            vocab_data = []
            for idx, row in df.iterrows():
                vocab_data.append((
                    row.get('English', ''),
                    row.get('Chinese', ''),
                    row.get('Japanese', ''),
                    int(row.get('level', 1))
                ))

            # 批量插入
            insert_query = """
                INSERT INTO vocabulary (english, chinese, japanese, level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING vocab_id
            """

            inserted_count = 0
            for data in vocab_data:
                self.cursor.execute(insert_query, data)
                if self.cursor.fetchone():
                    inserted_count += 1

            self.conn.commit()
            print(f"✅ 词汇表迁移完成，插入 {inserted_count} 条新数据")
            return True

        except Exception as e:
            print(f"❌ 词汇表迁移失败: {e}")
            self.conn.rollback()
            return False

    def migrate_user_data(self, username='default_user'):
        """
        迁移用户数据（学习记录、复习本、收藏本）

        Args:
            username: 用户名，默认为 'default_user'
        """
        print(f"\n👤 开始迁移用户 '{username}' 的数据...")

        # 确保用户存在
        user_id = self._ensure_user_exists(username)
        if not user_id:
            print(f"❌ 无法创建用户 '{username}'")
            return False

        # 迁移学习记录
        self._migrate_learning_records(user_id)

        # 迁移复习本
        self._migrate_review_list(user_id)

        # 迁移收藏本
        self._migrate_bookmarks(user_id)

        # 迁移每日统计
        self._migrate_daily_stats(user_id)

        return True

    def _ensure_user_exists(self, username, password='default123'):
        """确保用户存在，如果不存在则创建"""
        try:
            # 检查用户是否存在
            self.cursor.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (username,)
            )
            result = self.cursor.fetchone()

            if result:
                user_id = result[0]
                print(f"   用户 '{username}' 已存在 (ID: {user_id})")
            else:
                # 创建新用户
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
        """获取词汇 ID 映射（Excel 索引 -> 数据库 ID）"""
        # 从数据库获取所有词汇
        self.cursor.execute(
            "SELECT vocab_id, english, chinese, japanese FROM vocabulary"
        )
        db_vocab = self.cursor.fetchall()

        # 读取 Excel
        excel_path = os.path.join(self.server_dir, 'data.xlsx')
        df = pd.read_excel(excel_path, index_col=0)

        # 建立映射
        mapping = {}
        for idx, row in df.iterrows():
            for db_id, eng, chi, jpn in db_vocab:
                if (row.get('English') == eng and
                    row.get('Chinese') == chi and
                    row.get('Japanese') == jpn):
                    mapping[idx] = db_id
                    break

        return mapping

    def _migrate_learning_records(self, user_id):
        """迁移学习记录"""
        print("\n   📝 迁移学习记录...")
        try:
            # 读取 Excel
            excel_path = os.path.join(self.server_dir, 'record.xlsx')
            df = pd.read_excel(excel_path, index_col=0, sheet_name='Sheet1')
            print(f"      读取到 {len(df)} 条学习记录")

            # 获取词汇 ID 映射
            vocab_mapping = self._get_vocab_id_mapping()

            # 准备插入数据
            records = []
            for idx, row in df.iterrows():
                if idx in vocab_mapping:
                    vocab_id = vocab_mapping[idx]
                    star = int(row.get('star', 0))
                    records.append((user_id, vocab_id, star))

            # 批量插入
            if records:
                insert_query = """
                    INSERT INTO user_learning_records (user_id, vocab_id, star)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, vocab_id) DO UPDATE
                    SET star = EXCLUDED.star
                """
                execute_batch(self.cursor, insert_query, records)
                self.conn.commit()
                print(f"   ✅ 学习记录迁移完成，处理 {len(records)} 条数据")
            else:
                print("   ⚠️  没有学习记录需要迁移")

        except Exception as e:
            print(f"   ❌ 学习记录迁移失败: {e}")
            self.conn.rollback()

    def _migrate_review_list(self, user_id):
        """迁移复习本"""
        print("\n   📖 迁移复习本...")
        try:
            # 读取 Excel
            excel_path = os.path.join(self.server_dir, 'review.xlsx')
            df = pd.read_excel(excel_path, index_col=0, sheet_name='Sheet1')
            print(f"      读取到 {len(df)} 条复习记录")

            # 获取词汇 ID 映射
            vocab_mapping = self._get_vocab_id_mapping()

            # 准备插入数据
            reviews = []
            for idx, row in df.iterrows():
                if idx in vocab_mapping:
                    vocab_id = vocab_mapping[idx]
                    weight = float(row.get('weight', 10.0))
                    reviews.append((user_id, vocab_id, weight))

            # 批量插入
            if reviews:
                insert_query = """
                    INSERT INTO user_review_list (user_id, vocab_id, weight)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, vocab_id) DO UPDATE
                    SET weight = EXCLUDED.weight
                """
                execute_batch(self.cursor, insert_query, reviews)
                self.conn.commit()
                print(f"   ✅ 复习本迁移完成，处理 {len(reviews)} 条数据")
            else:
                print("   ⚠️  复习本为空")

        except Exception as e:
            print(f"   ❌ 复习本迁移失败: {e}")
            self.conn.rollback()

    def _migrate_bookmarks(self, user_id):
        """迁移收藏本"""
        print("\n   ⭐ 迁移收藏本...")
        try:
            # 读取 Excel
            excel_path = os.path.join(self.server_dir, 'book.xlsx')
            df = pd.read_excel(excel_path, index_col=0, sheet_name='Sheet1')
            print(f"      读取到 {len(df)} 条收藏记录")

            # 获取词汇 ID 映射
            vocab_mapping = self._get_vocab_id_mapping()

            # 准备插入数据
            bookmarks = []
            for idx, row in df.iterrows():
                if idx in vocab_mapping:
                    vocab_id = vocab_mapping[idx]
                    bookmarks.append((user_id, vocab_id))

            # 批量插入
            if bookmarks:
                insert_query = """
                    INSERT INTO user_bookmarks (user_id, vocab_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, vocab_id) DO NOTHING
                """
                execute_batch(self.cursor, insert_query, bookmarks)
                self.conn.commit()
                print(f"   ✅ 收藏本迁移完成，处理 {len(bookmarks)} 条数据")
            else:
                print("   ⚠️  收藏本为空")

        except Exception as e:
            print(f"   ❌ 收藏本迁移失败: {e}")
            self.conn.rollback()

    def _migrate_daily_stats(self, user_id):
        """迁移每日统计"""
        print("\n   📊 迁移每日统计...")
        try:
            # 读取 Excel
            excel_path = os.path.join(self.server_dir, 'day_record.xlsx')
            df = pd.read_excel(excel_path, index_col=0, sheet_name='Sheet1')
            print(f"      读取到 {len(df)} 条统计记录")

            # 准备插入数据
            stats = []
            for idx, row in df.iterrows():
                date = pd.to_datetime(idx).date() if isinstance(idx, str) else idx
                total = int(row.get('total', 0))
                correct = int(row.get('ac', 0))
                wrong = int(row.get('wa', 0))
                stats.append((user_id, date, total, correct, wrong))

            # 批量插入
            if stats:
                insert_query = """
                    INSERT INTO user_daily_stats
                    (user_id, date, total_questions, correct_answers, wrong_answers)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, date) DO UPDATE
                    SET total_questions = EXCLUDED.total_questions,
                        correct_answers = EXCLUDED.correct_answers,
                        wrong_answers = EXCLUDED.wrong_answers
                """
                execute_batch(self.cursor, insert_query, stats)
                self.conn.commit()
                print(f"   ✅ 每日统计迁移完成，处理 {len(stats)} 条数据")
            else:
                print("   ⚠️  没有统计数据")

        except Exception as e:
            print(f"   ❌ 每日统计迁移失败: {e}")
            self.conn.rollback()

    def migrate_all(self, username='default_user'):
        """执行完整迁移流程"""
        print("=" * 60)
        print("🚀 开始数据迁移")
        print("=" * 60)

        if not self.connect_database():
            return False

        try:
            # 1. 迁移词汇表
            self.migrate_vocabulary()

            # 2. 迁移用户数据
            self.migrate_user_data(username)

            print("\n" + "=" * 60)
            print("✅ 数据迁移全部完成！")
            print("=" * 60)
            return True

        except Exception as e:
            print(f"\n❌ 迁移过程中出现错误: {e}")
            return False

        finally:
            self.close_database()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("📦 Excel 数据迁移工具")
    print("=" * 60)

    # 数据库配置
    db_config = {
        'host': input("请输入数据库地址 (默认 localhost): ").strip() or 'localhost',
        'port': int(input("请输入数据库端口 (默认 5432): ").strip() or '5432'),
        'database': input("请输入数据库名称 (默认 vocabulary_db): ").strip() or 'vocabulary_db',
        'user': input("请输入数据库用户名: ").strip(),
        'password': input("请输入数据库密码: ").strip()
    }

    # 用户名
    username = input("\n请输入要迁移的用户名 (默认 default_user): ").strip() or 'default_user'

    # 确认
    print("\n配置信息:")
    print(f"  数据库: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    print(f"  用户名: {username}")

    confirm = input("\n确认开始迁移? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ 迁移已取消")
        return

    # 执行迁移
    migrator = ExcelToOpenGaussMigrator(db_config)
    migrator.migrate_all(username)


if __name__ == '__main__':
    main()
