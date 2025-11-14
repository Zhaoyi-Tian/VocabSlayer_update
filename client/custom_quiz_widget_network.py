# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QMessageBox, QScrollArea,
                            QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           InfoBar, InfoBarPosition, SmoothScrollArea)

class CustomQuizWidgetNetwork(QWidget):
    """自定义题库答题界面 - 网络版本"""

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

        # 网络管理器和用户ID将在外部设置
        self.network_manager = None
        self.user_id = None

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
        """从服务器加载题库"""
        self.current_bank_id = bank_id
        self.current_question_index = 0
        self.answer_shown = False
        self.user_answers = []

        if not self.network_manager:
            QMessageBox.critical(self, "错误", "网络管理器未初始化！")
            return

        try:
            # 获取题库信息
            bank_info = self.network_manager.get_bank_info(bank_id)
            if not bank_info:
                QMessageBox.critical(self, "错误", "题库不存在")
                return

            self.bank_data = bank_info

            # 获取题目列表（包含答案）
            questions = self.network_manager.get_bank_questions_with_answers(bank_id, self.user_id)
            if not questions:
                QMessageBox.warning(self, "提示", "该题库暂无题目")
                return

            self.questions = questions

            # 显示题目卡片
            self.question_card.show()
            self.bank_info_label.setText(bank_info['bank_name'])

            # 显示第一题
            self.show_question(0)

            # 更新进度
            self.update_progress()

            # 记录开始时间
            self.question_start_time = QTimer.currentTime()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载题库失败：{str(e)}")

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
        self.question_content.setText(question['question_text'])

        # 重置答案区域
        self.answer_widget.hide()
        self.show_answer_btn.setText("显示答案")
        self.show_answer_btn.setEnabled(True)

        # 重置评估按钮
        self.assessment_widget.hide()

        # 更新按钮状态
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.questions) - 1)

    def show_answer(self):
        """显示答案"""
        if not self.answer_shown:
            if self.current_question_index < len(self.questions):
                answer_text = self.questions[self.current_question_index]['answer_text']
                self.answer_content.setText(answer_text)
            else:
                self.answer_content.setText("答案加载失败")

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
        """保存用户答案到服务器"""
        # 确保列表足够大
        while len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(None)

        # 计算答题时间
        answer_time = 0
        if self.question_start_time:
            current_time = QTimer.currentTime()
            answer_time = (current_time - self.question_start_time) // 1000  # 转换为秒

        # 保存答案
        self.user_answers[self.current_question_index] = {
            'is_correct': is_correct,
            'timestamp': Qt.QDateTime.currentDateTime().toString(Qt.ISODate),
            'answer_time': answer_time
        }

        # 发送到服务器
        if self.network_manager and self.current_question_index < len(self.questions):
            try:
                question_id = self.questions[self.current_question_index]['question_id']
                self.network_manager.save_answer(
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