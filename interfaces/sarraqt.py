# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sarraqt.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setDockNestingEnabled(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.mplvl = QtWidgets.QHBoxLayout()
        self.mplvl.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.mplvl.setContentsMargins(-1, 0, -1, -1)
        self.mplvl.setSpacing(0)
        self.mplvl.setObjectName("mplvl")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.mplvl.addWidget(self.widget)
        self.verticalLayout_2.addLayout(self.mplvl)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.dockWidget_3 = QtWidgets.QDockWidget(MainWindow)
        self.dockWidget_3.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        self.dockWidget_3.setObjectName("dockWidget_3")
        self.dockWidgetContents_3 = QtWidgets.QWidget()
        self.dockWidgetContents_3.setObjectName("dockWidgetContents_3")
        self.formLayoutWidget = QtWidgets.QWidget(self.dockWidgetContents_3)
        self.formLayoutWidget.setGeometry(QtCore.QRect(0, 40, 93, 161))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setObjectName("formLayout")
        self.lblCultura = QtWidgets.QLabel(self.formLayoutWidget)
        self.lblCultura.setObjectName("lblCultura")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lblCultura)
        self.cboxCultura = QtWidgets.QComboBox(self.formLayoutWidget)
        self.cboxCultura.setObjectName("cboxCultura")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.cboxCultura)
        self.lblEstado = QtWidgets.QLabel(self.formLayoutWidget)
        self.lblEstado.setObjectName("lblEstado")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self.lblEstado)
        self.cboxEstado = QtWidgets.QComboBox(self.formLayoutWidget)
        self.cboxEstado.setObjectName("cboxEstado")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.cboxEstado)
        self.dockWidget_3.setWidget(self.dockWidgetContents_3)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget_3)
        self.dockWidget_3.raise_()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.lblCultura.setText(_translate("MainWindow", "Cultura:"))
        self.lblEstado.setText(_translate("MainWindow", "Estado:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
