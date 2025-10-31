import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QApplication, QWidget, QDialog
from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, SettingCardGroup, qconfig, \
    ColorSettingCard, setThemeColor, FluentIcon, HyperlinkCard, OptionsSettingCard, SingleDirectionScrollArea
from qfluentwidgets import FluentIcon as FIF

from client.Home_Widget import HomeWidget
from client.Review_training import reviewContainer
from client.data_view_widget import dataWidget
from client.setAPI import StrSettingCard
from client.login import Ui_Dialog
from client.users_manager_optimized import verify_user, create_user  # 使用优化的方法
from client.userConfig import UserConfig
from client.startup_screen import Splash_Screen
from client.quiz import Ui_quiz
from client.deepseek import Ai_Widget
from client.routine_training import ExamContainer
from client.ranking_widget import RankingWidget
from client.question_widget import QuestionWidget
from server.database_manager import DatabaseFactory

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

        # 标记是否为新用户
        self.is_new_user = False
        self.new_username = None

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

        # 一次性检查用户存在性和验证密码
        user_exists, password_correct = verify_user(username, password)

        if user_exists:
            # 用户已存在，验证密码
            if password_correct:
                print(f"[DEBUG] User {username} authenticated successfully")
                self.is_new_user = False
                self.accept()
            else:
                # 密码错误
                self.ui.label_2.setText("密码错误！")
                self.ui.label_2.setVisible(True)
                self.ui.LineEdit.setText("")
        else:
            # 用户不存在，创建新用户
            if password == "":
                self.ui.label_2.setText("请输入密码")
                self.ui.label_2.setVisible(True)
                return

            if create_user(username, password):
                print(f"[DEBUG] New user {username} created")
                self.is_new_user = True
                self.new_username = username
                # 新用户需要先完成问卷调查
                self._show_questionnaire(username)
            else:
                # 创建失败
                self.ui.label_2.setText("创建用户失败，请稍后重试")
                self.ui.label_2.setVisible(True)

    def _show_questionnaire(self, username):
        """显示新用户问卷"""
        # 创建问卷对话框
        question_dialog = QDialog(self)
        question_dialog.setWindowTitle("欢迎使用万词斩")
        question_dialog.setModal(True)
        question_dialog.resize(750, 680)

        # 创建问卷组件
        question_widget = QuestionWidget(username, question_dialog)

        # 布局
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(question_dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(question_widget)
        question_dialog.setLayout(layout)

        # 连接完成信号
        question_widget.finished.connect(lambda prefs: self._on_questionnaire_finished(prefs, question_dialog))

        # 显示问卷对话框
        question_dialog.exec_()

    def _on_questionnaire_finished(self, preferences, dialog):
        """问卷完成后保存用户偏好"""
        print(f"[DEBUG] User preferences: {preferences}")

        # 保存用户偏好到数据库
        try:
            db = DatabaseFactory.from_config_file('config.json')
            db.connect()
            db.save_user_config(
                username=self.new_username,
                main_language=preferences['main_language'],
                study_language=preferences['study_language'],
                difficulty=preferences['difficulty'],
                target_score=preferences['target_score']
            )
            print(f"[DEBUG] User preferences saved to database")
        except Exception as e:
            print(f"[ERROR] Failed to save user preferences: {e}")

        # 关闭问卷对话框
        dialog.accept()
        # 接受登录对话框
        self.accept()

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

        # 主语言设置卡
        self.mainLanguageCard = OptionsSettingCard(
            self.cfg.mainLanguage,
            FluentIcon.LANGUAGE,
            "主语言",
            "选择你的母语",
            texts=["中文", "英语", "日语"],
            parent=self
        )

        # 学习语言设置卡
        self.studyLanguageCard = OptionsSettingCard(
            self.cfg.studyLanguage,
            FluentIcon.EDUCATION,
            "学习语言",
            "选择你想要学习的语言",
            texts=["英语", "中文", "日语"],
            parent=self
        )

        # 难度设置卡
        self.difficultyCard = OptionsSettingCard(
            self.cfg.difficulty,
            FluentIcon.SPEED_HIGH,
            "学习难度",
            "选择你想要的学习难度",
            texts=["简单 (Level 1)", "中等 (Level 2)", "困难 (Level 3)"],
            parent=self
        )

        # 目标积分设置卡
        self.targetScoreCard = OptionsSettingCard(
            self.cfg.targetScore,
            FluentIcon.TAG,
            "目标积分",
            "设置你的学习目标积分",
            texts=["3000 分", "10000 分", "30000 分"],
            parent=self
        )

        # 从数据库加载用户配置
        self._load_user_config_from_database()

        # 创建子界面
        self.homeInterface = HomeWidget(self)
        self.homeInterface.setObjectName("home")
        self.exam1Interface = ExamContainer(self)
        self.exam1Interface.setObjectName("routine training")
        self.exam2Interface = reviewContainer(self)
        self.exam2Interface.setObjectName("review training")
        self.rankingInterface = RankingWidget(self.username, self)
        self.rankingInterface.setObjectName("ranking")
        self.aiInterface = Ai_Widget(self.cfg,self.username)
        self.aiInterface.setObjectName("deepseek")
        self.dataInterface=dataWidget(self)
        self.dataInterface.setObjectName("data view")

        self.cfg.primaryColor.valueChanged.connect(lambda x: setThemeColor(x))

        # 连接 API 配置更改信号，实现热重载
        self.APIcard.strChanged.connect(self._on_api_changed)

        # 连接配置更改信号,保存到数据库
        self.mainLanguageCard.optionChanged.connect(self._on_main_language_changed)
        self.studyLanguageCard.optionChanged.connect(self._on_study_language_changed)
        self.difficultyCard.optionChanged.connect(self._on_difficulty_changed)
        self.targetScoreCard.optionChanged.connect(self._on_target_score_changed)

        # 创建设置卡片组
        self.settingCardGroup = SettingCardGroup("设置", self)
        self.settingCardGroup.addSettingCard(self.cardcolor)
        self.settingCardGroup.addSettingCards([self.APIcard, self.deepseekcard])
        self.settingCardGroup.addSettingCards([
            self.mainLanguageCard,
            self.studyLanguageCard,
            self.difficultyCard,
            self.targetScoreCard
        ])

        # 创建滚动区域并设置设置卡片组为其内容
        self.settingInterface = SingleDirectionScrollArea(self, orient=Qt.Vertical)
        self.settingInterface.setWidget(self.settingCardGroup)
        self.settingInterface.setWidgetResizable(True)
        self.settingInterface.setObjectName("settingInterface")

        ###
        self.initNavigation()
        self.initWindow()
        self.center()

    def _load_user_config_from_database(self):
        """从数据库加载用户配置到ConfigItem"""
        try:
            db = DatabaseFactory.from_config_file('config.json')
            db.connect()
            user_config = db.get_user_config(self.username)
            db.close()

            if user_config:
                # 映射数据库值到显示文本索引
                lang_map = {"Chinese": 0, "English": 1, "Japanese": 2}
                difficulty_map = {1: 0, 2: 1, 3: 2}
                score_map = {3000: 0, 10000: 1, 30000: 2}

                # 设置配置值（不触发信号）
                if 'main_language' in user_config:
                    main_lang = user_config['main_language']
                    self.cfg.mainLanguage.value = main_lang
                    print(f"[DEBUG] Loaded main_language: {main_lang}")

                if 'study_language' in user_config:
                    study_lang = user_config['study_language']
                    self.cfg.studyLanguage.value = study_lang
                    print(f"[DEBUG] Loaded study_language: {study_lang}")

                if 'difficulty' in user_config:
                    difficulty = user_config['difficulty']
                    self.cfg.difficulty.value = difficulty
                    print(f"[DEBUG] Loaded difficulty: {difficulty}")

                if 'target_score' in user_config:
                    target = user_config['target_score']
                    self.cfg.targetScore.value = target
                    print(f"[DEBUG] Loaded target_score: {target}")
        except Exception as e:
            print(f"[ERROR] Failed to load user config from database: {e}")
            import traceback
            traceback.print_exc()

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

    def _on_main_language_changed(self, config_item):
        """主语言更改时的处理"""
        main_language = config_item.value
        print(f"[DEBUG] Main language changed to: {main_language}")

        # 保存到数据库
        db = DatabaseFactory.from_config_file('config.json')
        db.connect()
        db.save_user_config(username=self.username, main_language=main_language)
        db.close()

        # 热重载：更新答题和复习界面的语言设置
        if hasattr(self, 'exam1Interface'):
            self.exam1Interface.reload_config()
        if hasattr(self, 'exam2Interface'):
            self.exam2Interface.reload_config()

    def _on_study_language_changed(self, config_item):
        """学习语言更改时的处理"""
        study_language = config_item.value
        print(f"[DEBUG] Study language changed to: {study_language}")

        # 保存到数据库
        db = DatabaseFactory.from_config_file('config.json')
        db.connect()
        db.save_user_config(username=self.username, study_language=study_language)
        db.close()

        # 热重载：更新答题和复习界面的语言设置
        if hasattr(self, 'exam1Interface'):
            self.exam1Interface.reload_config()
        if hasattr(self, 'exam2Interface'):
            self.exam2Interface.reload_config()

    def _on_difficulty_changed(self, config_item):
        """难度更改时的处理"""
        difficulty = config_item.value
        print(f"[DEBUG] Difficulty changed to: {difficulty}")

        # 保存到数据库
        db = DatabaseFactory.from_config_file('config.json')
        db.connect()
        db.save_user_config(username=self.username, difficulty=difficulty)
        db.close()

        # 热重载：更新答题界面的难度设置
        if hasattr(self, 'exam1Interface'):
            self.exam1Interface.reload_config()

    def _on_target_score_changed(self, config_item):
        """目标积分更改时的处理"""
        target_score = config_item.value
        print(f"[DEBUG] Target score changed to: {target_score}")

        # 保存到数据库
        db = DatabaseFactory.from_config_file('config.json')
        db.connect()
        db.save_user_config(username=self.username, target_score=target_score)
        db.close()

        # 热重载：刷新Home界面的进度条
        if hasattr(self, 'homeInterface'):
            self.homeInterface.target_score = target_score
            self.homeInterface.ui.ProgressBar.setValue(int(self.homeInterface.configitem.value/target_score*100))
            self.homeInterface.ui.StrongBodyLabel.setText(f"{int(self.homeInterface.configitem.value)}/{target_score}")
            print(f"[DEBUG] Home interface progress bar updated with new target: {target_score}")

    
    def initNavigation(self):
        #创建图标
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')

        self.navigationInterface.addSeparator()
        self.addSubInterface(self.exam1Interface, FluentIcon.CHECKBOX, "routine training")
        self.addSubInterface(self.exam2Interface, FluentIcon.LABEL, "review training")
        self.addSubInterface(self.dataInterface,FluentIcon.SEARCH , 'view data', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.rankingInterface, FluentIcon.PEOPLE, 'ranking', NavigationItemPosition.BOTTOM)
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