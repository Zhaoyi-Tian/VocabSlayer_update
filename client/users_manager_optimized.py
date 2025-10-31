import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


class DatabaseManager:
    """数据库连接管理器 - 单例模式"""
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self):
        """获取数据库连接（复用现有连接）"""
        if self._connection is None:
            try:
                from server.database_manager import DatabaseFactory
                # 获取项目根目录
                if getattr(sys, 'frozen', False):
                    base_path = Path(sys.executable).parent
                else:
                    base_path = Path(__file__).parent.parent

                config_path = base_path / "config.json"
                db = DatabaseFactory.from_config_file(str(config_path))
                if db.connect():
                    self._connection = db
                    print("[DEBUG] Database connection established")
                else:
                    return None
            except Exception as e:
                print(f"[ERROR] Failed to connect to database: {e}")
                return None
        else:
            print("[DEBUG] Reusing existing database connection")
        return self._connection

    def close_connection(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None


# 全局数据库管理器实例
db_manager = DatabaseManager()


def verify_user(username: str, password: str) -> Tuple[bool, bool]:
    """
    一次性验证用户存在性和密码
    返回: (user_exists, password_correct)
    """
    db = db_manager.get_connection()
    if not db:
        print("[WARNING] Database not available, authentication failed")
        return False, False

    try:
        if hasattr(db, 'conn'):  # OpenGauss
            query = db.conn.prepare("SELECT password FROM users WHERE username = $1")
            result = query(username)
            if result and len(result) > 0:
                stored_password = result[0]['password']
                return True, stored_password == password
            return False, False
        else:
            # Excel模式下，检查用户文件
            print("[DEBUG] Using Excel mode for authentication")
            return False, False
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        return False, False


def user_exists(username: str) -> bool:
    """检查用户是否存在（保留向后兼容）"""
    user_exists, _ = verify_user(username, "")
    return user_exists


def authenticate_user(username: str, password: str) -> bool:
    """验证用户名和密码（保留向后兼容）"""
    _, password_correct = verify_user(username, password)
    return password_correct


def create_user(username: str, password: str) -> bool:
    """创建新用户"""
    db = db_manager.get_connection()
    if not db:
        print("[WARNING] Database not available, cannot create user")
        return False

    try:
        # 在数据库中创建用户
        if hasattr(db, 'conn'):  # OpenGauss
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


def cleanup():
    """清理资源"""
    db_manager.close_connection()


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