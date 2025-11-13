# -*- coding: utf-8 -*-
"""
网络连接测试脚本
"""
import socket
import telnetlib
import time

def test_network(host, port):
    print(f"测试网络连接到 {host}:{port}")

    # 测试TCP连接
    print("1. 测试TCP连接...")
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10秒超时
        result = sock.connect_ex((host, port))
        sock.close()
        connect_time = time.time() - start_time

        if result == 0:
            print(f"   ✓ TCP连接成功！耗时: {connect_time:.2f}秒")
        else:
            print(f"   ✗ TCP连接失败！错误码: {result}")
            return False
    except Exception as e:
        print(f"   ✗ TCP连接异常：{e}")
        return False

    # 测试telnet
    print("2. 测试telnet连接...")
    try:
        start_time = time.time()
        tn = telnetlib.Telnet(host, port, timeout=10)
        tn.close()
        telnet_time = time.time() - start_time
        print(f"   ✓ Telnet连接成功！耗时: {telnet_time:.2f}秒")
    except Exception as e:
        print(f"   ✗ Telnet连接失败：{e}")
        return False

    return True

if __name__ == "__main__":
    # 从配置文件读取数据库信息
    host = "10.129.211.118"
    port = 5432

    print("=" * 50)
    print("网络连接测试")
    print("=" * 50)

    success = test_network(host, port)

    print("\n" + "=" * 50)
    if success:
        print("网络连接正常！")
    else:
        print("网络连接存在问题，请检查：")
        print("1. 服务器IP地址是否正确")
        print("2. 端口5432是否开放")
        print("3. 防火墙是否阻止连接")
        print("4. 网络是否通畅")