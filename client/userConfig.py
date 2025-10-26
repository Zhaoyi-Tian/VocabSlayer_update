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
