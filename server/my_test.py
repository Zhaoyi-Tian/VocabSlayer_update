import io
import os
from random import randint, random, shuffle, sample
from time import time
from datetime import datetime
# TODO 2: 使用datetime库获取当前时间,以便于后续数据记录
import pandas as pd
import matplotlib.pyplot as plt
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QImage
from matplotlib.backends.backend_template import FigureCanvas
from matplotlib.figure import Figure
from openai import OpenAI

from server.database_manager import DatabaseFactory

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文黑体
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号
# 设置工作目录为当前脚本所在目录
# TODO Warning fixed 1: 使用相对路径,不然在不同机器下运行的情况会有所差别,由于存储路径不同可能出现不能运行的情况.下面将对应数据保存至文件夹"Data"中
class VocabularyLearningSystem:
    class RecordAC:
        def __init__(self):
            self.ac = 0  # 答对题目数
            self.wa = 0  # 答错题目数
            self.time = []  # 耗时记录
            self.is_correct = []  # 新增：记录每题正误
            self.data=datetime.today().strftime('%Y-%m-%d')  # 新增：记录数据生成时间

        def add_ac(self, t):
            self.ac += 1
            self.time.append(t)
            self.is_correct.append(True)  # 正确

        def add_wa(self, t):
            self.wa += 1
            self.time.append(t)
            self.is_correct.append(False)  # 错误

    def __init__(self, username: str = None):
        """
        初始化词汇学习系统

        Args:
            username: 用户名，如果提供则使用用户独立数据
        """
        # 初始化数据
        # 获取项目根目录（server的父目录）
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root_dir, 'config.json')

        self.username = username

        # 使用数据库工厂创建数据库连接
        self.db = DatabaseFactory.from_config_file(config_path)
        if not self.db.connect():
            raise RuntimeError("无法连接到数据库")

        self.today = 0

        # 从数据库加载词汇数据（所有用户共用）
        self.df0 = self.db.get_vocabulary()
        self.df1 = self.db.get_vocabulary()

        # 统一列名为大写（与原Excel格式兼容）
        column_mapping = {
            'chinese': 'Chinese',
            'english': 'English',
            'japanese': 'Japanese'
        }
        rename_dict_0 = {k: v for k, v in column_mapping.items() if k in self.df0.columns}
        rename_dict_1 = {k: v for k, v in column_mapping.items() if k in self.df1.columns}
        self.df0 = self.df0.rename(columns=rename_dict_0)
        self.df1 = self.df1.rename(columns=rename_dict_1)

        # 设置索引并添加id列（兼容现有代码）
        if 'vocab_id' in self.df0.columns:
            self.df0 = self.df0.set_index('vocab_id')
            self.df1 = self.df1.set_index('vocab_id')

        # 添加id列作为索引的副本（兼容现有代码中使用word['id']的地方）
        self.df1['id'] = self.df1.index

        # 从数据库加载用户数据
        if username:
            self._load_user_data_from_db()
        else:
            # 创建空DataFrame
            self.df2 = pd.DataFrame(columns=['star'])
            self.df2.index.name = 'vocab_id'
            self.df3 = pd.DataFrame(columns=['chinese', 'english', 'japanese', 'level', 'weight'])
            self.df3.index.name = 'vocab_id'
            self.df4 = pd.DataFrame(columns=['chinese', 'english', 'japanese', 'level'])
            self.df4.index.name = 'vocab_id'
            self.df5 = pd.DataFrame(columns=['total_questions', 'correct_answers', 'wrong_answers'])
            self.df5.index.name = 'date'

        self.mainlanguage = None
        self.studylanguage = None
        self.record = self.RecordAC()
        self.current_level_df = None

        # 保存路径供后续使用
        self.root_dir = root_dir

    def _load_user_data_from_db(self):
        """从数据库加载用户数据到DataFrame格式"""
        # 学习记录
        df_records = self.db.get_user_records(self.username)
        if not df_records.empty and 'vocab_id' in df_records.columns:
            self.df2 = df_records[['vocab_id', 'star']].set_index('vocab_id')
        else:
            self.df2 = pd.DataFrame(columns=['star'])
            self.df2.index.name = 'vocab_id'

        # 复习本
        df_review = self.db.get_review_list(self.username)
        if not df_review.empty and 'vocab_id' in df_review.columns:
            # 将数据库列名映射为代码中使用的大写列名
            column_mapping = {
                'chinese': 'Chinese',
                'english': 'English',
                'japanese': 'Japanese',
                'vocab_id': 'vocab_id',
                'level': 'level',
                'weight': 'weight'
            }
            # 只重命名存在的列
            rename_dict = {k: v for k, v in column_mapping.items() if k in df_review.columns}
            self.df3 = df_review.rename(columns=rename_dict)
            if 'vocab_id' in self.df3.columns:
                self.df3 = self.df3.set_index('vocab_id')
        else:
            self.df3 = pd.DataFrame(columns=['Chinese', 'English', 'Japanese', 'level', 'weight'])
            self.df3.index.name = 'vocab_id'

        # 收藏本
        df_bookmarks = self.db.get_bookmarks(self.username)
        if not df_bookmarks.empty and 'vocab_id' in df_bookmarks.columns:
            column_mapping = {
                'chinese': 'Chinese',
                'english': 'English',
                'japanese': 'Japanese',
                'vocab_id': 'vocab_id',
                'level': 'level'
            }
            rename_dict = {k: v for k, v in column_mapping.items() if k in df_bookmarks.columns}
            self.df4 = df_bookmarks.rename(columns=rename_dict)
            if 'vocab_id' in self.df4.columns:
                self.df4 = self.df4.set_index('vocab_id')
        else:
            self.df4 = pd.DataFrame(columns=['Chinese', 'English', 'Japanese', 'level'])
            self.df4.index.name = 'vocab_id'

        # 每日统计
        df_daily = self.db.get_daily_stats(self.username)
        if not df_daily.empty:
            self.df5 = df_daily.rename(columns={
                'correct_answers': 'ac',
                'wrong_answers': 'wa',
                'total_questions': 'total'
            })
            if 'date' in self.df5.columns:
                self.df5 = self.df5.set_index('date')
        else:
            self.df5 = pd.DataFrame(columns=['total', 'ac', 'wa'])
            self.df5.index.name = 'date'

    def choose_level(self,n):
        """设置题目难度等级"""
        self.current_level_df = self.df0[self.df0['level'] == n]
        return self.current_level_df

    def set_languages(self,mainlanguage,studylanguage):
        """设置学习语言"""
        self.mainlanguage = mainlanguage
        self.studylanguage = studylanguage

    def _choose_word(self):
        """内部方法：根据记忆曲线选择单词"""
        n = len(self.df1)
        if n == 0:
            raise ValueError("词库为空，无法选择单词")

        # 尝试最多10次，避免无限递归
        max_attempts = 10
        for attempt in range(max_attempts):
            id0 = n * random()
            id00 = int(id0)
            word = self.df1.iloc[id00]
            id1 = int(word['id'])

            # 检查该单词是否有学习记录
            if id1 in self.df2.index:
                record1 = int(self.df2.loc[id1, 'star'])
            else:
                # 如果没有记录，初始化为0星
                record1 = 0
                # 为新单词创建记录（添加到df2以便后续查询）
                self.df2.loc[id1] = {'star': 0}

            # TODO 3 简化链式比较,使用Python风格的比较方式
            if id1 >= id0 >= id1 - 1 + record1 / 3:
                return word

        # 如果10次都没选中，直接返回最后一个
        return word
    def choose_word(self):
        """加权随机从复习本中选择单词"""
        n = len(self.df3)

        # 如果复习本为空，抛出异常
        if n == 0:
            raise ValueError("复习本为空，无法选择单词")

        # 假设用 weight 字段做权重，weight 越大越需要复习
        weights = []
        for i in range(n):
            weight = self.df3.iloc[i]['weight']
            # 转换 Decimal 为 float，并防止负数权重
            weights.append(float(max(weight, 0.1)))

        # 归一化权重
        total = sum(weights)
        if total == 0:
            # 如果所有权重都是0，使用均匀分布
            weights = [1.0 / n] * n
        else:
            weights = [w / total for w in weights]

        # 用 random.choices 加权抽取
        import random
        idx = random.choices(range(n), weights=weights, k=1)[0]
        word = self.df3.iloc[idx]
        return word

    def _generate_options(self, correct_answer, language):
        """生成选择题选项"""
        options = [correct_answer]
        while len(options) < 4:
            random_word = self.df1.sample(1).iloc[0]
            candidate = random_word[language]
            if candidate not in options:
                options.append(candidate)
        shuffle(options)
        return {
            'A': options[0],
            'B': options[1],
            'C': options[2],
            'D': options[3]
        }, chr(65 + options.index(correct_answer))

    def generate_question(self):
        """生成题目"""
        word = self._choose_word()
        question_type = randint(0, 2)

        if question_type == 0:  # 外译中
            question = f"{word[self.mainlanguage]}的{self.studylanguage}是什么？"
            options, answer = self._generate_options(word[self.studylanguage], self.studylanguage)
        elif question_type == 1:  # 中译外
            question = f"{word[self.studylanguage]}的{self.mainlanguage}是什么？"
            options, answer = self._generate_options(word[self.mainlanguage], self.mainlanguage)
        else:  # 判断题
            random_word = self.df1.sample(1).iloc[0]
            is_correct = random() > 0.5
            target_word = word if is_correct else random_word
            question = f"判断{target_word[self.mainlanguage]}的{self.studylanguage}是否为{word[self.studylanguage]}？"
            options = {'A': '是', 'C': '否'}
            answer = 'A' if is_correct else 'C'

        return question, options, answer, word
    def generate_review_question(self):
        """生成单个复习题目"""
        word = self.choose_word()
        question_type = randint(0, 2)

        if question_type == 0:  # 外译中
            question = f"{word[self.mainlanguage]}的{self.studylanguage}是什么？"
            options, answer = self._generate_options(word[self.studylanguage], self.studylanguage)
        elif question_type == 1:  # 中译外
            question = f"{word[self.studylanguage]}的{self.mainlanguage}是什么？"
            options, answer = self._generate_options(word[self.mainlanguage], self.mainlanguage)
        else:  # 判断题
            random_word = self.df1.sample(1).iloc[0]
            is_correct = random() > 0.5
            target_word = word if is_correct else random_word
            question = f"判断{target_word[self.mainlanguage]}的{self.studylanguage}是否为{word[self.studylanguage]}？"
            options = {'A': '是', 'C': '否'}
            answer = 'A' if is_correct else 'C'

        return question, options, answer, word

    def generate_review_questions(self, n):
        """批量生成复习题目"""
        words = []
        questions = []
        options_list = []
        answers = []

        for i in range(n):
            word = self.choose_word()
            words.append(word)
            question_type = randint(0, 2)

            if question_type == 0:  # 外译中
                question = f"{word[self.mainlanguage]}的{self.studylanguage}是什么？"
                options, answer = self._generate_options(word[self.studylanguage], self.studylanguage)
            elif question_type == 1:  # 中译外
                question = f"{word[self.studylanguage]}的{self.mainlanguage}是什么？"
                options, answer = self._generate_options(word[self.mainlanguage], self.mainlanguage)
            else:  # 判断题
                random_word = self.df1.sample(1).iloc[0]
                is_correct = random() > 0.5
                target_word = word if is_correct else random_word
                question = f"判断{target_word[self.mainlanguage]}的{self.studylanguage}是否为{word[self.studylanguage]}？"
                options = {'A': '是', 'C': '否'}
                answer = 'A' if is_correct else 'C'

            questions.append(question)
            options_list.append(options)
            answers.append(answer)

        return questions, options_list, answers, words

    def generate_questions(self,n):
        """生成题目"""
        word0=[]
        question=[]
        options=[]
        answer=[]
        for i in range(n):
            word0.append ( self._choose_word())
            question_type = randint(0, 2)
            word = word0[i]
            if question_type == 0:  # 外译中
                question.append(f"{word[self.mainlanguage]}的{self.studylanguage}是什么？")
                options0, answer0 = self._generate_options(word[self.studylanguage], self.studylanguage)
                options.append(options0)
                answer.append(answer0)
            elif question_type == 1:  # 中译外
                question.append(  f"{word[self.studylanguage]}的{self.mainlanguage}是什么？")
                options0, answer0 = self._generate_options(word[self.mainlanguage], self.mainlanguage)
                options.append(options0)
                answer.append(answer0)
            else:  # 判断题
                random_word = self.df1.sample(1).iloc[0]
                is_correct = random() > 0.5
                target_word = word if is_correct else random_word
                question.append( f"判断{target_word[self.mainlanguage]}的{self.studylanguage}是否为{word[self.studylanguage]}？")
                options.append ( {'A': '是', 'C': '否'})
                answer .append( 'A' if is_correct else 'C')

        return question, options, answer, word0

    def choose_ai_words(self):
        """从复习本随机选择一个单词，让AI推荐相关单词"""
        # 检查复习本是否为空
        if self.df3.empty:
            return []
        for i in range(4):
            # 随机选择一个复习本中的单词
            sample_word = self.df3.sample(1).iloc[0]
            main_word = sample_word[self.mainlanguage]
            study_word = sample_word[self.studylanguage]
            self.valid_word=[]
            # 准备提示词
            prompt = (f"请推荐4个与'{main_word}({study_word})'相关的{self.studylanguage}单词，"
                      "按推荐强度排序，只返回单词列表，不要任何解释或额外信息，每行一个")

            try:
                # 使用大语言模型API获取推荐词
                response = requests.post(
                    "https://api.deepseek.com",
                    headers={"Authorization": f"sk-48e6fefd3f3d46c79819e1edab6747a7"},
                    json={
                        "model": "deepseek-reasoner",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 100
                    }
                )

                # 检查响应状态
                if response.status_code != 200:
                    return []

                # 解析推荐词
                content = response.json()["choices"][0]["message"]["content"]
                recommended_words = [
                    word.strip()
                    for word in content.split("\n")
                    if word.strip()
                ]

                # 找出在词汇数据库(df1)中存在的单词
                valid_words = []
                for word in recommended_words:
                    match = self.df1[self.df1[self.studylanguage].str.lower() == word.lower()]
                    if not match.empty:
                        valid_words.append(match.iloc[0])
                self.valid_word += valid_words
            except Exception as e:
                print(f"AI推荐出错: {e}")
        return self.valid_word
    def generate_ai_questions(self):
        """生成题目"""
        word0=self.choose_ai_words()
        question=[]
        options=[]
        answer=[]
        for word in word0:
            question_type = randint(0, 2)
            if question_type == 0:  # 外译中
                question.append(f"{word[self.mainlanguage]}的{self.studylanguage}是什么？")
                options0, answer0 = self._generate_options(word[self.studylanguage], self.studylanguage)
                options.append(options0)
                answer.append(answer0)
            elif question_type == 1:  # 中译外
                question.append(  f"{word[self.studylanguage]}的{self.mainlanguage}是什么？")
                options0, answer0 = self._generate_options(word[self.mainlanguage], self.mainlanguage)
                options.append(options0)
                answer.append(answer0)
            else:  # 判断题
                random_word = self.df1.sample(1).iloc[0]
                is_correct = random() > 0.5
                target_word = word if is_correct else random_word
                question.append( f"判断{target_word[self.mainlanguage]}的{self.studylanguage}是否为{word[self.studylanguage]}？")
                options.append ( {'A': '是', 'C': '否'})
                answer .append( 'A' if is_correct else 'C')

        return question, options, answer, word0
    def handle_correct_review_answer(self, word):
        """处理复习答案正确（不立即保存，等待批量保存）"""
        idx = word.name
        if idx in self.df3.index:
            # 转换 Decimal 为 float 进行计算
            current_weight = float(self.df3.loc[idx, 'weight'])
            self.df3.loc[idx, 'weight'] = current_weight * 0.8
            # 移除立即保存，改为批量保存

    def handel_wrong_review_answer(self, word):
        """处理复习答案错误（不立即保存，等待批量保存）"""
        idx = word.name
        if idx in self.df3.index:
            # 转换 Decimal 为 float 进行计算
            current_weight = float(self.df3.loc[idx, 'weight'])
            self.df3.loc[idx, 'weight'] = current_weight * 1.2
            # 移除立即保存，改为批量保存
    def handle_correct_answer(self, word):
        """处理正确答案"""
        idx = word.name

        # 确保该单词在df2中有记录
        if idx not in self.df2.index:
            self.df2.loc[idx] = {'star': 0}

        current_star = self.df2.loc[idx, 'star']
        if current_star < 3:
            self.df2.loc[idx, 'star'] += 1

        # 使用数据库保存
        if self.username:
            self.db.update_user_record(self.username, int(idx), int(self.df2.loc[idx, 'star']))

    def handle_wrong_answer(self, word):
        """处理错误答案"""
        idx = word.name

        # 确保该单词在df2中有记录
        if idx not in self.df2.index:
            self.df2.loc[idx] = {'star': 0}

        # 添加到复习本
        if self.df3.empty:
            # 从df1获取单词信息
            new_row = self.df1.loc[[idx]].copy()
            new_row['weight'] = 10.0
            self.df3 = new_row
        elif idx not in self.df3.index:
            # 只有不在复习本中才添加
            new_row = self.df1.loc[[idx]].copy()
            new_row['weight'] = 10.0
            self.df3 = pd.concat([self.df3, new_row])
            # 添加到数据库
            if self.username:
                self.db.add_to_review_list(self.username, int(idx), 10.0)
        else:
            # 已在复习本中，增加权重
            current_weight = float(self.df3.loc[idx, 'weight'])
            new_weight = min(current_weight * 1.2, 50)
            self.df3.loc[idx, 'weight'] = new_weight
            # 更新数据库权重
            if self.username:
                self.db.update_review_weight(self.username, int(idx), float(new_weight))

        # 更新用户记录
        if self.username:
            self.db.update_user_record(self.username, int(idx), int(self.df2.loc[idx, 'star']))

    def _save_progress(self):
        """保存学习进度到数据库"""
        if not self.username:
            return

        # 保存学习记录（df2）
        for idx in self.df2.index:
            star = int(self.df2.loc[idx, 'star'])
            self.db.update_user_record(self.username, int(idx), star)

        # 保存复习本（df3）- 更新权重
        for idx in self.df3.index:
            if 'weight' in self.df3.columns:
                weight = float(self.df3.loc[idx, 'weight'])
                self.db.update_review_weight(self.username, int(idx), weight)

    def add_to_book(self, word):
        """添加到收藏本"""
        if word.name not in self.df4.index:
            new_row = self.df1.loc[[word.name]]
            if self.df4.empty:
                self.df4 = new_row
            else:
                self.df4 = pd.concat([self.df4, new_row])

            # 保存到数据库
            if self.username:
                self.db.add_bookmark(self.username, int(word.name))

    def review(self):
        """复习功能"""
        if self.df3.empty:
            print("没有需要复习的单词！")
            return

        for idx, row in self.df3.iterrows():
            print(f"\n复习单词：{row[self.mainlanguage]} - {row[self.studylanguage]}")
            # 可以在此处添加复习逻辑

    def show_stats(self):
        """显示学习统计"""
        total_time = sum(self.record.time)
        print(f"\n学习统计：")
        print(f"正确题目：{self.record.ac}题")
        print(f"错误题目：{self.record.wa}题")
        print(f"总耗时：{total_time:.2f}秒")
        print(f"平均答题时间：{total_time / len(self.record.time):.2f}秒")

    def update_day_stats(self):
        """更新每日统计"""
        if self.username:
            # 使用数据库更新
            from datetime import datetime, date
            today = datetime.today().date()  # 转换为 date 对象
            total_q = self.record.ac + self.record.wa
            print(f"[DEBUG] update_day_stats called: username={self.username}, date={today}, total={total_q}, ac={self.record.ac}, wa={self.record.wa}")
            self.db.update_daily_stats(self.username, today,
                                      total_q,
                                      self.record.ac,
                                      self.record.wa)
            print(f"[DEBUG] Database update completed")
            # 重新加载到DataFrame
            self._load_user_data_from_db()
            print(f"[DEBUG] After reload, df5 shape: {self.df5.shape}, empty: {self.df5.empty}")

    def show_data(self):
        s=[]
        for i in range(len(self.df1)):
            s.append([f"{self.df1.iloc[i]['Chinese']}" ,f"{self.df1.iloc[i]['English']}",f"{self.df1.iloc[i]['Japanese']}", f"level {self.df1.iloc[i]['level']}"])
        return s
    def show_book(self):
        if self.df4.empty:
            return "收藏本为空！"
        else:
            s=[]
            for i in range(len(self.df4)):
                s.append([f"{self.df4.iloc[i]['Chinese']}" ,f"{self.df4.iloc[i]['English']}",f"{self.df4.iloc[i]['Japanese']}", f"level {self.df4.iloc[i]['level']}"])
            return s

    def show_day_stats(self):
        """显示每日统计折线图并返回 QImage 对象"""
        # 初始化 dates 和 total 属性（即使没有数据也要初始化）
        self.dates = []
        self.total = []

        # 创建图表
        fig = Figure(figsize=(10, 5))
        ax = fig.add_subplot(111)

        if self.df5.empty:
            print("暂无每日统计数据！")
            # 创建空图表，显示提示信息
            ax.text(0.5, 0.5, '暂无数据\n开始练习后即可看到统计图表',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes,
                   fontsize=16,
                   color='gray')
            ax.set_xlabel('日期')
            ax.set_ylabel('题目数')
            ax.set_title('每日答题统计')
            ax.grid(True, alpha=0.3)
        else:
            # 复制并排序数据
            df = self.df5.copy().sort_index()
            dates = df.index.tolist()
            self.dates = dates
            ac = df['ac'].tolist()
            wa = df['wa'].tolist()
            self.total = [a + w for a, w in zip(ac, wa)]

            # 绘制三条折线
            ax.plot(dates, ac, marker='o', label='正确(ac)')
            ax.plot(dates, wa, marker='o', label='错误(wa)')
            ax.plot(dates, self.total, marker='o', label='总答题数')

            # 设置图表属性
            ax.set_xlabel('日期')
            ax.set_ylabel('题目数')
            ax.set_title('每日答题统计')
            ax.legend()
            ax.grid(True)

        fig.tight_layout()

        # 转换为 QImage
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        qimg = QImage()
        qimg.loadFromData(buf.read())

        buf.close()

        return qimg  # 返回 QImage 对象用于显示

    def plot(self):
        self.update_day_stats()
        """生成图表并返回 Figure 对象"""
        x = list(range(1, len(self.record.time) + 1))
        y = self.record.time
        is_correct = self.record.is_correct

        # 创建图表
        fig = Figure(figsize=(8, 4))
        ax = fig.add_subplot(111)

        # 正确题目
        x_ac = [i + 1 for i, c in enumerate(is_correct) if c]
        y_ac = [y[i] for i, c in enumerate(is_correct) if c]
        ax.scatter(x_ac, y_ac, color='green', label='正确', zorder=3)

        # 错误题目
        x_wa = [i + 1 for i, c in enumerate(is_correct) if not c]
        y_wa = [y[i] for i, c in enumerate(is_correct) if not c]
        ax.scatter(x_wa, y_wa, color='red', label='错误', zorder=3)

        # 折线
        ax.plot(x, y, color='blue', alpha=0.5, zorder=2)

        # 设置图表属性
        ax.set_xlabel('题目序号')
        ax.set_ylabel('用时（秒）')
        ax.set_title('每题用时折线图')
        ax.legend()
        ax.grid(True)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        qimg = QImage()
        qimg.loadFromData(buf.read())

        buf.close()

        return qimg  # 返回图表对象，而非直接显示
    def run(self):
        """主运行循环"""
        print("欢迎使用智能单词学习系统！")
        self.set_languages()
        n=int(input("请选择题目难度等级（1-3）："))
        self.choose_level(n)

        while True:
            start_time = time()
            question, options, answer, word = self.generate_question()
            print(f"\n题目：{question}")
            for k, v in options.items():
                print(f"{k}. {v}")
            user_input = input("请输入答案：").upper()
            time_used = time() - start_time
            if user_input == answer:
                self.record.add_ac(time_used)
                self.handle_correct_answer(word)
                print("✅ 正确！")
            else:
                self.record.add_wa(time_used)
                self.handle_wrong_answer(word)
                print(f"❌ 错误，正确答案是：{answer}")

            # 收藏功能
            if input("添加到收藏本？(y/n) ").lower() == 'y':
                self.add_to_book(word)

            # 复习提示
            if len(self.df3) >= 5:
                print("\n您有5个以上需要复习的单词！")
                self.review()

            if input("继续学习？(y/n) ").lower() != 'y':
                self.show_stats()
                break
        self.update_day_stats()
        # 绘图部分
        x = list(range(1, len(self.record.time) + 1))
        y = self.record.time
        is_correct = self.record.is_correct
        plt.figure(figsize=(8, 4))
        # 正确题目
        x_ac = [i+1 for i, c in enumerate(is_correct) if c]
        y_ac = [y[i] for i, c in enumerate(is_correct) if c]
        plt.scatter(x_ac, y_ac, color='green', label='正确', zorder=3)
        # 错误题目
        x_wa = [i+1 for i, c in enumerate(is_correct) if not c]
        y_wa = [y[i] for i, c in enumerate(is_correct) if not c]
        plt.scatter(x_wa, y_wa, color='red', label='错误', zorder=3)
        # 折线
        plt.plot(x, y, color='blue', alpha=0.5, zorder=2)
        plt.xlabel('题目序号')
        plt.ylabel('用时（秒）')
        plt.title('每题用时折线图')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        self.show_day_stats()

        def show_book(self):
            if self.df4.empty:
                return "收藏本为空！"
            else:
                s = []
                for i in range(len(self.df4)):
                    s.append([f"{self.df4.iloc[i]['Chinese']}", f"{self.df4.iloc[i]['English']}",
                              f"{self.df4.iloc[i]['Japanese']}", f"level {self.df4.iloc[i]['level']}"])
                return s


if __name__ == "__main__":
    system = VocabularyLearningSystem()
    system.run()
