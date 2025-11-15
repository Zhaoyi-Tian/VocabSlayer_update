"""
网络模式的自定义题库管理界面
通过网络API与服务器通信
"""
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFileDialog, QMessageBox, QScrollArea, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from qfluentwidgets import (FluentIcon, CardWidget, SubtitleLabel,
                           BodyLabel, PrimaryPushButton, PushButton,
                           ProgressBar, InfoBar, InfoBarPosition,
                           SmoothScrollArea, ScrollArea)

# 导入网络客户端
from network_client import NetworkBankManager, DocumentUploadThread, ProgressMonitorThread


class CustomBankManageWidgetNetwork(QWidget):
    """自定义题库管理界面 - 网络模式"""

    def __init__(self, parent=None, username=None, server_url=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.banks_data = []  # 存储题库数据
        self.current_worker = None  # 当前上传线程
        self.network_manager = None
        self.user_id = None
        self.api_key = None

        # 服务器配置
        self.server_url = server_url or "http://10.129.211.118:5000"

        # 初始化网络管理器
        self.init_network()

        # 获取用户的API密钥
        self.get_user_api_key()

        self.init_ui()

    def init_network(self):
        """初始化网络连接"""
        try:
            # 创建网络管理器
            self.network_manager = NetworkBankManager(self.server_url)

            # 检查服务器连接
            if not self.network_manager.check_server_health():
                print("无法连接到服务器")
                self.network_manager = None
                return

            print(f"已连接到服务器: {self.server_url}")

            # 获取用户ID和API密钥
            self.user_id = None  # 将在父类中设置
            self.api_key = ""  # 需要用户配置

        except Exception as e:
            print(f"初始化网络连接失败: {e}")
            self.network_manager = None

    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域
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
        title = SubtitleLabel("自定义题库管理（网络模式）")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 服务器状态显示
        self.server_status_label = BodyLabel("服务器状态：未连接")
        if self.network_manager:
            self.server_status_label.setText(f"服务器状态：已连接 ({self.server_url})")
        self.server_status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.server_status_label)

        # API密钥状态提示
        if not self.api_key:
            api_key_label = BodyLabel("⚠️ 请先在设置中配置DeepSeek API密钥")
            api_key_label.setStyleSheet("color: #FF9500; font-size: 12px; padding: 5px;")
            api_key_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(api_key_label)

        # 上传区域
        upload_card = self.create_upload_card()
        layout.addWidget(upload_card)

        # 题库列表区域
        list_label = SubtitleLabel("我的题库")
        layout.addWidget(list_label)

        # 题库列表容器
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

        # 加载题库列表
        QTimer.singleShot(100, self.load_banks)

    def set_user_id(self, user_id):
        """设置用户ID"""
        self.user_id = user_id
        print(f"[INFO] 网络模式设置用户ID: {user_id}")

    def create_upload_card(self):
        """创建上传卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 上传说明
        upload_label = BodyLabel("上传文档到服务器生成自定义题库")
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
        self.generate_btn = PrimaryPushButton(FluentIcon.ADD, "上传并生成题库")
        self.generate_btn.clicked.connect(self.generate_bank)
        self.generate_btn.setEnabled(False)  # 初始禁用
        card_layout.addWidget(self.generate_btn, 0, Qt.AlignCenter)

        return card

    def get_user_api_key(self):
        """从数据库获取用户的API密钥"""
        try:
            # 从父窗口获取数据库连接
            if self.parent and hasattr(self.parent, 'username'):
                from server.database_manager import DatabaseFactory
                db = DatabaseFactory.from_config_file('config.json')
                db.connect()

                # 获取用户配置
                user_config = db.get_user_config(self.username)
                if user_config:
                    self.api_key = user_config.get('api_key', '')
                    if self.api_key:
                        print(f"[INFO] 已获取用户的API密钥")
                    else:
                        print(f"[WARNING] 用户未配置API密钥")
                        InfoBar.warning(
                            title="API密钥未配置",
                            content="请先在设置中配置DeepSeek API密钥",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
                db.close()
        except Exception as e:
            print(f"[ERROR] 获取API密钥失败: {e}")

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
        # 检查条件
        if not hasattr(self, 'selected_file'):
            QMessageBox.warning(self, "提示", "请先选择文件！")
            return

        if not self.network_manager:
            QMessageBox.critical(self, "错误", "未连接到服务器！")
            return

        if not self.api_key:
            QMessageBox.warning(self, "提示", "请先配置DeepSeek API密钥！")
            return

        if self.user_id is None:
            QMessageBox.warning(self, "提示", "用户ID未设置！")
            return

        # 禁用按钮
        self.select_file_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)

        # 创建进度显示容器
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(10, 10, 10, 10)
        progress_layout.setSpacing(10)

        # 创建进度文本标签
        self.progress_text = BodyLabel("准备上传...")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("font-size: 14px; color: #333; margin-bottom: 5px;")
        progress_layout.addWidget(self.progress_text)

        # 创建进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)

        # 插入到题库列表的顶部
        self.list_layout.insertWidget(0, progress_container)
        self.progress_container = progress_container

        # 显示开始上传的信息条
        InfoBar.info(
            title="开始上传",
            content=f"正在上传文档到服务器 {os.path.basename(self.selected_file)}...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 创建上传线程
        self.current_worker = DocumentUploadThread(
            network_manager=self.network_manager,
            file_path=self.selected_file,
            user_id=self.user_id,
            bank_name=self.current_bank_name,
            description=self.current_description,
            api_key=self.api_key
        )

        # 连接信号
        self.current_worker.progress_updated.connect(self.on_progress_update)
        self.current_worker.upload_completed.connect(self.on_upload_completed)
        self.current_worker.error_occurred.connect(self.on_upload_error)

        # 启动上传
        self.current_worker.start()

    def on_progress_update(self, percentage: int, status: str):
        """更新进度"""
        self.progress_bar.setValue(percentage)
        self.progress_text.setText(status)

    def on_upload_completed(self, result: dict):
        """上传完成回调"""
        # 检查是否需要开始监控实时进度
        if result.get('success') and result.get('task_id'):
            # 获取task_id，开始SSE监控
            task_id = result.get('task_id')
            self.progress_text.setText("文件上传成功，开始处理文档...")

            # 创建进度监控线程
            self.progress_monitor = ProgressMonitorThread(self.server_url, task_id)

            # 连接SSE信号
            self.progress_monitor.progress_updated.connect(self.on_sse_progress)
            self.progress_monitor.task_completed.connect(self.on_task_completed)
            self.progress_monitor.task_error.connect(self.on_task_error)

            # 启动监控
            self.progress_monitor.start()
        else:
            # 直接完成，无需监控
            self.handle_final_result(result)

    def on_sse_progress(self, progress_data: str):
        """处理SSE进度更新"""
        try:
            import json
            data = json.loads(progress_data)

            # 获取进度信息
            progress = data.get('progress', 0)
            message = data.get('message', '')
            current_step = data.get('current_step', '')
            details = data.get('details', {})

            # 构建详细的进度信息
            progress_text = message
            if current_step:
                progress_text += f"\n步骤: {current_step}"

            # 添加详细信息
            if details:
                if 'chunk_index' in details and 'total_chunks' in details:
                    progress_text += f"\n进度: {details['chunk_index']}/{details['total_chunks']} 个文本块"

            self.progress_text.setText(progress_text)
            self.progress_text.setWordWrap(True)  # 允许换行

            # 更新进度条 - 使用服务器返回的进度值
            self.progress_bar.setValue(int(progress))

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"处理SSE进度更新失败: {e}")

    def on_task_completed(self, result_data: str):
        """任务完成"""
        try:
            import json
            data = json.loads(result_data)
            self.progress_text.setText("题库生成完成！")
            self.progress_bar.setValue(100)

            # 延迟处理结果，让用户看到完成状态
            QTimer.singleShot(500, lambda: self.handle_final_result(data))

        except json.JSONDecodeError:
            self.handle_final_result({'success': False, 'error': '解析结果失败'})

    def on_task_error(self, error_data: str):
        """任务错误"""
        try:
            import json
            data = json.loads(error_data)
            error_msg = data.get('error', '未知错误')
            self.progress_text.setText(f"处理失败: {error_msg}")

        except json.JSONDecodeError:
            error_msg = "处理失败"
            self.progress_text.setText(error_msg)

        # 显示错误信息
        InfoBar.error(
            title="处理失败",
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 延迟清理，让用户看到错误状态
        QTimer.singleShot(2000, self.cleanup_progress)

    def handle_final_result(self, result: dict):
        """处理最终结果"""
        # 停止监控线程
        if hasattr(self, 'progress_monitor'):
            self.progress_monitor.stop()
            self.progress_monitor.wait()
            self.progress_monitor = None

        # 移除进度显示
        self.cleanup_progress()

        self.current_worker = None

        if result.get('success'):
            if result.get('status') == 'completed':
                # 成功完成
                question_count = result.get('question_count', 0)
                InfoBar.success(
                    title="生成成功",
                    content=f"题库 '{self.current_bank_name}' 已生成，共 {question_count} 道题目！",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            elif result.get('status') == 'skipped':
                # 文档已处理过
                question_count = result.get('question_count', 0)
                InfoBar.info(
                    title="提示",
                    content=f"该文档已经处理过，共 {question_count} 道题目",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        else:
            # 处理失败
            error_msg = result.get('error', '未知错误')
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

        # 重新加载题库列表
        QTimer.singleShot(1000, self.load_banks)

    def cleanup_progress(self):
        """清理进度显示"""
        if hasattr(self, 'progress_container'):
            self.progress_container.deleteLater()
            self.progress_container = None

    def cleanup_progress_and_reset(self):
        """清理进度显示并重置上传区域"""
        self.cleanup_progress()
        self.current_worker = None
        self.reset_upload_area()

    def on_upload_error(self, error_message: str):
        """上传错误回调"""
        # 更新进度文本
        if hasattr(self, 'progress_text'):
            self.progress_text.setText(f"上传失败: {error_message}")

        # 显示错误信息
        InfoBar.error(
            title="上传失败",
            content=f"错误：{error_message}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 延迟清理，让用户看到错误状态
        QTimer.singleShot(2000, self.cleanup_progress_and_reset)

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

        file_label = BodyLabel(f"来源：{bank_data.get('source_file', '')}")
        file_label.setStyleSheet("color: gray; font-size: 12px;")
        info_layout.addWidget(file_label)

        info_layout.addStretch()

        count_label = BodyLabel(f"题目数：{bank_data.get('question_count', 0)}")
        count_label.setStyleSheet("color: gray; font-size: 12px;")
        info_layout.addWidget(count_label)

        date_label = BodyLabel(f"创建时间：{bank_data.get('created_at', '')}")
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
            # 调用网络删除
            if self.network_manager and self.user_id:
                success = self.network_manager.delete_bank(bank_id, self.user_id)
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

    def load_banks(self):
        """从服务器加载题库列表"""
        # 清除当前题库数据
        self.banks_data.clear()

        # 清除界面上的所有卡片
        for i in reversed(range(self.list_layout.count())):
            item = self.list_layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, CardWidget):
                widget.deleteLater()

        # 从服务器加载题库
        if self.network_manager and self.user_id:
            try:
                banks = self.network_manager.get_user_banks(self.user_id)

                if banks:
                    for bank in banks:
                        # 转换服务器格式到界面格式
                        bank_data = {
                            'id': bank['bank_id'],
                            'name': bank['bank_name'],
                            'description': bank.get('description', ''),
                            'source_file': os.path.basename(bank.get('source_file', '')),
                            'question_count': bank.get('question_count', 0),
                            'created_at': bank.get('created_at', ''),
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
            empty_label = BodyLabel("未连接到服务器或用户未登录")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: gray; padding: 40px;")
            self.list_layout.addWidget(empty_label)

        # 在底部添加空白空间
        self.list_layout.addStretch()