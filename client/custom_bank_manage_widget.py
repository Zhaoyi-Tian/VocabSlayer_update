# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFileDialog, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           ProgressBar, InfoBar, InfoBarPosition,
                           SmoothScrollArea, ScrollArea)

# 添加common模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           'VocabSlayer_update_servier', 'common'))
from custom_bank_manager import CustomBankManager

class CustomBankManageWidget(QWidget):
    """自定义题库管理界面"""

    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.banks_data = []  # 存储题库数据
        self.current_worker = None  # 当前处理线程

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
        # 检查是否选择了文件
        if not hasattr(self, 'selected_file'):
            QMessageBox.warning(self, "提示", "请先选择文件！")
            return

        # 检查数据库连接
        if not self.db or not self.user_id:
            QMessageBox.critical(self, "错误", "数据库连接失败！")
            return

        # 检查API密钥
        if not self.api_key:
            QMessageBox.warning(self, "提示", "请先在设置中配置DeepSeek API密钥！")
            return

        # 禁用按钮，防止重复点击
        self.select_file_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)

        # 创建并显示进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.list_layout.insertWidget(0, self.progress_bar)

        # 显示开始处理的信息条
        InfoBar.info(
            title="开始处理",
            content=f"正在解析文档 {os.path.basename(self.selected_file)}...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        try:
            # 创建处理线程
            self.current_worker = self.bank_manager.create_bank_from_document(
                file_path=self.selected_file,
                bank_name=self.current_bank_name,
                user_id=self.user_id,
                progress_callback=self.on_progress_update,
                log_callback=self.on_log_message
            )

            # 连接信号
            self.current_worker.processing_completed.connect(self.on_processing_completed)
            self.current_worker.error_occurred.connect(self.on_processing_error)
            self.current_worker.question_generated.connect(self.on_question_generated)

            # 启动处理线程
            self.current_worker.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建处理线程失败：{str(e)}")
            self.reset_upload_area()

    def on_progress_update(self, percentage: int, status: str):
        """更新进度"""
        self.progress_bar.setValue(percentage)
        # 可以更新状态标签

    def on_log_message(self, message: str):
        """处理日志消息"""
        print(f"[处理日志] {message}")

    def on_question_generated(self, question: dict):
        """单个题目生成完成"""
        # 可以显示已生成的题目数量
        pass

    def on_processing_completed(self, result: dict):
        """处理完成回调"""
        # 移除进度条
        self.progress_bar.deleteLater()
        self.current_worker = None

        if result.get('status') == 'completed':
            # 成功完成
            bank_id = result.get('bank_id')
            question_count = result.get('total_questions', 0)

            # 显示成功信息
            InfoBar.success(
                title="生成成功",
                content=f"题库 '{self.current_bank_name}' 已生成，共 {question_count} 道题目！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

            # 重新加载题库列表
            self.load_banks()
        elif result.get('status') == 'skipped':
            # 文档已处理过
            InfoBar.info(
                title="提示",
                content="该文档已经处理过，请检查题库列表",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            # 处理失败
            error_msg = result.get('error_message', '未知错误')
            InfoBar.error(
                title="生成失败",
                content=f"错误：{error_msg}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

        # 重置上传区域
        self.reset_upload_area()

    def on_processing_error(self, error_message: str):
        """处理错误回调"""
        # 移除进度条
        if hasattr(self, 'progress_bar'):
            self.progress_bar.deleteLater()
        self.current_worker = None

        # 显示错误信息
        InfoBar.error(
            title="处理失败",
            content=f"错误：{error_message}",
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
            # 调用后端删除
            if self.bank_manager:
                success = self.bank_manager.delete_bank(bank_id, self.user_id)
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
                    # 重新加载题库列表
                    self.load_banks()
                else:
                    InfoBar.error(
                        title="删除失败",
                        content="删除题库时出错",
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
        """从数据库加载已存在的题库"""
        # 清除当前题库数据
        self.banks_data.clear()

        # 清除界面上的所有卡片（保留底部的空白空间）
        # 从后往前删除，避免索引问题
        for i in reversed(range(self.list_layout.count())):
            item = self.list_layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, CardWidget):
                widget.deleteLater()

        # 从数据库加载题库
        if self.bank_manager and self.user_id:
            try:
                banks = self.bank_manager.get_user_banks(self.user_id)

                if banks:
                    for bank in banks:
                        # 转换数据库格式到界面格式
                        bank_data = {
                            'id': bank['bank_id'],
                            'name': bank['bank_name'],
                            'description': bank.get('description', ''),
                            'source_file': os.path.basename(bank.get('source_file', '')),
                            'question_count': bank.get('question_count', 0),
                            'created_at': bank['created_at'].strftime("%Y-%m-%d %H:%M") if bank['created_at'] else '',
                            'status': bank.get('processing_status', 'completed')
                        }

                        self.banks_data.append(bank_data)
                        card = self.create_bank_card(bank_data)
                        self.list_layout.addWidget(card)
                else:
                    # 显示空状态
                    empty_label = BodyLabel("还没有题库，上传文档创建第一个吧！")
                    empty_label.setAlignment(Qt.AlignCenter)
                    empty_label.setStyleSheet("color: gray; padding: 40px;")
                    self.list_layout.addWidget(empty_label)

            except Exception as e:
                print(f"加载题库失败: {e}")
                # 显示错误状态
                error_label = BodyLabel(f"加载题库失败: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: red; padding: 40px;")
                self.list_layout.addWidget(error_label)
        else:
            # 显示未连接状态
            empty_label = BodyLabel("请先配置API密钥后创建题库")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: gray; padding: 40px;")
            self.list_layout.addWidget(empty_label)

        # 在底部添加空白空间
        self.list_layout.addStretch()