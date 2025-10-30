# -*- coding: utf-8 -*-
"""
数据库配置模块 - 硬编码数据库连接信息
不再依赖 config.json 文件
"""

# 数据库连接配置
DATABASE_CONFIG = {
    "database_type": "opengauss",
    "database_config": {
        "host": "10.129.211.118",
        "port": 5432,
        "database": "vocabulary_db",
        "user": "vocabuser",
        "password": "OpenEuler123!"
    }
}

def get_database_config():
    """获取数据库配置"""
    return DATABASE_CONFIG
