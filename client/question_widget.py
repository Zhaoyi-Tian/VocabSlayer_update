# -*- coding: utf-8 -*-
"""
用户注册时的问卷调查组件
用于收集用户的母语、学习语言、难度偏好和目标积分
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QStackedWidget
from client.question import Ui_fanyi


class QuestionWidget(QWidget):
    """多页问卷组件"""

    # 完成信号，携带用户的选择结果
    finished = pyqtSignal(dict)  # {"main_language": "Chinese", "study_language": "English", "difficulty": 1, "target_score": 10000}

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_preferences = {
            "main_language": None,
            "study_language": None,
            "difficulty": None,
            "target_score": None
        }

        # 当前问题索引
        self.current_question = 0

        # 创建堆叠布局以支持多页
        self.stack = QStackedWidget(self)

        # 创建4个问题页面
        self.question_pages = []
        self._create_question_pages()

        # 设置布局
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def _create_question_pages(self):
        """创建4个问题页面"""

        # 问题1: 母语选择
        page1 = QWidget()
        ui1 = Ui_fanyi()
        ui1.setupUi(page1)
        ui1.LargeTitleLabel.setText(f"欢迎使用万识斩, {self.username}")
        ui1.BodyLabel.setText("这些配置之后可在设置选项中调整")
        ui1.CaptionLabel.setText("请选择你的母语（主语言）")
        ui1.RadioButton.setText("中文 (Chinese)")
        ui1.RadioButton_2.setText("英语 (English)")
        ui1.RadioButton_3.setText("日语 (Japanese)")
        ui1.PrimaryPushButton.setText("NEXT")
        ui1.PrimaryPushButton.clicked.connect(lambda: self._on_next_clicked(0, ui1))
        # 存储UI引用
        page1.ui = ui1
        self.question_pages.append(page1)
        self.stack.addWidget(page1)

        # 问题2: 学习语言选择
        page2 = QWidget()
        ui2 = Ui_fanyi()
        ui2.setupUi(page2)
        ui2.LargeTitleLabel.setText(f"欢迎使用万识斩, {self.username}")
        ui2.BodyLabel.setText("这些配置之后可在设置选项中调整")
        ui2.CaptionLabel.setText("请选择你想要学习的语言")
        ui2.RadioButton.setText("英语 (English)")
        ui2.RadioButton_2.setText("中文 (Chinese)")
        ui2.RadioButton_3.setText("日语 (Japanese)")
        ui2.PrimaryPushButton.setText("NEXT")
        ui2.PrimaryPushButton.clicked.connect(lambda: self._on_next_clicked(1, ui2))
        page2.ui = ui2
        self.question_pages.append(page2)
        self.stack.addWidget(page2)

        # 问题3: 难度选择
        page3 = QWidget()
        ui3 = Ui_fanyi()
        ui3.setupUi(page3)
        ui3.LargeTitleLabel.setText(f"欢迎使用万识斩, {self.username}")
        ui3.BodyLabel.setText("这些配置之后可在设置选项中调整")
        ui3.CaptionLabel.setText("请选择你想要的学习难度")
        ui3.RadioButton.setText("简单 (Level 1) - 基础词汇")
        ui3.RadioButton_2.setText("中等 (Level 2) - 常用词汇")
        ui3.RadioButton_3.setText("困难 (Level 3) - 高级词汇")
        ui3.PrimaryPushButton.setText("NEXT")
        ui3.PrimaryPushButton.clicked.connect(lambda: self._on_next_clicked(2, ui3))
        page3.ui = ui3
        self.question_pages.append(page3)
        self.stack.addWidget(page3)

        # 问题4: 目标积分选择
        page4 = QWidget()
        ui4 = Ui_fanyi()
        ui4.setupUi(page4)
        ui4.LargeTitleLabel.setText(f"欢迎使用万识斩, {self.username}")
        ui4.BodyLabel.setText("这些配置之后可在设置选项中调整")
        ui4.CaptionLabel.setText("请选择你的目标积分")
        ui4.RadioButton.setText("3000 分 - 入门目标")
        ui4.RadioButton_2.setText("10000 分 - 进阶目标")
        ui4.RadioButton_3.setText("30000 分 - 精通目标")
        ui4.PrimaryPushButton.setText("完成")
        ui4.PrimaryPushButton.clicked.connect(lambda: self._on_next_clicked(3, ui4))
        page4.ui = ui4
        self.question_pages.append(page4)
        self.stack.addWidget(page4)

    def _on_next_clicked(self, page_index, ui):
        """处理NEXT按钮点击"""
        # 获取用户选择
        selected_option = None
        if ui.RadioButton.isChecked():
            selected_option = 0
        elif ui.RadioButton_2.isChecked():
            selected_option = 1
        elif ui.RadioButton_3.isChecked():
            selected_option = 2

        # 如果没有选择，不允许继续
        if selected_option is None:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title="请选择",
                content="请至少选择一个选项后再继续",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 保存用户选择
        if page_index == 0:  # 母语
            languages = ["Chinese", "English", "Japanese"]
            self.user_preferences["main_language"] = languages[selected_option]
        elif page_index == 1:  # 学习语言
            languages = ["English", "Chinese", "Japanese"]
            self.user_preferences["study_language"] = languages[selected_option]
        elif page_index == 2:  # 难度
            self.user_preferences["difficulty"] = selected_option + 1  # level1, level2, level3
        elif page_index == 3:  # 目标积分
            target_scores = [3000, 10000, 30000]
            self.user_preferences["target_score"] = target_scores[selected_option]

        # 前进到下一页或完成
        if page_index < 3:
            self.stack.setCurrentIndex(page_index + 1)
        else:
            # 完成所有问题，发射完成信号
            self.finished.emit(self.user_preferences)
