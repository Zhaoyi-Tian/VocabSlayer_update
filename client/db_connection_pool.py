"""
数据库连接池管理
提供全局的数据库连接复用机制
"""
from threading import Lock
from typing import Optional
from server.database_manager import DatabaseFactory


class DatabaseConnectionPool:
    """数据库连接池 - 单例模式"""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._connection = None
            self._connection_count = 0
            self._lock = Lock()
            self._initialized = True

    def get_connection(self):
        """获取数据库连接（复用）"""
        with self._lock:
            if self._connection is None:
                print("[DEBUG] Creating new database connection...")
                self._connection = DatabaseFactory.from_config_file('config.json')
                if self._connection:
                    success = self._connection.connect()
                    if not success:
                        print("[ERROR] Failed to connect to database")
                        self._connection = None
                        return None
                    print("[DEBUG] Database connection established")

            if self._connection:
                self._connection_count += 1
                print(f"[DEBUG] Connection reused (count: {self._connection_count})")

            return self._connection

    def release_connection(self):
        """释放连接引用"""
        with self._lock:
            if self._connection_count > 0:
                self._connection_count -= 1
                print(f"[DEBUG] Connection released (count: {self._connection_count})")

            # 可选：当没有使用时关闭连接
            # if self._connection_count == 0 and self._connection:
            #     self._connection.close()
            #     self._connection = None
            #     print("[DEBUG] Database connection closed")

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
                self._connection_count = 0
                print("[DEBUG] All database connections closed")


# 全局连接池实例
connection_pool = DatabaseConnectionPool()


class DatabaseConnection:
    """数据库连接上下文管理器"""

    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = connection_pool.get_connection()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            connection_pool.release_connection()
        return False