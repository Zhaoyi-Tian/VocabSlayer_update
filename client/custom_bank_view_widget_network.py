# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           SmoothScrollArea, InfoBar, InfoBarPosition)

class CustomBankViewWidgetNetwork(QWidget):
    """自定义题库查看界面 - 网络版本"""

    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.current_bank_id = None
        self.questions = []
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

        # 题目列表（使用滚动区域）
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.questions_widget = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_widget)
        self.questions_layout.setSpacing(15)
        self.questions_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area.setWidget(self.questions_widget)
        layout.addWidget(self.scroll_area)

        # 底部控制按钮
        self.create_bottom_controls(layout)

        # 初始状态
        self.show_empty_state()

    def create_top_bar(self, layout):
        """创建顶部信息栏"""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 返回按钮
        self.back_btn = PushButton(FluentIcon.LEFT_ARROW, "返回")
        self.back_btn.clicked.connect(self.back)
        top_layout.addWidget(self.back_btn)

        top_layout.addStretch()

        # 题库信息
        self.bank_title = SubtitleLabel("题库内容")
        top_layout.addWidget(self.bank_title)

        top_layout.addStretch()

        # 题目数量
        self.count_label = BodyLabel("")
        top_layout.addWidget(self.count_label)

        layout.addWidget(top_widget)

    def create_bottom_controls(self, layout):
        """创建底部控制按钮"""
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout.addStretch()

        # 删除题库按钮
        self.delete_btn = PushButton(FluentIcon.DELETE, "删除题库")
        self.delete_btn.clicked.connect(self.delete_bank)
        controls_layout.addWidget(self.delete_btn)

        # 开始答题按钮
        self.start_quiz_btn = PrimaryPushButton(FluentIcon.PLAY, "开始答题")
        self.start_quiz_btn.clicked.connect(self.start_quiz)
        controls_layout.addWidget(self.start_quiz_btn)

        layout.addWidget(controls_widget)

    def show_empty_state(self):
        """显示空状态"""
        # 清除所有题目卡片
        for i in reversed(range(self.questions_layout.count())):
            child = self.questions_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # 添加空状态提示
        empty_label = SubtitleLabel("请选择题库查看内容")
        empty_label.setAlignment(Qt.AlignCenter)
        self.questions_layout.addWidget(empty_label)
        self.questions_layout.addStretch()

        # 隐藏底部按钮
        self.delete_btn.hide()
        self.start_quiz_btn.hide()

    def load_bank(self, bank_id):
        """从服务器加载题库内容"""
        self.current_bank_id = bank_id

        if not self.network_manager:
            InfoBar.error(
                title="错误",
                content="网络管理器未初始化",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        try:
            # 获取题库信息
            bank_data = self.network_manager.get_bank_info(bank_id, self.user_id)
            if not bank_data:
                InfoBar.error(
                    title="错误",
                    content="题库不存在",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return

            self.bank_data = bank_data

            # 获取题目列表（包含答案）
            questions = self.network_manager.get_bank_questions_with_answers(bank_id, self.user_id)
            self.questions = questions

            # 更新界面
            self.bank_title.setText(f"题库：{bank_data['bank_name']}")
            self.count_label.setText(f"共 {len(self.questions)} 道题目")

            # 显示题目
            self.show_questions()

            # 显示底部按钮
            self.delete_btn.show()
            self.start_quiz_btn.show()

            InfoBar.success(
                title="加载成功",
                content=f"已加载 {len(self.questions)} 道题目",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        except Exception as e:
            InfoBar.error(
                title="加载失败",
                content=f"错误：{str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def show_questions(self):
        """显示所有题目"""
        # 清除空状态
        for i in reversed(range(self.questions_layout.count())):
            child = self.questions_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # 添加题目卡片
        for i, q in enumerate(self.questions):
            card = self.create_question_card(i + 1, q)
            self.questions_layout.addWidget(card)

        # 添加底部空间
        self.questions_layout.addStretch()

    def create_question_card(self, index, question):
        """创建题目卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 题号
        number_label = SubtitleLabel(f"第 {index} 题")
        number_label.setStyleSheet("color: #4080FF;")
        card_layout.addWidget(number_label)

        # 题目内容
        question_label = BodyLabel(f"问题：{question['question_text']}")
        question_label.setWordWrap(True)
        question_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                line-height: 1.6;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 5px;
                border-left: 4px solid #4080FF;
            }
        """)
        card_layout.addWidget(question_label)

        # 答案内容
        answer_label = BodyLabel(f"答案：{question['answer_text']}")
        answer_label.setWordWrap(True)
        answer_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                line-height: 1.6;
                padding: 10px;
                background-color: #f0f8ff;
                border-radius: 5px;
                border-left: 4px solid #28a745;
            }
        """)
        card_layout.addWidget(answer_label)

        return card

    def delete_bank(self):
        """删除题库"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除题库 '{self.bank_data['bank_name'] if self.bank_data else '当前题库'}' 吗？\n\n"
            "此操作将删除所有题目，且不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 调用后端删除
            if self.network_manager:
                success = self.network_manager.delete_bank(self.current_bank_id, self.user_id)
                if success:
                    InfoBar.success(
                        title="删除成功",
                        content="题库已被删除",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    # 返回管理界面
                    self.back_to_manage()
                else:
                    InfoBar.error(
                        title="删除失败",
                        content="删除题库时出错",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )

    def start_quiz(self):
        """开始答题"""
        if self.parent:
            self.parent.switch_to_custom_quiz(self.current_bank_id)

    def back(self):
        """返回"""
        if hasattr(self.parent, 'switch_to_custom_manage'):
            self.parent.switch_to_custom_manage()

    def back_to_manage(self):
        """返回管理界面"""
        if hasattr(self.parent, 'switch_to_custom_manage'):
            self.parent.switch_to_custom_manage()