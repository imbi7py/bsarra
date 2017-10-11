# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crudCulturas.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_crudCulturasDialog(object):
    def setupUi(self, crudCulturasDialog):
        crudCulturasDialog.setObjectName("crudCulturasDialog")
        crudCulturasDialog.resize(650, 324)
        self.widget = QtWidgets.QWidget(crudCulturasDialog)
        self.widget.setGeometry(QtCore.QRect(40, 22, 583, 266))
        self.widget.setObjectName("widget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.treeWidget = QtWidgets.QTreeWidget(self.widget)
        self.treeWidget.setMinimumSize(QtCore.QSize(351, 0))
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.treeWidget.setObjectName("treeWidget")
        self.horizontalLayout.addWidget(self.treeWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.novaCulturaButton = QtWidgets.QPushButton(self.widget)
        self.novaCulturaButton.setObjectName("novaCulturaButton")
        self.verticalLayout.addWidget(self.novaCulturaButton)
        self.novaConfButton = QtWidgets.QPushButton(self.widget)
        self.novaConfButton.setObjectName("novaConfButton")
        self.verticalLayout.addWidget(self.novaConfButton)
        self.novoGrupoButton = QtWidgets.QPushButton(self.widget)
        self.novoGrupoButton.setObjectName("novoGrupoButton")
        self.verticalLayout.addWidget(self.novoGrupoButton)
        self.editarItemButton = QtWidgets.QPushButton(self.widget)
        self.editarItemButton.setObjectName("editarItemButton")
        self.verticalLayout.addWidget(self.editarItemButton)
        self.removerItemButton = QtWidgets.QPushButton(self.widget)
        self.removerItemButton.setObjectName("removerItemButton")
        self.verticalLayout.addWidget(self.removerItemButton)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.widget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(crudCulturasDialog)
        self.buttonBox.accepted.connect(crudCulturasDialog.accept)
        self.buttonBox.rejected.connect(crudCulturasDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(crudCulturasDialog)

    def retranslateUi(self, crudCulturasDialog):
        _translate = QtCore.QCoreApplication.translate
        crudCulturasDialog.setWindowTitle(_translate("crudCulturasDialog", "Culturas"))
        self.treeWidget.headerItem().setText(1, _translate("crudCulturasDialog", "Info"))
        self.novaCulturaButton.setText(_translate("crudCulturasDialog", "Nova Cultura"))
        self.novaConfButton.setText(_translate("crudCulturasDialog", "Nova Configuração Regional"))
        self.novoGrupoButton.setText(_translate("crudCulturasDialog", "Novo Grupo"))
        self.editarItemButton.setText(_translate("crudCulturasDialog", "Editar Item"))
        self.removerItemButton.setText(_translate("crudCulturasDialog", "Remover Item"))

