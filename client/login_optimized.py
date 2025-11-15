# -*- coding: utf-8 -*-

# 登录优化版本 - 带进度提示

import os
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from qfluentwidgets import (HyperlinkLabel, LargeTitleLabel, LineEdit,
                           PrimaryPushButton, PasswordLineEdit, ProgressRing)


class Ui_DialogOptimized(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(714, 438)
        Dialog.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        # 原有UI元素
        self.LargeTitleLabel = LargeTitleLabel(Dialog)
        self.LargeTitleLabel.setGeometry(QtCore.QRect(80, 30, 281, 54))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(36)
        font.setBold(False)
        font.setWeight(50)
        self.LargeTitleLabel.setFont(font)
        self.LargeTitleLabel.setObjectName("LargeTitleLabel")

        self.HyperlinkLabel_3 = HyperlinkLabel(Dialog)
        self.HyperlinkLabel_3.setGeometry(QtCore.QRect(480, 345, 200, 60))
        self.HyperlinkLabel_3.setObjectName("HyperlinkLabel_3")

        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(30, 90, 331, 311))
        self.label.setText("")
        client_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(client_dir, "resource", "logo.png")
        self.label.setPixmap(QtGui.QPixmap(logo_path))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        self.HyperlinkLabel = HyperlinkLabel(Dialog)
        self.HyperlinkLabel.setGeometry(QtCore.QRect(360, 170, 56, 19))
        self.HyperlinkLabel.setMouseTracking(True)
        self.HyperlinkLabel.setObjectName("HyperlinkLabel")

        self.HyperlinkLabel_2 = HyperlinkLabel(Dialog)
        self.HyperlinkLabel_2.setGeometry(QtCore.QRect(360, 220, 42, 19))
        self.HyperlinkLabel_2.setObjectName("HyperlinkLabel_2")

        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(430, 160, 241, 141))
        self.layoutWidget.setObjectName("layoutWidget")

        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")

        self.LineEdit_2 = LineEdit(self.layoutWidget)
        self.LineEdit_2.setText("")
        self.LineEdit_2.setObjectName("LineEdit_2")
        self.verticalLayout.addWidget(self.LineEdit_2)

        self.LineEdit = PasswordLineEdit(self.layoutWidget)
        self.LineEdit.setObjectName("LineEdit")
        self.verticalLayout.addWidget(self.LineEdit)

        self.PrimaryPushButton = PrimaryPushButton(self.layoutWidget)
        self.PrimaryPushButton.setObjectName("PrimaryPushButton")
        self.verticalLayout.addWidget(self.PrimaryPushButton)

        self.label_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)

        # 新增进度指示器
        self.progressRing = ProgressRing(Dialog)
        self.progressRing.setGeometry(QtCore.QRect(490, 310, 50, 50))
        self.progressRing.setVisible(False)
        self.progressRing.setObjectName("progressRing")

        self.progressLabel = QtWidgets.QLabel(Dialog)
        self.progressLabel.setGeometry(QtCore.QRect(440, 360, 150, 20))
        self.progressLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.progressLabel.setVisible(False)
        self.progressLabel.setObjectName("progressLabel")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.LineEdit_2, self.LineEdit)
        Dialog.setTabOrder(self.LineEdit, self.HyperlinkLabel_3)
        Dialog.setTabOrder(self.HyperlinkLabel_3, self.HyperlinkLabel)
        Dialog.setTabOrder(self.HyperlinkLabel, self.HyperlinkLabel_2)
        Dialog.setTabOrder(self.HyperlinkLabel_2, self.PrimaryPushButton)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "万识斩"))
        self.LargeTitleLabel.setText(_translate("Dialog", "万 词 斩"))
        self.HyperlinkLabel_3.setText(_translate("Dialog", "authors:\n"
"田照亿，桂诗清，\n张霖泽，杜浩嘉"))
        self.HyperlinkLabel.setText(_translate("Dialog", "用户名："))
        self.HyperlinkLabel_2.setText(_translate("Dialog", "密码："))
        self.LineEdit_2.setPlaceholderText(_translate("Dialog", "请输入用户名"))
        self.LineEdit.setPlaceholderText(_translate("Dialog", "请输入密码"))
        self.PrimaryPushButton.setText(_translate("Dialog", "登录"))
        self.label_2.setText(_translate("Dialog", "           密码错误，请重新输入"))
        self.progressLabel.setText(_translate("Dialog", "正在验证..."))

    def show_progress(self, text="正在验证..."):
        """显示进度指示器"""
        self.progressRing.setVisible(True)
        self.progressRing.startAnimation()
        self.progressLabel.setText(text)
        self.progressLabel.setVisible(True)
        self.PrimaryPushButton.setEnabled(False)
        self.LineEdit_2.setEnabled(False)
        self.LineEdit.setEnabled(False)
        QtWidgets.QApplication.processEvents()  # 强制刷新UI

    def hide_progress(self):
        """隐藏进度指示器"""
        self.progressRing.setVisible(False)
        self.progressRing.stopAnimation()
        self.progressLabel.setVisible(False)
        self.PrimaryPushButton.setEnabled(True)
        self.LineEdit_2.setEnabled(True)
        self.LineEdit.setEnabled(True)