"""
用户数据管理模块
负责管理每个用户的独立数据存储，包括收藏本、复习本、学习记录等
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class UserDataManager:
    """用户数据管理器"""

    def __init__(self, username: str):
        """
        初始化用户数据管理器

        Args:
            username: 用户名
        """
        self.username = username

        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.user_dir = os.path.join(root_dir, 'user', username)

        # 确保用户目录存在
        os.makedirs(self.user_dir, exist_ok=True)

        # 定义各个数据文件路径
        self.profile_file = os.path.join(self.user_dir, 'profile.json')
        self.book_file = os.path.join(self.user_dir, 'book.json')
        self.review_file = os.path.join(self.user_dir, 'review.json')
        self.record_file = os.path.join(self.user_dir, 'record.json')
        self.day_stats_file = os.path.join(self.user_dir, 'day_stats.json')
        self.chat_history_file = os.path.join(self.user_dir, 'chat_history.json')

        # 初始化数据文件
        self._init_data_files()

    def _init_data_files(self):
        """初始化所有数据文件（如果不存在）"""
        # 用户配置
        if not os.path.exists(self.profile_file):
            default_profile = {
                "username": self.username,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "last_login": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "preferences": {
                    "main_language": "Chinese",
                    "study_language": "English",
                    "default_level": 2
                }
            }
            self._save_json(self.profile_file, default_profile)
        else:
            # 验证现有文件，如果损坏则重新初始化
            try:
                self._load_json(self.profile_file)
            except Exception:
                default_profile = {
                    "username": self.username,
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "last_login": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "preferences": {
                        "main_language": "Chinese",
                        "study_language": "English",
                        "default_level": 2
                    }
                }
                self._save_json(self.profile_file, default_profile)

        # 收藏本
        if not os.path.exists(self.book_file):
            self._save_json(self.book_file, {"words": []})

        # 复习本
        if not os.path.exists(self.review_file):
            self._save_json(self.review_file, {"words": []})

        # 学习记录（每个单词的学习进度）
        if not os.path.exists(self.record_file):
            self._save_json(self.record_file, {"words": {}})

        # 每日统计
        if not os.path.exists(self.day_stats_file):
            self._save_json(self.day_stats_file, {"daily_records": {}})

        # 聊天历史（如果不存在）
        if not os.path.exists(self.chat_history_file):
            self._save_json(self.chat_history_file, [])

    def _save_json(self, filepath: str, data: Any):
        """保存JSON数据"""
        # 转换numpy/pandas数据类型为Python原生类型
        data = self._convert_to_json_serializable(data)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _convert_to_json_serializable(self, obj):
        """递归转换对象为JSON可序列化类型"""
        import numpy as np
        import pandas as pd

        if isinstance(obj, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj

    def _load_json(self, filepath: str) -> Any:
        """加载JSON数据，带容错处理"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    # 文件为空，返回默认值
                    return self._get_default_data(filepath)
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            # JSON 解析错误，备份损坏文件并返回默认值
            print(f"警告: {filepath} 格式错误，将重新初始化。错误: {e}")
            # 备份损坏的文件
            if os.path.exists(filepath):
                backup_path = filepath + '.backup'
                import shutil
                shutil.copy2(filepath, backup_path)
                print(f"已备份损坏文件到: {backup_path}")
            return self._get_default_data(filepath)
        except FileNotFoundError:
            return self._get_default_data(filepath)

    def _get_default_data(self, filepath: str):
        """根据文件路径返回默认数据结构"""
        if 'record.json' in filepath:
            return {"words": {}}
        elif 'book.json' in filepath or 'review.json' in filepath:
            return {"words": []}
        elif 'day_stats.json' in filepath:
            return {"daily_records": {}}
        elif 'chat_history.json' in filepath:
            return []
        elif 'profile.json' in filepath:
            return {
                "username": self.username,
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

    # ==================== 用户配置管理 ====================

    def get_profile(self) -> Dict:
        """获取用户配置"""
        return self._load_json(self.profile_file)

    def update_profile(self, updates: Dict):
        """更新用户配置"""
        profile = self.get_profile()
        profile.update(updates)
        profile['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_json(self.profile_file, profile)

    def get_preference(self, key: str, default=None):
        """获取用户偏好设置"""
        profile = self.get_profile()
        return profile.get('preferences', {}).get(key, default)

    def set_preference(self, key: str, value: Any):
        """设置用户偏好"""
        profile = self.get_profile()
        if 'preferences' not in profile:
            profile['preferences'] = {}
        profile['preferences'][key] = value
        self._save_json(self.profile_file, profile)

    # ==================== 收藏本管理 ====================

    def get_book_words(self) -> List[Dict]:
        """获取收藏本中的所有单词"""
        data = self._load_json(self.book_file)
        return data.get('words', [])

    def add_to_book(self, word_data: Dict) -> bool:
        """
        添加单词到收藏本

        Args:
            word_data: 单词数据，应包含 id, Chinese, English, Japanese, level 等字段

        Returns:
            是否成功添加（如果已存在则返回False）
        """
        data = self._load_json(self.book_file)
        words = data.get('words', [])

        # 检查是否已存在
        word_id = word_data.get('id')
        if any(w.get('id') == word_id for w in words):
            return False

        # 添加时间戳
        word_data['added_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        words.append(word_data)

        data['words'] = words
        self._save_json(self.book_file, data)
        return True

    def remove_from_book(self, word_id: int) -> bool:
        """从收藏本移除单词"""
        data = self._load_json(self.book_file)
        words = data.get('words', [])

        original_len = len(words)
        words = [w for w in words if w.get('id') != word_id]

        if len(words) < original_len:
            data['words'] = words
            self._save_json(self.book_file, data)
            return True
        return False

    def is_in_book(self, word_id: int) -> bool:
        """检查单词是否在收藏本中"""
        words = self.get_book_words()
        return any(w.get('id') == word_id for w in words)

    # ==================== 复习本管理 ====================

    def get_review_words(self) -> List[Dict]:
        """获取复习本中的所有单词"""
        data = self._load_json(self.review_file)
        return data.get('words', [])

    def add_to_review(self, word_data: Dict, weight: float = 10.0) -> bool:
        """
        添加单词到复习本

        Args:
            word_data: 单词数据
            weight: 权重（越大表示越需要复习）

        Returns:
            是否成功添加
        """
        data = self._load_json(self.review_file)
        words = data.get('words', [])

        word_id = word_data.get('id')

        # 如果已存在，只更新权重
        for w in words:
            if w.get('id') == word_id:
                w['weight'] = weight
                w['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_json(self.review_file, data)
                return True

        # 不存在则添加
        word_data['weight'] = weight
        word_data['added_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        words.append(word_data)

        data['words'] = words
        self._save_json(self.review_file, data)
        return True

    def update_review_weight(self, word_id: int, multiplier: float):
        """
        更新复习本中单词的权重

        Args:
            word_id: 单词ID
            multiplier: 权重乘数（答对用0.8，答错用1.2）
        """
        data = self._load_json(self.review_file)
        words = data.get('words', [])

        for w in words:
            if w.get('id') == word_id:
                w['weight'] = w.get('weight', 10.0) * multiplier
                w['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

        data['words'] = words
        self._save_json(self.review_file, data)

    def remove_from_review(self, word_id: int) -> bool:
        """从复习本移除单词"""
        data = self._load_json(self.review_file)
        words = data.get('words', [])

        original_len = len(words)
        words = [w for w in words if w.get('id') != word_id]

        if len(words) < original_len:
            data['words'] = words
            self._save_json(self.review_file, data)
            return True
        return False

    # ==================== 学习记录管理 ====================

    def get_word_record(self, word_id: int) -> Dict:
        """获取单词的学习记录"""
        data = self._load_json(self.record_file)
        words = data.get('words', {})
        return words.get(str(word_id), {
            'id': word_id,
            'star': 0,  # 熟练度星级
            'correct_count': 0,
            'wrong_count': 0,
            'last_studied': None
        })

    def update_word_record(self, word_id: int, is_correct: bool):
        """
        更新单词的学习记录

        Args:
            word_id: 单词ID
            is_correct: 是否答对
        """
        data = self._load_json(self.record_file)
        words = data.get('words', {})

        key = str(word_id)
        if key not in words:
            words[key] = {
                'id': word_id,
                'star': 0,
                'correct_count': 0,
                'wrong_count': 0,
                'last_studied': None
            }

        record = words[key]

        if is_correct:
            record['correct_count'] += 1
            # 星级最多3星
            if record['star'] < 3:
                record['star'] += 1
        else:
            record['wrong_count'] += 1

        record['last_studied'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data['words'] = words
        self._save_json(self.record_file, data)

    def get_all_records(self) -> Dict[str, Dict]:
        """获取所有单词的学习记录"""
        data = self._load_json(self.record_file)
        return data.get('words', {})

    # ==================== 每日统计管理 ====================

    def update_day_stats(self, correct: int, wrong: int):
        """
        更新今天的统计数据

        Args:
            correct: 正确题数
            wrong: 错误题数
        """
        today = datetime.today().strftime('%Y-%m-%d')
        data = self._load_json(self.day_stats_file)
        daily_records = data.get('daily_records', {})

        if today not in daily_records:
            daily_records[today] = {
                'date': today,
                'correct': 0,
                'wrong': 0,
                'total': 0
            }

        daily_records[today]['correct'] += correct
        daily_records[today]['wrong'] += wrong
        daily_records[today]['total'] += correct + wrong

        data['daily_records'] = daily_records
        self._save_json(self.day_stats_file, data)

    def get_day_stats(self, date: Optional[str] = None) -> Dict:
        """
        获取指定日期的统计（默认今天）

        Args:
            date: 日期字符串 (YYYY-MM-DD)，None表示今天

        Returns:
            统计数据字典
        """
        if date is None:
            date = datetime.today().strftime('%Y-%m-%d')

        data = self._load_json(self.day_stats_file)
        daily_records = data.get('daily_records', {})

        return daily_records.get(date, {
            'date': date,
            'correct': 0,
            'wrong': 0,
            'total': 0
        })

    def get_all_day_stats(self) -> Dict[str, Dict]:
        """获取所有日期的统计"""
        data = self._load_json(self.day_stats_file)
        return data.get('daily_records', {})

    def get_stats_summary(self) -> Dict:
        """获取学习统计摘要"""
        all_stats = self.get_all_day_stats()

        total_correct = sum(s.get('correct', 0) for s in all_stats.values())
        total_wrong = sum(s.get('wrong', 0) for s in all_stats.values())
        total_words = total_correct + total_wrong

        return {
            'total_days': len(all_stats),
            'total_words_learned': total_words,
            'total_correct': total_correct,
            'total_wrong': total_wrong,
            'accuracy': total_correct / total_words * 100 if total_words > 0 else 0,
            'book_count': len(self.get_book_words()),
            'review_count': len(self.get_review_words())
        }

    # ==================== 数据转换工具 ====================

    def convert_dataframe_to_dict(self, df: pd.DataFrame, index_name: int) -> Dict:
        """
        将 Pandas DataFrame 的一行转换为字典格式

        Args:
            df: DataFrame
            index_name: 索引值

        Returns:
            单词数据字典
        """
        row = df.loc[index_name]
        return {
            'id': index_name,
            'Chinese': row.get('Chinese', ''),
            'English': row.get('English', ''),
            'Japanese': row.get('Japanese', ''),
            'level': int(row.get('level', 2))
        }

    def export_to_json(self, output_dir: Optional[str] = None):
        """
        导出所有用户数据为JSON（备份用）

        Args:
            output_dir: 输出目录，默认为用户目录
        """
        if output_dir is None:
            output_dir = self.user_dir

        export_data = {
            'username': self.username,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'profile': self.get_profile(),
            'book': self.get_book_words(),
            'review': self.get_review_words(),
            'records': self.get_all_records(),
            'day_stats': self.get_all_day_stats()
        }

        export_file = os.path.join(output_dir, f'{self.username}_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        self._save_json(export_file, export_data)

        return export_file
