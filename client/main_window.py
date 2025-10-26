import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QApplication, QWidget, QDialog
from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, SettingCardGroup, qconfig, \
    ColorSettingCard, setThemeColor, FluentIcon, HyperlinkCard
from qfluentwidgets import FluentIcon as FIF

from client.Home_Widget import HomeWidget
from client.Review_training import reviewContainer
from client.data_view_widget import dataWidget
from client.setAPI import StrSettingCard
from client.login import Ui_Dialog
from client.users_manager import authenticate_user, create_user, user_exists
from client.userConfig import UserConfig
from client.startup_screen import Splash_Screen
from client.quiz import Ui_quiz
from client.deepseek import Ai_Widget
from client.routine_training import ExamContainer

class LoginDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        # 初始化错误标签为隐藏状态
        self.ui.label_2.setVisible(False)
        self.ui.label_2.setStyleSheet("color: red;")
        # 连接登录按钮点击事件
        self.ui.PrimaryPushButton.clicked.connect(self.check_credentials)
        self.setWindowTitle("万词斩")
        # 获取 client/resource 目录的图标路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(client_dir, "resource", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def check_credentials(self):
        # 获取输入的用户名和密码
        username = self.ui.LineEdit_2.text().strip()
        password = self.ui.LineEdit.text().strip()
        # 清除之前的错误提示
        self.ui.label_2.setVisible(False)

        if username == "":
            self.ui.label_2.setText("请输入用户名")
            self.ui.label_2.setVisible(True)
            return

        # 检查用户是否存在
        if user_exists(username):
            # 用户已存在，验证密码
            if authenticate_user(username, password):
                print(f"[DEBUG] User {username} authenticated successfully")
                self.accept()
            else:
                # 密码错误
                self.ui.label_2.setText("密码错误！")
                self.ui.label_2.setVisible(True)
                self.ui.LineEdit.setText("")
        else:
            # 用户不存在，创建新用户
            if create_user(username, password):
                print(f"[DEBUG] New user {username} created")
                self.accept()
            else:
                # 创建失败
                self.ui.label_2.setText("创建用户失败，请稍后重试")
                self.ui.label_2.setVisible(True)

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # 必须给子界面设置全局唯一的对象名
        self.setObjectName(text.replace(' ', '-'))


class Window(FluentWindow):
    """ 主界面 """
    def __init__(self,User):
        super().__init__()
        ###设置颜色卡添加部分
        self.cfg = UserConfig()
        self.username = User
        # 不再使用本地 JSON 文件存储用户配置，改为使用内存配置
        # 用户配置将在数据库中管理，或者使用默认值
        # 创建设置卡片
        self.cardcolor = ColorSettingCard(
            configItem=self.cfg.primaryColor,
            icon=FIF.PALETTE,
            title="主题色",
            content="调整应用主题的颜色",
            enableAlpha=True,
            parent=self
        )
        self.APIcard=StrSettingCard(
            '',
            configItem=self.cfg.API,
            icon=FluentIcon.ADD_TO,
            title="API",
            content="调整AI的API",
            enableAlpha=True,
            parent=self)
        # 获取 client/resource 目录的 deepseek 图标路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        deepseek_icon = os.path.join(client_dir, "resource", "deepseek.png")
        self.deepseekcard = HyperlinkCard(
            url="https://platform.deepseek.com/usage",
            text="打开deepseekAPI页面",
            icon=deepseek_icon,
            title="getAPI",
            content="获得属于自己的deepseek的API，并启用ai功能"
        )
        # 创建子界面
        self.homeInterface = HomeWidget(self)
        self.homeInterface.setObjectName("home")
        self.exam1Interface = ExamContainer(self)
        self.exam1Interface.setObjectName("routine training")
        self.exam2Interface = reviewContainer(self)
        self.exam2Interface.setObjectName("review training")
        self.aiInterface = Ai_Widget(self.cfg,self.username)
        self.aiInterface.setObjectName("deepseek")
        self.dataInterface=dataWidget(self)
        self.dataInterface.setObjectName("data view")

        self.cfg.primaryColor.valueChanged.connect(lambda x: setThemeColor(x))

        # 连接 API 配置更改信号，实现热重载
        self.APIcard.strChanged.connect(self._on_api_changed)

        self.settingInterface = SettingCardGroup("设置", self)
        self.settingInterface.setObjectName("settingInterface")
        self.settingInterface.addSettingCard(self.cardcolor)
        self.settingInterface.addSettingCards([self.APIcard, self.deepseekcard])

        ###
        self.initNavigation()
        self.initWindow()
        self.center()

    def _on_api_changed(self, new_api):
        """API 配置更改时的处理"""
        # 保存到数据库
        from server.database_manager import DatabaseFactory
        db = DatabaseFactory.from_config_file('config.json')
        db.connect()
        db.save_user_config(username=self.username, api_key=new_api)
        db.close()

        # 重新加载 AI 界面的配置
        if hasattr(self, 'aiInterface'):
            self.aiInterface.reload_api_config()

    def initNavigation(self):
        #创建图标
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')


        self.navigationInterface.addSeparator()
        self.addSubInterface(self.exam1Interface, FluentIcon.CHECKBOX, "routine training")
        self.addSubInterface(self.exam2Interface, FluentIcon.LABEL, "review training")
        self.addSubInterface(self.dataInterface,FluentIcon.SEARCH , 'view data', NavigationItemPosition.BOTTOM)
        # 获取 client/resource 目录的 deepseek 图标路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        deepseek_icon = os.path.join(client_dir, "resource", "deepseek.png")
        self.addSubInterface(self.aiInterface, deepseek_icon, 'deepseek',NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)
    def initWindow(self):
        self.setFixedSize(1024, 768)
        self.navigationInterface.setExpandWidth(200)
        # 获取 client/resource 目录的图标路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(client_dir, "resource", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('万 词 斩')
        self.navigationInterface.expand(useAni=False)

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