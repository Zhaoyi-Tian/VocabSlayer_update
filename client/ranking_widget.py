# -*- coding: utf-8 -*-
"""
排行榜组件 - 显示用户学习统计排名
"""
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QAbstractItemView

from client.ranking import Ui_Form
from server.database_manager import DatabaseFactory


class RankingDataLoader(QThread):
    """后台加载排行榜数据的线程"""
    dataLoaded = pyqtSignal(list)
    errorOccurred = pyqtSignal(str)

    def __init__(self, username):
        super().__init__()
        self.username = username

    def run(self):
        try:
            db = DatabaseFactory.from_config_file('config.json')
            db.connect()
            ranking_data = db.get_ranking_data()
            db.close()
            self.dataLoaded.emit(ranking_data)
        except Exception as e:
            self.errorOccurred.emit(f"加载排行榜数据失败: {str(e)}")


class RankingWidget(QWidget):
    """排行榜界面组件"""

    # 排序选项配置
    SORT_OPTIONS = {
        "今日答题数": ("today_questions", True),
        "今日正确率": ("today_accuracy", True),
        "历史总答题数": ("total_questions", True),
        "历史总正确率": ("total_accuracy", True),
        "总积分": ("total_score", True),
        "学习天数": ("study_days", True),
    }

    # 表格列配置
    COLUMNS = [
        "用户名", "今日题数", "今日正确率", "总题数", "总正确率", "总积分", "学习天数"
    ]

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.username = username
        self.ranking_data = []
        self.current_sort_column = "total_questions"
        self.current_sort_reverse = True

        self._init_ui()
        self._connect_signals()
        self.load_data()

    def _init_ui(self):
        """初始化UI"""
        # 设置标题
        self.ui.TitleLabel.setText("学习排行榜")

        # 配置排序下拉框
        self.ui.ComboBox.addItems(list(self.SORT_OPTIONS.keys()))
        self.ui.ComboBox.setCurrentText("历史总答题数")

        # 配置表格
        self.ui.TableWidget.setColumnCount(len(self.COLUMNS))
        self.ui.TableWidget.setHorizontalHeaderLabels(self.COLUMNS)

        # 设置表格属性
        self.ui.TableWidget.setBorderVisible(True)
        self.ui.TableWidget.setBorderRadius(8)
        self.ui.TableWidget.setWordWrap(False)
        self.ui.TableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # 设置列宽
        header = self.ui.TableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 用户名
        self.ui.TableWidget.setColumnWidth(0, 120)

        for i in range(1, len(self.COLUMNS)):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

    def _connect_signals(self):
        """连接信号"""
        self.ui.ComboBox.currentTextChanged.connect(self._on_sort_changed)

    def _on_sort_changed(self, text):
        """排序方式改变"""
        if text in self.SORT_OPTIONS:
            sort_key, reverse = self.SORT_OPTIONS[text]
            self.current_sort_column = sort_key
            self.current_sort_reverse = reverse
            self._update_table()

    def load_data(self):
        """加载排行榜数据"""
        self.loader = RankingDataLoader(self.username)
        self.loader.dataLoaded.connect(self._on_data_loaded)
        self.loader.errorOccurred.connect(self._on_error)
        self.loader.start()

    def _on_data_loaded(self, data):
        """数据加载完成"""
        self.ranking_data = data
        self._update_table()

    def _on_error(self, error_msg):
        """数据加载失败"""
        print(f"[ERROR] {error_msg}")

    def _update_table(self):
        """更新表格显示"""
        if not self.ranking_data:
            return

        # 排序数据
        sorted_data = sorted(
            self.ranking_data,
            key=lambda x: x.get(self.current_sort_column, 0),
            reverse=self.current_sort_reverse
        )

        # 清空表格
        self.ui.TableWidget.setRowCount(0)

        # 填充数据
        for rank, user_data in enumerate(sorted_data, 1):
            row = self.ui.TableWidget.rowCount()
            self.ui.TableWidget.insertRow(row)

            username = user_data.get('username', '')
            is_current_user = (username == self.username)

            # 填充各列数据
            items = [
                username,
                str(user_data.get('today_questions', 0)),
                f"{user_data.get('today_accuracy', 0):.1f}%",
                str(user_data.get('total_questions', 0)),
                f"{user_data.get('total_accuracy', 0):.1f}%",
                f"{user_data.get('total_score', 0):.1f}",
                str(user_data.get('study_days', 0)),
            ]

            for col, item_text in enumerate(items):
                item = QTableWidgetItem(item_text)
                item.setTextAlignment(Qt.AlignCenter)

                # 高亮当前用户
                if is_current_user:
                    # 使用金色高亮当前用户
                    item.setBackground(QBrush(QColor(255, 215, 0, 80)))
                    item.setForeground(QBrush(QColor(184, 134, 11)))

                self.ui.TableWidget.setItem(row, col, item)

        # 滚动到当前用户
        self._scroll_to_current_user(sorted_data)

    def _scroll_to_current_user(self, sorted_data):
        """滚动到当前用户所在行"""
        for i, user_data in enumerate(sorted_data):
            if user_data.get('username') == self.username:
                self.ui.TableWidget.scrollToItem(
                    self.ui.TableWidget.item(i, 0)
                )
                break

    def refresh(self):
        """刷新排行榜数据"""
        self.load_data()
