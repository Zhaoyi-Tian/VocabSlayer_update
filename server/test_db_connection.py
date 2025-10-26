#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database_manager import DatabaseFactory

def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("🧪 测试 VocabSlayer 数据库连接")
    print("=" * 60)

    try:
        # 从配置文件创建数据库连接
        db = DatabaseFactory.from_config_file('config.json')

        print("\n1️⃣  连接数据库...")
        if not db.connect():
            print("❌ 连接失败")
            return False
        print("✅ 数据库连接成功")

        print("\n2️⃣  测试查询词汇表...")
        vocab = db.get_vocabulary()
        print(f"✅ 词汇总数: {len(vocab)} 条")

        print("\n3️⃣  测试查询用户数据 (tianzhaoyi)...")
        records = db.get_user_records('tianzhaoyi')
        print(f"✅ 学习记录: {len(records)} 条")

        review_list = db.get_review_list('tianzhaoyi')
        print(f"✅ 复习本: {len(review_list)} 条")

        bookmarks = db.get_bookmarks('tianzhaoyi')
        print(f"✅ 收藏本: {len(bookmarks)} 条")

        daily_stats = db.get_daily_stats('tianzhaoyi')
        print(f"✅ 每日统计: {len(daily_stats)} 条")

        print("\n4️⃣  测试按等级查询词汇...")
        level1 = db.get_vocabulary(level=1)
        level2 = db.get_vocabulary(level=2)
        level3 = db.get_vocabulary(level=3)
        print(f"✅ Level 1: {len(level1)} 条")
        print(f"✅ Level 2: {len(level2)} 条")
        print(f"✅ Level 3: {len(level3)} 条")

        print("\n5️⃣  测试数据写入...")
        # 测试更新学习记录
        db.update_user_record('tianzhaoyi', 1, star=3)
        print("✅ 更新学习记录成功")

        print("\n6️⃣  关闭连接...")
        db.close()
        print("✅ 连接已关闭")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！数据库配置正确！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_connection()
