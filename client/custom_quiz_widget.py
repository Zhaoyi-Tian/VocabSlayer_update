# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QMessageBox, QScrollArea,
                            QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QElapsedTimer
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           InfoBar, InfoBarPosition, SmoothScrollArea, TextBrowser)

# 尝试导入custom_bank_manager模块
try:
    # 检查是否存在VocabSlayer_update_servier目录
    servier_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                'VocabSlayer_update_servier', 'common')
    if os.path.exists(servier_path):
        sys.path.append(servier_path)
        from custom_bank_manager import CustomBankManager
        CUSTOM_BANK_MANAGER_AVAILABLE = True
    else:
        CUSTOM_BANK_MANAGER_AVAILABLE = False
except ImportError:
    CUSTOM_BANK_MANAGER_AVAILABLE = False

class CustomQuizWidget(QWidget):
    """自定义题库答题界面"""

    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.current_bank_id = None
        self.current_question_index = 0
        self.questions = []
        self.user_answers = []  # 存储用户答题记录
        self.answer_shown = False
        self.question_start_time = None
        self.bank_data = None

        # 初始化数据库和题库管理器
        self.init_database()

        self.init_ui()

    def init_database(self):
        """初始化数据库连接和题库管理器"""
        # 检查是否有服务端模块
        if not CUSTOM_BANK_MANAGER_AVAILABLE:
            print("本地模式：自定义题库功能不可用")
            self.db = None
            self.user_id = None
            self.api_key = None
            self.bank_manager = None
            return

        try:
            # 导入数据库管理器
            from server.database_manager import DatabaseFactory

            # 创建数据库连接
            self.db = DatabaseFactory.from_config_file('config.json')
            self.db.connect()

            # 获取用户ID
            self.user_id = self.db._get_user_id(self.username)

            # 获取API配置
            user_config = self.db.get_user_config(self.username)
            self.api_key = user_config.get('api_key', '') if user_config else ''

            # 创建题库管理器
            if self.api_key:
                self.bank_manager = CustomBankManager(
                    db_manager=self.db,
                    api_key=self.api_key
                )
            else:
                self.bank_manager = None

        except Exception as e:
            print(f"初始化数据库失败: {e}")
            self.db = None
            self.user_id = None
            self.api_key = None
            self.bank_manager = None

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 顶部信息栏
        self.create_top_bar(layout)

        # 题目卡片
        self.question_card = self.create_question_card()
        layout.addWidget(self.question_card)

        # 底部控制按钮
        self.create_bottom_controls(layout)

        # 初始隐藏题目卡片（直到选择题库）
        self.question_card.hide()

    def create_top_bar(self, layout):
        """创建顶部信息栏"""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 返回按钮
        self.back_btn = PushButton(FluentIcon.LEFT_ARROW, "返回题库管理")
        self.back_btn.clicked.connect(self.back_to_manage)
        top_layout.addWidget(self.back_btn)

        top_layout.addStretch()

        # 题库信息
        self.bank_info_label = SubtitleLabel("请选择题库")
        top_layout.addWidget(self.bank_info_label)

        top_layout.addStretch()

        # 进度信息
        self.progress_label = BodyLabel("")
        top_layout.addWidget(self.progress_label)

        layout.addWidget(top_widget)

    def create_question_card(self):
        """创建题目卡片"""
        card = CardWidget()
        card.setMinimumHeight(400)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # 题号
        self.question_number_label = SubtitleLabel("")
        self.question_number_label.setStyleSheet("""
            SubtitleLabel {
                font-size: 18px;
                font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", sans-serif;
                font-weight: 600;
                color: #4080ff;
                margin-bottom: 8px;
            }
        """)
        card_layout.addWidget(self.question_number_label)

        # 题目内容 - 直接使用TextBrowser，不要外层滚动区域
        self.question_content = TextBrowser()
        self.question_content.setAcceptRichText(True)
        self.question_content.setReadOnly(True)
        self.question_content.setOpenExternalLinks(False)
        self.question_content.setMinimumHeight(80)
        self.question_content.setMaximumHeight(150)
        self.question_content.setStyleSheet("""
            QTextBrowser {
                background: #f5f7fb;
                border: none;
                padding: 10px;
                font-size: 14px;
            }
        """)

        # 添加默认样式表 - 使用AI界面的样式
        self.question_content.document().setDefaultStyleSheet("""
            p { margin: 5px 0; }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #0078D4;
                margin: 10px 0;
            }
            blockquote {
                border-left: 4px solid #ccc;
                margin: 10px 0;
                padding-left: 10px;
                color: #666;
            }
            ul, ol { margin: 5px 0; padding-left: 20px; }
            li { margin: 3px 0; }
        """)

        card_layout.addWidget(self.question_content)

        # 分隔线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e0e0e0;")
        card_layout.addWidget(line)

        # 答案区域（初始隐藏）
        self.answer_widget = QWidget()
        self.answer_layout = QVBoxLayout(self.answer_widget)
        self.answer_layout.setSpacing(20)

        # 答案内容 - 直接使用TextBrowser，不要外层滚动区域
        self.answer_content = TextBrowser()
        self.answer_content.setAcceptRichText(True)
        self.answer_content.setReadOnly(True)
        self.answer_content.setOpenExternalLinks(False)
        self.answer_content.setMinimumHeight(300)
        self.answer_content.setStyleSheet("""
            QTextBrowser {
                background: #f5f7fb;
                border: none;
                padding: 15px;
                font-size: 14px;
            }
        """)

        # 添加默认样式表 - 使用AI界面的样式
        self.answer_content.document().setDefaultStyleSheet("""
            p { margin: 5px 0; }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #0078D4;
                margin: 10px 0;
            }
            blockquote {
                border-left: 4px solid #ccc;
                margin: 10px 0;
                padding-left: 10px;
                color: #666;
            }
            ul, ol { margin: 5px 0; padding-left: 20px; }
            li { margin: 3px 0; }
        """)

        self.answer_layout.addWidget(self.answer_content)

        card_layout.addWidget(self.answer_widget)
        self.answer_widget.hide()  # 初始隐藏

        card_layout.addStretch()

        return card

    def create_bottom_controls(self, layout):
        """创建底部控制按钮"""
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout.addStretch()

        # 显示答案按钮
        self.show_answer_btn = PrimaryPushButton(FluentIcon.VIEW, "显示答案")
        self.show_answer_btn.clicked.connect(self.show_answer)
        controls_layout.addWidget(self.show_answer_btn)

        # 上一题按钮
        self.prev_btn = PushButton(FluentIcon.LEFT_ARROW, "上一题")
        self.prev_btn.clicked.connect(self.prev_question)
        self.prev_btn.setEnabled(False)
        controls_layout.addWidget(self.prev_btn)

        # 下一题按钮
        self.next_btn = PrimaryPushButton(FluentIcon.RIGHT_ARROW, "下一题")
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setEnabled(False)
        controls_layout.addWidget(self.next_btn)

        layout.addWidget(controls_widget)

    def load_bank(self, bank_id):
        """从数据库加载题库"""
        self.current_bank_id = bank_id
        self.current_question_index = 0
        self.answer_shown = False
        self.user_answers = []

        # 检查是否是本地模式
        if not CUSTOM_BANK_MANAGER_AVAILABLE or not self.bank_manager:
            QMessageBox.information(
                self,
                "提示",
                "自定义题库功能需要在服务器端运行。\n\n"
                "请在服务器上使用该功能，或者确保已部署VocabSlayer_update_servier服务。"
            )
            return

        try:
            # 获取题库信息
            banks = self.bank_manager.get_user_banks(self.user_id)
            self.bank_data = next((b for b in banks if b['bank_id'] == bank_id), None)

            if not self.bank_data:
                QMessageBox.critical(self, "错误", "题库不存在")
                return

            # 获取题目列表（只包含问题，不含答案）
            self.questions = self.bank_manager.get_questions_for_quiz(bank_id)

            if not self.questions:
                QMessageBox.warning(self, "提示", "该题库暂无题目")
                return

            # 显示题目卡片
            self.question_card.show()
            self.bank_info_label.setText(self.bank_data['bank_name'])

            # 显示第一题
            self.show_question(0)

            # 更新进度
            self.update_progress()

            # 创建计时器
            self.question_start_time = QElapsedTimer()
            self.question_start_time.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载题库失败：{str(e)}")

    def load_sample_questions(self):
        """加载示例题目"""
        # 模拟题目数据
        self.questions = [
            {
                'id': 1,
                'question': '什么是CPU？它的主要功能是什么？',
                'answer': 'CPU（Central Processing Unit）中央处理器是计算机的核心部件，负责执行指令、处理数据。主要功能包括：\n1. 指令控制：读取和执行程序指令\n2. 时序控制：产生操作时序信号\n3. 数据加工：对数据进行算术和逻辑运算\n4. 中断处理：响应和处理中断请求'
            },
            {
                'id': 2,
                'question': 'RAM和ROM有什么区别？',
                'answer': 'RAM（随机存取存储器）和ROM（只读存储器）的主要区别：\n\nRAM：\n- 可读可写，数据易失（断电后丢失）\n- 用于存储临时数据和运行中的程序\n- 访问速度快\n\nROM：\n- 只读（特殊类型可写），数据非易失（断电后保留）\n- 用于存储固件和启动程序\n- 访问速度相对较慢'
            },
            {
                'id': 3,
                'question': '什么是操作系统？其主要功能有哪些？',
                'answer': '操作系统是管理计算机硬件与软件资源的系统软件。主要功能包括：\n1. 进程管理：创建、调度和终止进程\n2. 内存管理：分配和回收内存空间\n3. 文件管理：管理文件的存储和访问\n4. 设备管理：管理I/O设备\n5. 用户接口：提供用户与计算机交互的方式\n6. 系统保护：确保系统安全稳定运行'
            }
        ]

    def show_question(self, index):
        """显示指定索引的题目"""
        if index < 0 or index >= len(self.questions):
            return

        self.current_question_index = index
        self.answer_shown = False

        question = self.questions[index]

        # 更新题号
        self.question_number_label.setText(f"第 {index + 1} / {len(self.questions)} 题")

        # 更新题目内容（支持富文本）
        question_text = question['question'].replace('\n', '<br>')
        self.question_content.setHtml(f"<p>{question_text}</p>")

        # 重置答案区域
        self.answer_widget.hide()
        self.show_answer_btn.setText("显示答案")
        self.show_answer_btn.setEnabled(True)

      
        # 更新按钮状态
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.questions) - 1)

    def show_answer(self):
        """显示答案"""
        if not self.answer_shown:
            # 从数据库获取完整题目（包含答案）
            if self.bank_manager:
                questions_with_answers = self.bank_manager.get_bank_questions(self.current_bank_id)
                current_question = None
                for q in questions_with_answers:
                    if q['question_id'] == self.questions[self.current_question_index]['question_id']:
                        current_question = q
                        break

                if current_question:
                    # 支持富文本显示，保留换行
                    html_text = current_question['answer_text'].replace('\n', '<br>')
                    self.answer_content.setHtml(f"<p>{html_text}</p>")
                else:
                    self.answer_content.setHtml("<p style='color: red;'>答案加载失败</p>")
            else:
                self.answer_content.setHtml("<p style='color: #666;'>数据库未初始化</p>")

            self.answer_widget.show()
            self.show_answer_btn.setText("隐藏答案")
            self.answer_shown = True
        else:
            self.answer_widget.hide()
            self.show_answer_btn.setText("显示答案")
            self.answer_shown = False

  
    def save_user_answer(self, is_correct):
        """保存用户答案到数据库"""
        # 确保列表足够大
        while len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(None)

        # 计算答题时间
        answer_time = 0
        if self.question_start_time:
            answer_time = self.question_start_time.elapsed() // 1000  # 转换为秒

        # 保存答案
        self.user_answers[self.current_question_index] = {
            'is_correct': is_correct,
            'timestamp': Qt.QDateTime.currentDateTime().toString(Qt.ISODate),
            'answer_time': answer_time
        }

        # 保存到数据库
        if self.bank_manager and self.current_question_index < len(self.questions):
            try:
                question_id = self.questions[self.current_question_index]['question_id']
                self.bank_manager.save_answer(
                    user_id=self.user_id,
                    question_id=question_id,
                    user_answer="",  # 简答题不需要用户答案文本
                    is_correct=is_correct,
                    answer_time=answer_time
                )
            except Exception as e:
                print(f"保存答案失败: {e}")

    
    def prev_question(self):
        """上一题"""
        if self.current_question_index > 0:
            self.show_question(self.current_question_index - 1)

    def next_question(self):
        """下一题"""
        if self.current_question_index < len(self.questions) - 1:
            self.show_question(self.current_question_index + 1)
        else:
            # 最后一题，询问是否完成
            self.show_completion_dialog()

    def update_progress(self):
        """更新进度显示"""
        total = len(self.questions)
        answered = len([a for a in self.user_answers if a is not None])
        self.progress_label.setText(f"进度：{answered}/{total}")

    def show_completion_dialog(self):
        """显示完成对话框"""
        total = len(self.questions)
        correct = len([a for a in self.user_answers if a and a.get('is_correct')])

        msg = QMessageBox(self)
        msg.setWindowTitle("答题完成")
        msg.setText(f"您已完成所有题目！\n\n"
                   f"总题数：{total}\n"
                   f"已掌握：{correct}\n"
                   f"未掌握：{total - correct}\n\n"
                   f"掌握率：{correct/total*100:.1f}%")
        msg.addButton("返回题库", QMessageBox.AcceptRole)
        msg.addButton("继续复习", QMessageBox.RejectRole)

        if msg.exec_() == QMessageBox.AcceptRole:
            self.back_to_manage()

    def back_to_manage(self):
        """返回题库管理"""
        if self.parent:
            self.parent.switch_to_custom_manage()