"""
网络客户端模块
用于与服务器API通信，上传文档并生成题库
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List
import logging
from PyQt5.QtCore import QThread, pyqtSignal

# 配置日志
logger = logging.getLogger(__name__)

class NetworkBankManager:
    """网络题库管理器"""

    def __init__(self, server_url: str, timeout: int = 300):
        """
        初始化网络管理器

        Args:
            server_url: 服务器URL，如 http://10.129.211.118:5000
            timeout: 超时时间（秒）
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout

    def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = self.session.get(f"{self.server_url}/api/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"服务器健康检查失败: {e}")
            return False

    def upload_document(self,
                       file_path: str,
                       user_id: int,
                       bank_name: str,
                       description: str = "",
                       api_key: str = "",
                       chunk_size: int = 1000,
                       questions_per_chunk: int = 3,
                       progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        上传文档并生成题库

        Args:
            file_path: 文档路径
            user_id: 用户ID
            bank_name: 题库名称
            description: 描述
            api_key: DeepSeek API密钥
            chunk_size: 文本块大小
            questions_per_chunk: 每块题目数
            progress_callback: 进度回调函数

        Returns:
            处理结果字典
        """
        try:
            if progress_callback:
                progress_callback(10, "准备上传文件...")

            # 检查文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 准备文件上传
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}

                data = {
                    'user_id': user_id,
                    'bank_name': bank_name,
                    'description': description,
                    'api_key': api_key,
                    'chunk_size': chunk_size,
                    'questions_per_chunk': questions_per_chunk
                }

                if progress_callback:
                    progress_callback(20, "正在上传文件...")

                # 上传文件
                response = self.session.post(
                    f"{self.server_url}/api/upload",
                    files=files,
                    data=data
                )

                if progress_callback:
                    progress_callback(50, "服务器正在处理文档...")

                # 处理响应
                if response.status_code == 200:
                    result = response.json()

                    if result.get('success'):
                        if progress_callback:
                            progress_callback(100, "处理完成")
                        return result
                    else:
                        raise Exception(result.get('error', '未知错误'))
                else:
                    raise Exception(f"服务器错误: {response.status_code}")

        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            if progress_callback:
                progress_callback(0, f"错误: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_banks(self, user_id: int) -> List[Dict]:
        """获取用户的题库列表"""
        try:
            response = self.session.get(f"{self.server_url}/api/banks/{user_id}")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('banks', [])
            return []
        except Exception as e:
            logger.error(f"获取题库列表失败: {e}")
            return []

    def get_bank_info(self, bank_id: int) -> Optional[Dict]:
        """获取单个题库的信息"""
        try:
            response = self.session.get(f"{self.server_url}/api/banks/{bank_id}/info")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('bank_info')
            return None
        except Exception as e:
            logger.error(f"获取题库信息失败: {e}")
            return None

    def get_bank_questions(self, bank_id: int, user_id: int, limit: int = 20) -> List[Dict]:
        """获取题库的题目（不包含答案）"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/banks/{bank_id}/questions",
                params={'user_id': user_id, 'limit': limit}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('questions', [])
            return []
        except Exception as e:
            logger.error(f"获取题目失败: {e}")
            return []

    def get_bank_questions_with_answers(self, bank_id: int, user_id: int) -> List[Dict]:
        """获取题库的题目（包含答案）"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/banks/{bank_id}/questions_with_answers",
                params={'user_id': user_id}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('questions', [])
            return []
        except Exception as e:
            logger.error(f"获取题目（含答案）失败: {e}")
            return []

    def delete_bank(self, bank_id: int, user_id: int) -> bool:
        """删除题库"""
        try:
            response = self.session.delete(
                f"{self.server_url}/api/banks/{bank_id}",
                json={'user_id': user_id}
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            return False
        except Exception as e:
            logger.error(f"删除题库失败: {e}")
            return False

    def save_answer(self, user_id: int, question_id: int, is_correct: bool, answer_time: int = 0):
        """保存答题记录"""
        try:
            response = self.session.post(
                f"{self.server_url}/api/answers",
                json={
                    'user_id': user_id,
                    'question_id': question_id,
                    'is_correct': is_correct,
                    'answer_time': answer_time
                }
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            return False
        except Exception as e:
            logger.error(f"保存答案失败: {e}")
            return False

    def get_user_stats(self, user_id: int) -> Dict:
        """获取用户答题统计"""
        try:
            response = self.session.get(f"{self.server_url}/api/stats/{user_id}")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('stats', {})
            return {}
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}


class DocumentUploadThread(QThread):
    """文档上传线程"""

    # 信号定义
    progress_updated = pyqtSignal(int, str)      # 进度更新
    upload_completed = pyqtSignal(dict)           # 上传完成
    error_occurred = pyqtSignal(str)              # 发生错误

    def __init__(self,
                 network_manager: NetworkBankManager,
                 file_path: str,
                 user_id: int,
                 bank_name: str,
                 description: str = "",
                 api_key: str = "",
                 chunk_size: int = 1000,
                 questions_per_chunk: int = 3):
        """
        初始化上传线程

        Args:
            network_manager: 网络管理器实例
            file_path: 文件路径
            user_id: 用户ID
            bank_name: 题库名称
            description: 描述
            api_key: API密钥
            chunk_size: 块大小
            questions_per_chunk: 每块题目数
        """
        super().__init__()
        self.network_manager = network_manager
        self.file_path = file_path
        self.user_id = user_id
        self.bank_name = bank_name
        self.description = description
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.questions_per_chunk = questions_per_chunk
        self._cancelled = False

    def run(self):
        """执行上传"""
        try:
            result = self.network_manager.upload_document(
                file_path=self.file_path,
                user_id=self.user_id,
                bank_name=self.bank_name,
                description=self.description,
                api_key=self.api_key,
                chunk_size=self.chunk_size,
                questions_per_chunk=self.questions_per_chunk,
                progress_callback=self.on_progress
            )

            if not self._cancelled:
                self.upload_completed.emit(result)
        except Exception as e:
            if not self._cancelled:
                self.error_occurred.emit(str(e))

    def on_progress(self, percentage: int, status: str):
        """进度回调"""
        if not self._cancelled:
            self.progress_updated.emit(percentage, status)

    def cancel(self):
        """取消上传"""
        self._cancelled = True