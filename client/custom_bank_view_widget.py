# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           SmoothScrollArea, InfoBar, InfoBarPosition)

# 添加common模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           'VocabSlayer_update_servier', 'common'))
from custom_bank_manager import CustomBankManager

class CustomBankViewWidget(QWidget):
    """自定义题库查看界面"""

    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.current_bank_id = None
        self.questions = []
        self.bank_data = None

        # 初始化数据库和题库管理器
        self.init_database()

        self.init_ui()

    def init_database(self):
        """初始化数据库连接和题库管理器"""
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
        """从数据库加载题库内容"""
        self.current_bank_id = bank_id

        if not self.bank_manager:
            InfoBar.error(
                title="错误",
                content="数据库未初始化",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        try:
            # 获取题库信息
            banks = self.bank_manager.get_user_banks(self.user_id)
            self.bank_data = next((b for b in banks if b['bank_id'] == bank_id), None)

            if not self.bank_data:
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

            # 获取题目列表
            questions = self.bank_manager.get_bank_questions(bank_id)
            self.questions = questions

            # 更新界面
            self.bank_title.setText(f"题库：{self.bank_data['bank_name']}")
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

    def get_bank_name(self, bank_id):
        """获取题库名称"""
        # 这里应该从服务器获取
        bank_names = {
            1: "计算机基础第一章",
            2: "数学公式汇总"
        }
        return bank_names.get(bank_id, "未知题库")

    def load_sample_questions(self):
        """加载示例题目"""
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
            },
            {
                'id': 4,
                'question': '什么是算法？算法的特征是什么？',
                'answer': '算法是解决特定问题的一系列清晰、有限的指令步骤。\n\n算法的特征：\n1. 有穷性：算法必须在执行有限步骤后终止\n2. 确定性：算法的每一步都有确切的含义，无歧义\n3. 可行性：算法的每一步都能通过有限次数的运算完成\n4. 输入：算法有0个或多个输入\n5. 输出：算法至少产生一个输出\n\n算法的效率通常用时间复杂度和空间复杂度来衡量。'
            },
            {
                'id': 5,
                'question': '什么是数据结构？常见的数据结构有哪些？',
                'answer': '数据结构是计算机中存储、组织数据的方式，它不仅包含数据元素本身，还包括数据元素之间的关系。\n\n常见的数据结构：\n\n1. 线性结构：\n   - 数组：连续存储的元素集合\n   - 链表：通过指针连接的节点序列\n   - 栈：后进先出(LIFO)的线性结构\n   - 队列：先进先出(FIFO)的线性结构\n\n2. 非线性结构：\n   - 树：分层组织的数据结构\n   - 二叉树：每个节点最多有两个子节点的树\n   - 图：由顶点和边组成的结构\n\n3. 哈希表：\n   - 通过哈希函数实现快速查找的结构\n\n选择合适的数据结构对程序效率至关重要。'
            }
        ]

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
        question_label = BodyLabel(f"问题：{question['question']}")
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
        answer_label = BodyLabel(f"答案：{question['answer']}")
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
            if self.bank_manager:
                success = self.bank_manager.delete_bank(self.current_bank_id, self.user_id)
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
        elif hasattr(self.parent, 'switch_to_view'):
            self.parent.switch_to_view()

    def back_to_manage(self):
        """返回管理界面"""
        if hasattr(self.parent, 'switch_to_custom_manage'):
            self.parent.switch_to_custom_manage()