from PyQt5.QtGui import QColor
from qfluentwidgets import QConfig, OptionsConfigItem, OptionsValidator, qconfig, ColorSettingCard, FluentIcon, \
    ColorSerializer, ConfigItem, Theme, EnumSerializer


class UserConfig(QConfig):
    User = ConfigItem(
        "User", "name", "让三颗心免于哀伤",
        restart=False
    )

    primaryColor = OptionsConfigItem(
        "MainWindow", "primaryColor", QColor("#4080FF"),
        serializer=ColorSerializer(),
        restart=False
    )

    API=ConfigItem(
        "User", "API", "",  # 默认为空，需要用户自行配置
        restart=False  # 改为 False，支持热重载
    )

    total_num=ConfigItem(
        "User","total_num",default=0,restart=False
    )

    # 主语言配置
    mainLanguage = OptionsConfigItem(
        "User", "mainLanguage", "Chinese",
        OptionsValidator(["Chinese", "English", "Japanese"]),
        restart=False
    )

    # 学习语言配置
    studyLanguage = OptionsConfigItem(
        "User", "studyLanguage", "English",
        OptionsValidator(["English", "Chinese", "Japanese"]),
        restart=False
    )

    # 难度配置
    difficulty = OptionsConfigItem(
        "User", "difficulty", 1,
        OptionsValidator([1, 2, 3]),
        restart=False
    )

    # 目标积分配置
    targetScore = OptionsConfigItem(
        "User", "targetScore", 10000,
        OptionsValidator([3000, 10000, 30000]),
        restart=False
    )
