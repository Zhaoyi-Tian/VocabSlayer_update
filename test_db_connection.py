# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
"""
import sys
import time
from server.database_manager import DatabaseFactory

def test_connection():
    print("开始测试数据库连接...")

    try:
        # 创建数据库实例
        print("1. 创建数据库实例...")
        db = DatabaseFactory.from_config_file('config.json')

        # 测试连接
        print("2. 尝试连接数据库...")
        start_time = time.time()
        db.connect()
        connect_time = time.time() - start_time
        print(f"   ✓ 连接成功！耗时: {connect_time:.2f}秒")

        # 测试基本查询
        print("3. 测试基本查询...")
        start_time = time.time()
        vocab = db.get_vocabulary()
        query_time = time.time() - start_time
        print(f"   ✓ 查询成功！获取到 {len(vocab)} 条词汇，耗时: {query_time:.2f}秒")

        # 测试用户查询
        print("4. 测试用户查询...")
        username = "tianzhaoyi"  # 使用示例用户
        start_time = time.time()
        records = db.get_user_records(username)
        query_time = time.time() - start_time
        print(f"   ✓ 查询成功！获取到 {len(records)} 条学习记录，耗时: {query_time:.2f}秒")

        # 关闭连接
        print("5. 关闭连接...")
        db.close()
        print("   ✓ 连接已关闭")

        print("\n✅ 所有测试通过！数据库连接正常。")
        return True

    except Exception as e:
        print(f"\n❌ 连接失败！错误信息：{e}")
        print(f"错误类型：{type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置输出立即刷新
    import os
    os.environ['PYTHONUNBUFFERED'] = '1'

    test_connection()