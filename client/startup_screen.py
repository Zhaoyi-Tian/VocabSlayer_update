# coding:utf-8
import os
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import SplashScreen
from qframelesswindow import FramelessWindow


class Splash_Screen(FramelessWindow):

    def __init__(self):
        super().__init__()
        # 设置与登录页面相同的尺寸
        self.setFixedSize(714, 438)
        self.setWindowTitle('万识斩 - 加载中...')

        # 获取 client/resource 目录的图标路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(client_dir, "resource", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(256, 256))

        # 显示并居中
        self.show()
        self.center()

    def center(self):
        """将窗口居中显示的方法"""
        # 获取屏幕的几何信息（分辨率）
        screen_geometry = QApplication.desktop().screenGeometry()
        # 获取窗口的几何信息
        window_geometry = self.frameGeometry()
        # 计算居中位置：屏幕中心减去窗口一半大小
        window_geometry.moveCenter(screen_geometry.center())
        # 将窗口移动到计算好的位置
        self.move(window_geometry.topLeft())

    def close(self):
        """重写关闭方法，同时关闭SplashScreen"""
        if hasattr(self, 'splashScreen'):
            self.splashScreen.close()
        super().close()