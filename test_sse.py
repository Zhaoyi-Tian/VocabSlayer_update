#!/usr/bin/env python3
"""
测试SSE连接
"""
import requests
import json
import time

def test_sse_connection(task_id):
    """测试SSE连接"""
    server_url = "http://10.129.211.118:5000"
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
            timeout=30,
            stream=True
        )

        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            print("开始接收SSE数据...")
            for line in response.iter_lines():
                if line:
                    # 解码
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')

                    print(f"收到: {line}")

                    # 解析数据
                    if line.startswith('data: '):
                        data = line[6:]
                        if data.strip():
                            try:
                                progress_data = json.loads(data)
                                print(f"  解析结果: {progress_data}")
                            except json.JSONDecodeError as e:
                                print(f"  JSON解析错误: {e}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    # 使用示例task_id测试
    test_sse_connection("test-task-id")