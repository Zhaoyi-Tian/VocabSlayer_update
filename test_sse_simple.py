#!/usr/bin/env python3
"""
简单的SSE测试
"""
import requests
import json
import time

def test_sse():
    """测试SSE连接"""
    server_url = "http://10.129.211.118:5000"
    task_id = "test-12345"
    url = f"{server_url}/api/progress/{task_id}"

    print(f"测试SSE连接: {url}")

    try:
        response = requests.get(
            url,
            headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            },
            stream=True,
            timeout=10
        )

        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            print("开始接收数据...")
            count = 0
            for line in response.iter_lines():
                if line:
                    # 解码
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    print(f"收到: {line}")
                    count += 1
                    if count > 10:  # 只显示前10行
                        break
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_sse()