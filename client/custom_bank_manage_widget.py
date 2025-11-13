# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFileDialog, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           ProgressBar, InfoBar, InfoBarPosition,
                           SmoothScrollArea, ScrollArea)

class CustomBankManageWidget(QWidget):
    """自定义题库管理界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.banks_data = []  # 存储题库数据
        self.init_ui()

    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域，让整个页面都可以滚动
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建滚动区域内的内容widget
        self.content_widget = QWidget()
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("自定义题库管理")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 上传区域
        upload_card = self.create_upload_card()
        layout.addWidget(upload_card)

        # 题库列表区域
        list_label = SubtitleLabel("我的题库")
        layout.addWidget(list_label)

        # 题库列表容器（不再需要滚动区域，因为整个页面都在滚动）
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(15)
        self.list_layout.setContentsMargins(10, 10, 10, 20)

        layout.addWidget(self.list_container)

        # 在底部添加一些空白空间
        layout.addStretch()

        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.content_widget)

        # 将滚动区域添加到主布局
        main_layout.addWidget(self.scroll_area)

        # 加载已存在的题库
        self.load_banks()

    def create_upload_card(self):
        """创建上传卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 上传说明
        upload_label = BodyLabel("上传文档生成自定义题库")
        upload_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(upload_label)

        # 支持格式说明
        format_label = BodyLabel("支持格式：Word文档 (.docx)、PDF文档 (.pdf)")
        format_label.setAlignment(Qt.AlignCenter)
        format_label.setStyleSheet("color: gray;")
        card_layout.addWidget(format_label)

        # 选择文件按钮
        self.select_file_btn = PrimaryPushButton(FluentIcon.FOLDER, "选择文件")
        self.select_file_btn.clicked.connect(self.select_file)
        card_layout.addWidget(self.select_file_btn, 0, Qt.AlignCenter)

        # 文件路径显示
        self.file_path_label = BodyLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: gray; padding: 5px;")
        card_layout.addWidget(self.file_path_label)

        # 题库名称输入
        name_layout = QHBoxLayout()
        name_label = BodyLabel("题库名称：")
        self.bank_name_edit = PushButton("未命名题库")
        self.bank_name_edit.clicked.connect(self.edit_bank_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.bank_name_edit)
        name_layout.addStretch()
        card_layout.addLayout(name_layout)

        # 描述输入
        desc_label = BodyLabel("题库描述（可选）：")
        card_layout.addWidget(desc_label)
        self.description_edit = PushButton("点击添加描述")
        self.description_edit.clicked.connect(self.edit_description)
        card_layout.addWidget(self.description_edit)

        # 生成题库按钮
        self.generate_btn = PrimaryPushButton(FluentIcon.ADD, "生成题库")
        self.generate_btn.clicked.connect(self.generate_bank)
        self.generate_btn.setEnabled(False)  # 初始禁用
        card_layout.addWidget(self.generate_btn, 0, Qt.AlignCenter)

        return card

    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文档",
            "",
            "文档文件 (*.docx *.pdf);;Word文档 (*.docx);;PDF文档 (*.pdf);;所有文件 (*.*)"
        )

        if file_path:
            self.selected_file = file_path
            file_name = os.path.basename(file_path)
            self.file_path_label.setText(f"已选择：{file_name}")
            self.file_path_label.setStyleSheet("color: black; padding: 5px;")

            # 自动设置题库名称
            bank_name = os.path.splitext(file_name)[0]
            self.bank_name_edit.setText(bank_name)
            self.current_bank_name = bank_name
            self.current_description = ""

            # 启用生成按钮
            self.generate_btn.setEnabled(True)

    def edit_bank_name(self):
        """编辑题库名称"""
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            "题库名称",
            "请输入题库名称：",
            text=self.bank_name_edit.text()
        )
        if ok and name:
            self.bank_name_edit.setText(name)
            self.current_bank_name = name

    def edit_description(self):
        """编辑题库描述"""
        from PyQt5.QtWidgets import QInputDialog
        desc, ok = QInputDialog.getMultiLineText(
            self,
            "题库描述",
            "请输入题库描述：",
            text=self.description_edit.text() if self.description_edit.text() != "点击添加描述" else ""
        )
        if ok:
            self.current_description = desc
            self.description_edit.setText(desc[:30] + "..." if len(desc) > 30 else desc)

    def generate_bank(self):
        """生成题库"""
        if not hasattr(self, 'selected_file'):
            QMessageBox.warning(self, "提示", "请先选择文件！")
            return

        # 模拟上传和生成过程
        self.select_file_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)

        # 创建进度条
        progress = ProgressBar()
        self.list_layout.insertWidget(0, progress)
        progress.setRange(0, 0)  # 不确定进度

        # 显示开始上传的信息条
        InfoBar.success(
            title="开始上传",
            content=f"正在上传并分析 {os.path.basename(self.selected_file)}...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 这里应该调用服务器接口上传文件
        # 暂时模拟成功
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.on_upload_complete(progress))

    def on_upload_complete(self, progress):
        """上传完成回调"""
        progress.deleteLater()

        # 模拟题库数据
        bank_data = {
            'id': len(self.banks_data) + 1,
            'name': self.current_bank_name,
            'description': self.current_description,
            'source_file': os.path.basename(self.selected_file),
            'question_count': 10,  # 模拟题目数量
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'questions': []  # 这里应该从服务器获取
        }

        self.banks_data.append(bank_data)

        # 添加到界面
        bank_card = self.create_bank_card(bank_data)
        self.list_layout.addWidget(bank_card)

        # 显示成功信息
        InfoBar.success(
            title="生成成功",
            content=f"题库 '{self.current_bank_name}' 已生成，共10道题目！",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 重置上传区域
        self.reset_upload_area()

    def reset_upload_area(self):
        """重置上传区域"""
        self.select_file_btn.setEnabled(True)
        self.file_path_label.setText("未选择文件")
        self.file_path_label.setStyleSheet("color: gray; padding: 5px;")
        self.bank_name_edit.setText("未命名题库")
        self.description_edit.setText("点击添加描述")
        self.generate_btn.setEnabled(False)
        if hasattr(self, 'selected_file'):
            delattr(self, 'selected_file')

    def create_bank_card(self, bank_data):
        """创建题库卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)

        # 题库名称
        name_label = SubtitleLabel(bank_data['name'])
        card_layout.addWidget(name_label)

        # 描述（如果有）
        if bank_data.get('description'):
            desc_label = BodyLabel(bank_data['description'])
            desc_label.setStyleSheet("color: gray; margin-bottom: 5px;")
            card_layout.addWidget(desc_label)

        # 信息
        info_layout = QHBoxLayout()

        file_label = BodyLabel(f"来源：{bank_data['source_file']}")
        file_label.setStyleSheet("color: gray; font-size: 12px;")
        info_layout.addWidget(file_label)

        info_layout.addStretch()

        count_label = BodyLabel(f"题目数：{bank_data['question_count']}")
        count_label.setStyleSheet("color: gray; font-size: 12px;")
        info_layout.addWidget(count_label)

        date_label = BodyLabel(f"创建时间：{bank_data['created_at']}")
        date_label.setStyleSheet("color: gray; font-size: 12px;")
        info_layout.addWidget(date_label)

        card_layout.addLayout(info_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()

        # 开始答题按钮
        start_btn = PrimaryPushButton(FluentIcon.PLAY, "开始答题")
        start_btn.clicked.connect(lambda: self.start_bank(bank_data['id']))
        btn_layout.addWidget(start_btn)

        # 查看题目按钮
        view_btn = PushButton(FluentIcon.DOCUMENT, "查看题目")
        view_btn.clicked.connect(lambda: self.view_bank(bank_data['id']))
        btn_layout.addWidget(view_btn)

        # 删除按钮
        delete_btn = PushButton(FluentIcon.DELETE, "删除")
        delete_btn.clicked.connect(lambda: self.delete_bank(bank_data['id']))
        btn_layout.addWidget(delete_btn)

        card_layout.addLayout(btn_layout)

        return card

    def start_bank(self, bank_id):
        """开始答题"""
        # 切换到自定义题库答题界面
        if self.parent:
            self.parent.switch_to_custom_quiz(bank_id)

    def view_bank(self, bank_id):
        """查看题库"""
        # 切换到view界面并显示该题库
        if self.parent:
            self.parent.switch_to_view_custom_bank(bank_id)

    def delete_bank(self, bank_id):
        """删除题库"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个题库吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 从列表中移除
            self.banks_data = [b for b in self.banks_data if b['id'] != bank_id]

            # 重新加载界面
            self.refresh_banks()

            InfoBar.success(
                title="删除成功",
                content="题库已被删除",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def refresh_banks(self):
        """刷新题库列表"""
        # 清除当前列表（保留底部可能存在的stretch）
        for i in reversed(range(self.list_layout.count())):
            item = self.list_layout.itemAt(i)
            child = item.widget()
            if child and not isinstance(child, type(None)):
                child.deleteLater()
            elif item.spacerItem():
                # 如果是空白占位符，先不删除，最后统一添加
                continue

        # 重新添加题库卡片
        for bank in self.banks_data:
            card = self.create_bank_card(bank)
            self.list_layout.addWidget(card)

    def load_banks(self):
        """加载已存在的题库"""
        # 这里应该从服务器加载用户的题库
        # 暂时添加一些示例数据
        sample_banks = [
            {
                'id': 1,
                'name': "计算机基础第一章",
                'description': "计算机基础知识概论",
                'source_file': "计算机基础.pdf",
                'question_count': 15,
                'created_at': "2024-01-15 14:30",
                'questions': []
            },
            {
                'id': 2,
                'name': "数学公式汇总",
                'description': "",
                'source_file': "数学公式.docx",
                'question_count': 8,
                'created_at': "2024-01-16 10:15",
                'questions': []
            },
            {
                'id': 3,
                'name': "英语语法要点",
                'description': "重要英语语法知识整理",
                'source_file': "英语语法.pdf",
                'question_count': 20,
                'created_at': "2024-01-17 09:20",
                'questions': []
            },
            {
                'id': 4,
                'name': "历史复习资料",
                'description': "中国历史重点内容",
                'source_file': "历史复习.docx",
                'question_count': 12,
                'created_at': "2024-01-18 16:45",
                'questions': []
            },
            {
                'id': 5,
                'name': "物理实验报告",
                'description': "高中物理实验总结",
                'source_file': "物理实验.pdf",
                'question_count': 18,
                'created_at': "2024-01-19 11:30",
                'questions': []
            }
        ]

        for bank in sample_banks:
            self.banks_data.append(bank)
            card = self.create_bank_card(bank)
            self.list_layout.addWidget(card)

        # 在底部添加足够的空白空间
        self.list_layout.addStretch()
        self.list_layout.addStretch()