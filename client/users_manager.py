import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def get_database_connection():
    """获取数据库连接"""
    try:
        from server.database_manager import DatabaseFactory
        # 获取项目根目录
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent.parent

        config_path = base_path / "config.json"
        db = DatabaseFactory.from_config_file(str(config_path))
        db.connect()
        return db
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return None


def user_exists(username: str) -> bool:
    """检查用户是否存在"""
    db = get_database_connection()
    if not db:
        return False

    try:
        if hasattr(db, 'conn'):  # OpenGauss
            query = db.conn.prepare("SELECT user_id FROM users WHERE username = $1")
            result = query(username)
            return len(result) > 0 if result else False
        else:
            return False
    except Exception as e:
        print(f"[ERROR] Failed to check user existence: {e}")
        return False


def authenticate_user(username: str, password: str) -> bool:
    """验证用户名和密码"""
    db = get_database_connection()
    if not db:
        print("[WARNING] Database not available, authentication failed")
        return False

    try:
        # 从数据库查询用户
        if hasattr(db, 'conn'):  # OpenGauss
            query = db.conn.prepare("SELECT password FROM users WHERE username = $1")
            result = query(username)
            if result and len(result) > 0:
                stored_password = result[0]['password']
                return stored_password == password
            return False
        else:
            print("[ERROR] Unsupported database type")
            return False
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        return False


def create_user(username: str, password: str) -> bool:
    """创建新用户"""
    db = get_database_connection()
    if not db:
        print("[WARNING] Database not available, cannot create user")
        return False

    try:
        # 在数据库中创建用户
        if hasattr(db, 'conn'):  # OpenGauss
            # 检查用户是否已存在
            check_query = db.conn.prepare("SELECT user_id FROM users WHERE username = $1")
            existing = check_query(username)
            if existing:
                print(f"[WARNING] User {username} already exists")
                return False

            # 创建新用户
            insert_query = db.conn.prepare("""
                INSERT INTO users (username, password)
                VALUES ($1, $2)
            """)
            insert_query(username, password)
            print(f"[DEBUG] User {username} created in database")
            return True
        else:
            print("[ERROR] Unsupported database type")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to create user: {e}")
        return False


# ===== 以下代码仅用于向后兼容，不再主动使用 =====

def get_data_dir() -> Path:
    """获取存储用户数据的目录路径（已废弃，仅用于兼容）"""
    if "USER_DATA_DIR" in os.environ:
        return Path(os.environ["USER_DATA_DIR"])

    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent

    data_dir = base_path / "user_data"
    return data_dir


def get_users_file() -> Path:
    """获取用户数据文件路径（已废弃，仅用于兼容）"""
    return get_data_dir() / "users.json"


def load_users() -> Dict[str, str]:
    """加载用户数据（已废弃，仅用于向后兼容）"""
    users_file = get_users_file()

    if not users_file.exists():
        # 不再自动创建文件
        return {}

    try:
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users: Dict[str, str]) -> None:
    """保存用户数据到文件（已废弃，不再使用）"""
    # 不再保存到本地文件
    print("[INFO] Local user file saving is deprecated, users are now stored in database")
    pass


# 向后兼容：保留原有的 users 变量（但不再自动创建文件）
users = {}