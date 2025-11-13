# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           InfoBar, InfoBarPosition, SmoothScrollArea)

class CustomQuizWidget(QWidget):
    """自定义题库答题界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_bank_id = None
        self.current_question_index = 0
        self.questions = []
        self.user_answers = []  # 存储用户答题记录
        self.answer_shown = False
        self.init_ui()

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
        card_layout.addWidget(self.question_number_label)

        # 题目内容
        self.question_scroll = SmoothScrollArea()
        self.question_scroll.setWidgetResizable(True)
        self.question_scroll.setMinimumHeight(150)

        self.question_content = BodyLabel("")
        self.question_content.setWordWrap(True)
        self.question_content.setStyleSheet("""
            QLabel {
                font-size: 16px;
                line-height: 1.6;
                padding: 10px;
            }
        """)

        question_widget = QWidget()
        question_layout = QVBoxLayout(question_widget)
        question_layout.addWidget(self.question_content)
        self.question_scroll.setWidget(question_widget)

        card_layout.addWidget(self.question_scroll)

        # 分隔线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e0e0e0;")
        card_layout.addWidget(line)

        # 答案区域（初始隐藏）
        self.answer_widget = QWidget()
        self.answer_layout = QVBoxLayout(self.answer_widget)
        self.answer_layout.setSpacing(10)

        answer_title = SubtitleLabel("答案：")
        self.answer_layout.addWidget(answer_title)

        self.answer_content = BodyLabel("")
        self.answer_content.setWordWrap(True)
        self.answer_content.setStyleSheet("""
            QLabel {
                font-size: 16px;
                line-height: 1.6;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        self.answer_layout.addWidget(self.answer_content)

        # 用户自我评估
        self.assessment_widget = QWidget()
        assessment_layout = QHBoxLayout(self.assessment_widget)
        assessment_layout.setContentsMargins(0, 0, 0, 0)

        assessment_label = BodyLabel("掌握程度：")
        assessment_layout.addWidget(assessment_label)

        self.correct_btn = PrimaryPushButton(FluentIcon.CHECKBOX, "已掌握")
        self.correct_btn.clicked.connect(self.mark_as_correct)
        assessment_layout.addWidget(self.correct_btn)

        self.incorrect_btn = PushButton(FluentIcon.CANCEL, "未掌握")
        self.incorrect_btn.clicked.connect(self.mark_as_incorrect)
        assessment_layout.addWidget(self.incorrect_btn)

        self.answer_layout.addWidget(self.assessment_widget)

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
        """加载题库"""
        self.current_bank_id = bank_id
        self.current_question_index = 0
        self.answer_shown = False
        self.user_answers = []

        # 这里应该从服务器获取题库和题目
        # 暂时使用模拟数据
        self.load_sample_questions()

        # 显示题目卡片
        self.question_card.show()
        self.bank_info_label.setText("自定义题库")

        # 显示第一题
        self.show_question(0)

        # 更新进度
        self.update_progress()

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

        # 更新题目内容
        self.question_content.setText(question['question'])

        # 重置答案区域
        self.answer_widget.hide()
        self.show_answer_btn.setText("显示答案")
        self.show_answer_btn.setEnabled(True)

        # 重置评估按钮（如果有之前的答案）
        if index < len(self.user_answers) and self.user_answers[index] is not None:
            self.show_user_assessment()
        else:
            self.assessment_widget.hide()

        # 更新按钮状态
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.questions) - 1)

    def show_answer(self):
        """显示答案"""
        if not self.answer_shown:
            question = self.questions[self.current_question_index]
            self.answer_content.setText(question['answer'])
            self.answer_widget.show()
            self.show_answer_btn.setText("隐藏答案")
            self.answer_shown = True

            # 如果还没有评估记录，显示评估按钮
            if self.current_question_index >= len(self.user_answers) or \
               self.user_answers[self.current_question_index] is None:
                self.assessment_widget.show()
        else:
            self.answer_widget.hide()
            self.show_answer_btn.setText("显示答案")
            self.answer_shown = False
            if self.current_question_index >= len(self.user_answers) or \
               self.user_answers[self.current_question_index] is None:
                self.assessment_widget.hide()

    def mark_as_correct(self):
        """标记为已掌握"""
        self.save_user_answer(True)
        InfoBar.success(
            title="记录成功",
            content="已标记为掌握",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self
        )
        self.assessment_widget.hide()

    def mark_as_incorrect(self):
        """标记为未掌握"""
        self.save_user_answer(False)
        InfoBar.warning(
            title="记录成功",
            content="已标记为未掌握",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self
        )
        self.assessment_widget.hide()

    def save_user_answer(self, is_correct):
        """保存用户答案"""
        # 确保列表足够大
        while len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(None)

        # 保存答案
        self.user_answers[self.current_question_index] = {
            'is_correct': is_correct,
            'timestamp': Qt.QDateTime.currentDateTime().toString(Qt.ISODate)
        }

        # 这里应该将答案发送到服务器
        # self.send_answer_to_server()

    def show_user_assessment(self):
        """显示用户之前的评估"""
        answer = self.user_answers[self.current_question_index]
        if answer and 'is_correct' in answer:
            self.assessment_widget.show()
            if answer['is_correct']:
                self.correct_btn.setEnabled(False)
                self.correct_btn.setText("✓ 已掌握")
                self.incorrect_btn.setEnabled(True)
                self.incorrect_btn.setText("改为未掌握")
            else:
                self.correct_btn.setEnabled(True)
                self.correct_btn.setText("改为已掌握")
                self.incorrect_btn.setEnabled(False)
                self.incorrect_btn.setText("✗ 未掌握")

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