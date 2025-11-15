#!/usr/bin/env python3
"""
测试修复的客户端
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.network_client import NetworkBankManager

def test_delete_bank():
    """测试删除题库功能"""
    # 服务器URL
    server_url = "http://10.129.211.118:5000"

    # 创建网络管理器
    manager = NetworkBankManager(server_url)

    # 测试删除题库
    bank_id = 40  # 测试题库ID
    user_id = 1   # 测试用户ID

    print(f"测试删除题库 bank_id={bank_id}, user_id={user_id}")

    # 检查服务器健康状态
    if manager.check_server_health():
        print("✓ 服务器连接正常")

        # 测试删除
        success = manager.delete_bank(bank_id, user_id)
        if success:
            print("✓ 删除成功")
        else:
            print("✗ 删除失败")
    else:
        print("✗ 服务器连接失败")

if __name__ == "__main__":
    test_delete_bank()