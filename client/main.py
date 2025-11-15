import os
import shutil
import sys

# 添加项目根目录到 Python 路径，以便导入 server 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QApplication, QDialog
from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, setThemeColor
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow.utils import getSystemAccentColor

from client.main_window import Window, LoginDialog
from client.startup_screen import Splash_Screen

if __name__ == '__main__':
    # 必须在创建 QApplication 之前设置高DPI属性
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    if sys.platform in ["win32", "darwin"]:
        setThemeColor(getSystemAccentColor(), save=False)

    # 1. 显示登录对话框
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        username = login_dialog.ui.LineEdit_2.text().strip()

        # 2. 登录成功后显示加载页面
        splash_screen = Splash_Screen()
        splash_screen.show()

        # 3. 使用QTimer异步创建主窗口
        # 将main_window声明为列表，以便在闭包中修改
        main_window = [None]

        def create_main_window():
            try:
                print(f"[DEBUG] 开始创建主窗口，用户名: {username}")
                main_window[0] = Window(username)
                print(f"[DEBUG] 主窗口创建成功")

                # 关闭加载页面并显示主窗口
                splash_screen.close()
                main_window[0].show()
            except Exception as e:
                print(f"[DEBUG] 创建主窗口失败: {e}")
                import traceback
                traceback.print_exc()
                splash_screen.close()

        # 延迟100ms后创建主窗口，让加载页面先显示
        QTimer.singleShot(100, create_main_window)

        # 4. 运行应用
        app.exec_()
    else:
        # 用户关闭了登录窗口，退出程序
        sys.exit(0)

