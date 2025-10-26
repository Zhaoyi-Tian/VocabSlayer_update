"""
清理用户目录中损坏的JSON文件

运行此脚本会：
1. 检查所有用户目录下的JSON文件
2. 备份损坏的文件
3. 重新初始化为正确的格式
"""
import os
import json
import shutil
from datetime import datetime

def clean_user_data():
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_base_dir = os.path.join(root_dir, 'user')

    if not os.path.exists(user_base_dir):
        print("用户目录不存在")
        return

    # 遍历所有用户目录
    for username in os.listdir(user_base_dir):
        user_dir = os.path.join(user_base_dir, username)
        if not os.path.isdir(user_dir):
            continue

        print(f"\n检查用户: {username}")

        # 检查所有JSON文件
        json_files = [
            'profile.json',
            'book.json',
            'review.json',
            'record.json',
            'day_stats.json',
            'chat_history.json'
        ]

        for filename in json_files:
            filepath = os.path.join(user_dir, filename)

            if not os.path.exists(filepath):
                print(f"  - {filename}: 不存在，跳过")
                continue

            # 尝试加载JSON
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError("文件为空")
                    data = json.loads(content)
                print(f"  ✓ {filename}: 格式正确")
            except Exception as e:
                print(f"  ✗ {filename}: 格式错误 - {e}")

                # 备份损坏的文件
                backup_path = filepath + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                shutil.copy2(filepath, backup_path)
                print(f"    已备份到: {backup_path}")

                # 重新初始化为正确格式
                default_data = get_default_data(filename, username)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                print(f"    已重新初始化")

def get_default_data(filename, username):
    """返回默认数据结构"""
    if filename == 'record.json':
        return {"words": {}}
    elif filename in ['book.json', 'review.json']:
        return {"words": []}
    elif filename == 'day_stats.json':
        return {"daily_records": {}}
    elif filename == 'chat_history.json':
        return []
    elif filename == 'profile.json':
        return {
            "username": username,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "last_login": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "preferences": {
                "main_language": "Chinese",
                "study_language": "English",
                "default_level": 2
            }
        }
    else:
        return {}

if __name__ == '__main__':
    print("=" * 50)
    print("开始清理用户数据...")
    print("=" * 50)
    clean_user_data()
    print("\n" + "=" * 50)
    print("清理完成！")
    print("=" * 50)
