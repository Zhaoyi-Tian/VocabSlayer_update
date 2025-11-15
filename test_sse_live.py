#!/usr/bin/env python3
"""
实时测试SSE
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VocabSlayer_update_servier'))

import requests
import json
import time
from progress_manager import progress_manager
import threading

def create_test_task():
    """创建测试任务"""
    task_id = f"live-test-{int(time.time())}"
    progress_manager.create_task(task_id, "test.pdf", 1)
    return task_id

def send_updates(task_id):
    """发送进度更新"""
    messages = [
        {'progress': 5, 'message': '开始解析文档...'},
        {'progress': 10, 'message': '正在读取PDF...'},
        {'progress': 20, 'message': 'PDF解析完成，共 100 页'},
        {'progress': 30, 'message': '正在清洗文本...'},
        {'progress': 50, 'message': '正在生成题目...'},
        {'progress': 80, 'message': '已生成 50 道题目...'},
        {'progress': 100, 'message': '处理完成！'}
    ]

    for i, msg in enumerate(messages):
        time.sleep(1)
        progress_manager.update_progress(
            task_id=task_id,
            status='processing' if i < len(messages) - 1 else 'completed',
            progress=msg['progress'],
            message=msg['message'],
            current_step=f'step_{i+1}'
        )
        print(f"发送更新: {msg['progress']}% - {msg['message']}")

def test_sse():
    """测试SSE"""
    task_id = create_test_task()
    print(f"测试task_id: {task_id}")

    # 启动发送更新的线程
    sender_thread = threading.Thread(target=send_updates, args=(task_id,))
    sender_thread.daemon = True
    sender_thread.start()

    # 等待一下让第一个消息发送
    time.sleep(0.5)

    # 连接SSE
    url = f"http://10.129.211.118:5000/api/progress/{task_id}"
    print(f"连接SSE: {url}")

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
        print(f"Content-Type: {response.headers.get('Content-Type', 'None')}")

        if response.status_code == 200:
            print("\n接收SSE数据:")
            print("-" * 50)
            count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"收到: {line}")
                    count += 1
                    if count > 20:
                        break
            print("-" * 50)
        else:
            print(f"错误: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"连接错误: {e}")

if __name__ == "__main__":
    test_sse()