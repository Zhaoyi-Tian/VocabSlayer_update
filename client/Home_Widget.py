
import os
from datetime import datetime, date,timedelta

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import FluentIcon, ConfigItem, qconfig
from server.my_test import VocabularyLearningSystem
from client.home import Ui_home_widget
from client.appcard import AppCard
class HomeWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__()

        self.parent = parent
        self.configitem = self.parent.cfg.total_num
        self.ui = Ui_home_widget()
        self.ui.setupUi(self)
        self.card1=AppCard(
            FluentIcon.CHECKBOX,
            "常规训练",
            "选择难度从题库中抽题训练",
            self
        )
        self.card2 = AppCard(
            FluentIcon.LABEL,
            "复习训练",
            "从已做过的题中抽题训练",
            self
        )
        # 获取 client/resource 目录的 deepseek 图标路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        deepseek_icon = os.path.join(client_dir, "resource", "deepseek.png")
        self.card4 = AppCard(
            QIcon(deepseek_icon),
            "deepseek",
            "和ai探讨问题",
            self
        )
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(15)
        content_layout.addWidget(self.card1)
        content_layout.addWidget(self.card2)
        content_layout.addWidget(self.card4)
        self.ui.SmoothScrollArea.setWidget(content_widget)
        self.ui.SmoothScrollArea.setWidgetResizable(True)
        # 从父窗口获取用户名并传递给 VocabularyLearningSystem
        username = self.parent.username if hasattr(self.parent, 'username') else None
        self.VLS = VocabularyLearningSystem(username=username)
        self.ui.HorizontalFlipView.addImage(self.VLS.show_day_stats())
        self.ui.HorizontalFlipView.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.ui.HorizontalFlipView.setItemSize(QSize(561, 270))
        self.ui.HorizontalFlipView.setFixedSize(QSize(561, 270))
        self.card1.clicked.connect(lambda:self.parent.switchTo(self.parent.exam1Interface))
        self.card2.clicked.connect(lambda: self.parent.switchTo(self.parent.exam2Interface))
        self.card4.clicked.connect(lambda: self.parent.switchTo(self.parent.aiInterface))
        self.card1.openButton.clicked.connect(lambda:self.parent.switchTo(self.parent.exam1Interface))
        self.card2.openButton.clicked.connect(lambda: self.parent.switchTo(self.parent.exam2Interface))
        self.card4.openButton.clicked.connect(lambda: self.parent.switchTo(self.parent.aiInterface))
        # 获取今天的日期
        self.today = date.today()
        self.todayn=self.today.strftime('%Y年%m月%d日')
        # 获取星期几（0-6，0表示周一）
        self.weekday_num = self.today.weekday()
        # 获取中文星期几
        weekday_chinese = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][self.weekday_num]
        self.ui.StrongBodyLabel_2.setText(f"今天是{self.todayn},{weekday_chinese}")
        self.ui.ToolButton.clicked.connect(self.flush)
        self.ui.ToolButton.setIcon(FluentIcon.UPDATE)
        self.ui.ProgressBar.setValue(int(self.configitem.value/3000*100))
        self.ui.StrongBodyLabel.setText(f"{int(self.configitem.value)}/3000")
        self.ratio=1
        # 检查是否有日期数据
        if self.VLS.dates:
            last_date = self._to_date(self.VLS.dates[-1])
            if last_date == self.today:
                self.lastflash = self.VLS.total[-1]
            else:
                self.lastflash = 0
        else:
            self.lastflash=0
        self.flush()

    def _to_date(self, date_obj):
        """将任意日期对象转换为 date 对象"""
        if hasattr(date_obj, 'to_pydatetime'):
            # pandas Timestamp
            return date_obj.to_pydatetime().date()
        elif isinstance(date_obj, str):
            # 字符串格式
            return datetime.strptime(date_obj, "%Y-%m-%d").date()
        elif hasattr(date_obj, 'date'):
            # datetime 对象
            return date_obj.date()
        else:
            # 已经是 date 对象
            return date_obj

    def flush(self):
        username = self.parent.username if hasattr(self.parent, 'username') else None
        self.VLS = VocabularyLearningSystem(username=username)

        # 使用更简单的方式：重新初始化整个 home 界面
        # 保存旧的 HorizontalFlipView 的父布局位置
        try:
            # 尝试直接清除并重新加载图片
            # 先隐藏再显示，避免闪烁
            self.ui.HorizontalFlipView.hide()

            # 保存位置和尺寸信息
            old_geometry = self.ui.HorizontalFlipView.geometry()
            old_size = self.ui.HorizontalFlipView.size()
            old_item_size = self.ui.HorizontalFlipView.itemSize
            old_aspect_mode = self.ui.HorizontalFlipView.aspectRatioMode
            old_object_name = self.ui.HorizontalFlipView.objectName()

            # 删除旧组件
            old_flip_view = self.ui.HorizontalFlipView
            old_flip_view.setParent(None)
            old_flip_view.deleteLater()

            # 创建新组件
            from qfluentwidgets import HorizontalFlipView
            self.ui.HorizontalFlipView = HorizontalFlipView(self)
            self.ui.HorizontalFlipView.setObjectName(old_object_name)
            self.ui.HorizontalFlipView.setGeometry(old_geometry)
            self.ui.HorizontalFlipView.setFixedSize(old_size)
            self.ui.HorizontalFlipView.setItemSize(old_item_size)
            self.ui.HorizontalFlipView.setAspectRatioMode(old_aspect_mode)
            self.ui.HorizontalFlipView.addImage(self.VLS.show_day_stats())
            self.ui.HorizontalFlipView.show()

        except Exception as e:
            print(f"[ERROR] Failed to refresh HorizontalFlipView: {e}")
            import traceback
            traceback.print_exc()

        self.ui.SubtitleLabel.setText(f"您已连续练习{self.count_consecutive_days(self.VLS.dates)}天")
        self.ratio = 1 + self.count_consecutive_days(self.VLS.dates) * 0.1
        # 检查是否有日期数据
        if self.VLS.dates:
            last_date = self._to_date(self.VLS.dates[-1])
            if last_date == self.today:
                self.ui.HyperlinkLabel_2.setText(f"{self.VLS.total[-1]}个")
                self.configitem.value +=self.VLS.total[-1]-self.lastflash
                self.lastflash = self.VLS.total[-1]
            else:
                self.ui.HyperlinkLabel_2.setText("0个")
        else:
            self.ui.HyperlinkLabel_2.setText("0个")
        self.ui.HyperlinkLabel.setText(f"x{self.ratio:.2f}")

        self.ui.ProgressBar.setValue(int(self.configitem.value/3000*100))
        self.ui.StrongBodyLabel.setText(f"{int(self.configitem.value)}/3000")
        # 不再保存配置到本地文件

        # 刷新收藏夹数据
        if hasattr(self.parent, 'dataInterface'):
            self.parent.dataInterface.flush()
            print("[DEBUG] dataInterface flushed from homeInterface")
    def count_consecutive_days(self,date_list):
        # 1. 日期排序（确保升序）
        sorted_dates = sorted(date_list,reverse=True)

        # 2. 转换为datetime对象并检查连续性
        prev_date = None
        consecutive_days = 0

        for date_obj in sorted_dates:
            # 处理 pandas Timestamp 或字符串
            if hasattr(date_obj, 'to_pydatetime'):
                # pandas Timestamp
                curr_date = date_obj.to_pydatetime().date()
            elif isinstance(date_obj, str):
                # 字符串格式
                curr_date = datetime.strptime(date_obj, "%Y-%m-%d").date()
            else:
                # 已经是 date 对象
                curr_date = date_obj if hasattr(date_obj, 'year') else datetime.strptime(str(date_obj), "%Y-%m-%d").date()

            # 处理第一个日期
            if prev_date is None:
                prev_date = curr_date
                consecutive_days = 1
                continue

            # 计算日期间隔
            delta = prev_date - curr_date
            if delta == timedelta(days=1):
                # 日期连续，天数+1
                consecutive_days += 1
                prev_date = curr_date
            else:
                # 日期不连续，返回当前连续天数
                return consecutive_days

        return consecutive_days
