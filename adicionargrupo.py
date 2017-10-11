import sqlite3
import sys
from PyQt5.uic import loadUiType
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QApplication, QDialogButtonBox, QItemDelegate, QSpinBox, QDoubleSpinBox, QTableWidgetItem, QShortcut
# from interfaces.ui_adicionargrupo import Ui_adicionarGrupoDlg

Ui_adicionarGrupoDlg, QDialog = loadUiType('interfaces/adicionarGrupo.ui')


class duracaoDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        delegateSpinBox = QSpinBox(parent)

        delegateSpinBox.setButtonSymbols(QSpinBox.NoButtons)

        return delegateSpinBox

class kcDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        delegateSpinBox = QDoubleSpinBox(parent)
        delegateSpinBox.setDecimals(2)

        delegateSpinBox.setButtonSymbols(QDoubleSpinBox.NoButtons)

        return delegateSpinBox

class AdicionarGrupo(QDialog, Ui_adicionarGrupoDlg):


    # Construtor
    def __init__(self, grupo = None, parent = None):
        super(AdicionarGrupo, self).__init__(parent)

        self.conn = sqlite3.connect('sarra.db')
        self.cursor = self.conn.cursor()
        self.grupo = {}

        self.setupUi(self)

         # Tipos de Coeficientes culturais
        self.tipoKc = {}
        self.cursor.execute('''
                        SELECT * FROM tipo_kc''')
        for linha in self.cursor.fetchall():
            self.tipoKcComboBox.addItem(linha[1])
            self.tipoKc.update({linha[1] : linha[0]})

        self.duracaoTableWidget.setItemDelegateForRow(0, duracaoDelegate())
        self.nFases = 0
        self.kcTableWidget.setItemDelegateForRow(0, kcDelegate())
        self.updateUI()

        QShortcut(QKeySequence('Ctrl+v'), self).activated.connect(self.handlePaste)

        if grupo is not None:
            self.grupo['id'] = grupo['id']
            self.grupoLineEdit.setText(grupo['nome'])

            for i in range(len(grupo['fases'])):
                item = QTableWidgetItem()
                item.setText(str(grupo['fases'][i]))
                self.duracaoTableWidget.setItem(0, i, item)


            tipoKc = [text for text in self.tipoKc.keys() if self.tipoKc[text] == grupo['tipoKc']]
            self.tipoKcComboBox.setCurrentText(tipoKc[0])

            for i in range(len(grupo['kc'])):
                item = QTableWidgetItem()
                item.setText(str(grupo['kc'][i]))
                self.kcTableWidget.setItem(0, i, item)

        else:
            self.grupo['id'] = 0

        self.conn.close()

    def handlePaste(self):
        clipboard_text = QApplication.clipboard().text().split('\t')

        widget = self.focusWidget()

        if widget == self.duracaoTableWidget:
            nColunas = self.duracaoTableWidget.columnCount()
            coluna = self.duracaoTableWidget.currentColumn()
            coluna = coluna if coluna >=0 else 0

            for numero in clipboard_text:
                if self.RepresentsInt(numero):
                    item = QTableWidgetItem()
                    item.setText(numero)
                    self.duracaoTableWidget.setItem(0, coluna, item)


                    coluna += 1

                    if coluna >= nColunas:
                        break

        else:
            if widget == self.kcTableWidget:
                nColunas = self.kcTableWidget.columnCount()
                coluna = self.kcTableWidget.currentColumn()
                coluna = coluna if coluna >= 0 else 0

                for numero in clipboard_text:
                    numero = numero.replace(',', '.')
                    if self.RepresentsFloat(numero):
                        item = QTableWidgetItem()
                        item.setText(numero)
                        self.kcTableWidget.setItem(0, coluna, item)

                        coluna += 1

                        if coluna >= nColunas:
                            break

    def RepresentsInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def RepresentsFloat(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False


    @pyqtSlot('QString')
    def on_grupoLineEdit_textChanged(self, text):


        self.updateUI()

    def on_duracaoTableWidget_cellChanged(self):
        for i in range(self.duracaoTableWidget.columnCount() - 1, -1, -1):
            if self.duracaoTableWidget.item(0, i) is not None:
                if int(self.duracaoTableWidget.item(0, i).text()) > 0:
                    break

        self.nFases = i + 1

        self.updateUI()

    def on_kcTableWidget_cellChanged(self):
        self.updateUI()

    def getGrupo(self):
        return self.grupo

    def accept(self):

        self.grupo['nome'] = self.grupoLineEdit.text()
        self.grupo['ciclo'] = self.duracaoCicloLabel.text().split()[0]
        self.grupo['fases'] = []
        for i in range(self.nFases):
            self.grupo['fases'].append(int(self.duracaoTableWidget.item(0, i).text()))
        self.grupo['tipoKc'] = self.tipoKc[self.tipoKcComboBox.currentText()]
        self.grupo['kc'] = []
        for i in range(self.kcTableWidget.columnCount()):
            self.grupo['kc'].append(float(self.kcTableWidget.item(0, i).text()))


        QDialog.accept(self)




    def updateUI(self):

        duracao = 0
        for i in range(self.nFases):
            if self.duracaoTableWidget.item(0, i) is not None:
                duracaoFase = int(self.duracaoTableWidget.item(0, i).text())
                duracao += duracaoFase

        self.duracaoCicloLabel.setText(str(duracao) + ' dias')

        self.kcTableWidget.setColumnCount(duracao//10 + 1)


        grupoLineEdit = self.grupoLineEdit.text() != ''

        tipoKc = (self.tipoKcComboBox.currentText() != '')

        duracaoTableWidget = True
        for i in range(self.nFases):
            if self.duracaoTableWidget.item(0, i) is None or \
                            self.duracaoTableWidget.item(0, i).text() == '0':
                duracaoTableWidget = False
                break

        kcTableWidget = True
        for i in range(self.kcTableWidget.columnCount()):
            if self.kcTableWidget.item(0, i) is None or \
                float(self.kcTableWidget.item(0, i).text()) == 0:
                kcTableWidget = False
                break

        okbutton = self.buttonBox.button(QDialogButtonBox.Ok)
        okbutton.setEnabled(grupoLineEdit & duracaoTableWidget & kcTableWidget & tipoKc)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = AdicionarGrupo()
    janela.show()
    app.exec_()


# def visibilidadeFase(self, mostrar):
#     self.restricoesGroupBox.setHidden(not (mostrar))
#     self.duracaoLabel.setHidden(not (mostrar))
#     self.duracaoSpinBox.setHidden(not (mostrar))
#
#  # Tipos de Coeficientes culturais
#         self.cursor.execute('''
#                         SELECT * FROM tipo_kc''')
#         for linha in self.cursor.fetchall():
#             self.tipoKcComboBox.addItem(linha[1])
#
# # Tipos de restricoes
#         self.restricoes_tipo = {}
#         self.cursor.execute('''
#                         SELECT  * FROM restricoes_tipo''')
#         for linha in self.cursor.fetchall():
#             self.restricoes_tipo.update({linha[1]: linha[0]})
#
# self.tableWidget.setItemDelegateForRow(0, kcDelegate())
#
#
# class kcDelegate(QItemDelegate):
#     def createEditor(self, parent, option, index):
#         delegateSpinBox = QDoubleSpinBox(parent)
#         delegateSpinBox.setDecimals(1)
#
#         delegateSpinBox.setButtonSymbols(QDoubleSpinBox.NoButtons)
#
#         return delegateSpinBox
#
# @pyqtSlot('int', 'int')
#     def on_tableWidget_cellChanged(self, row, column):
#         self.updateUi()
#
#
# @pyqtSlot()
# def on_adicionarFaseButton_clicked(self):
#     self.fasesLista.addItem('Fase ' + str(len(self.fases) + 1))
#     self.fases.append({'duracao': 0, 'restricoes': []})
#
#
#     @pyqtSlot()
#     def on_removerFaseButton_clicked(self):
#         currentIndex = int(self.fasesLista.currentRow())
#         if currentIndex != -1:
#
#             self.fasesLista.takeItem(currentIndex)
#             del self.fases[currentIndex]
#
#             for i in range(len(self.fases)):
#                 self.fasesLista.item(i).setText('Fase ' + str(i + 1))
#
#         self.updateUi()
#
#
#
#
#     def on_fasesLista_currentItemChanged(self):
#         faseAtual = int(self.fasesLista.currentRow())
#         if faseAtual >= 0:
#             self.duracaoSpinBox.setValue(self.fases[faseAtual]['duracao'])
#             ISNACheckbox = [restricao for restricao in self.fases[faseAtual]['restricoes'] if restricao['tipoRestricao'] == 'ISNA']
#             if ISNACheckbox:
#                 self.ISNACheckbox.setChecked(True)
#                 self.ISNAMinSpinBox.setValue(ISNACheckbox[0]['minimo'])
#                 self.ISNAMaxSpinBox.setValue(ISNACheckbox[0]['maximo'])
#             else:
#                 self.ISNACheckbox.setChecked(False)
#                 self.ISNAMinSpinBox.setValue(0)
#                 self.ISNAMaxSpinBox.setValue(0)
#
#
#         self.updateUi()
#
#
#     @pyqtSlot('int')
#     def on_duracaoSpinBox_valueChanged(self, duracaoFase):
#         faseAtual = int(self.fasesLista.currentRow())
#         self.fases[faseAtual]['duracao'] = duracaoFase
#
#         self.updateUi()
#
#     @pyqtSlot('bool')
#     def on_ISNACheckbox_toggled(self, isChecked):
#         faseAtual = int(self.fasesLista.currentRow())
#         if isChecked == True:
#             self.fases[faseAtual]['restricoes'].append({'tipoRestricao': 'ISNA',
#                                                         'minimo': self.ISNAMinSpinBox.value(),
#                                                         'maximo': self.ISNAMaxSpinBox.value()})
#         else:
#             self.fases[faseAtual]['restricoes'][:] = [restricao for restricao in self.fases[faseAtual]['restricoes']
#                                                       if restricao['tipoRestricao'] != 'ISNA']
#
#         self.updateUi()
#
#
#     @pyqtSlot('double')
#     def on_ISNAMinSpinBox_valueChanged(self, value):
#         self.ISNAMinSpinBox.edi
#         print('lala')
#         faseAtual = int(self.fasesLista.currentRow())
#         restricaoISNA = [restricao for restricao in self.fases[faseAtual]['restricoes']
#                          if restricao['tipoRestricao'] == 'ISNA'][0]
#         restricaoISNA['minimo'] = self.ISNAMinSpinBox.value()
#
#     @pyqtSlot('double')
#     def on_ISNAMaxSpinBox_valueChanged(self, value):
#         print('lala')
#         faseAtual = int(self.fasesLista.currentRow())
#         restricaoISNA = [restricao for restricao in self.fases[faseAtual]['restricoes']
#                          if restricao['tipoRestricao'] == 'ISNA'][0]
#         restricaoISNA['maximo'] = self.ISNAMaxSpinBox.value()
#
#
#     def checkTableIsEmpty(self):
#         vazio = False
#
#         iColumns = self.tableWidget.columnCount()
#         for column in range(iColumns):
#             if self.tableWidget.item(0, column) is None:
#                 vazio = True
#                 break
#
#         return vazio
#
# grupo['ciclo'] = self.duracaoCicloLabel.text().split(' ')[0]
#
# grupo['tipo_kc'] = int(self.tipoKcComboBox.currentIndex()) + 1
#
#         #
#         iColumns = self.tableWidget.columnCount()
#         grupo['kcLista'] = []
#
#         for column in range(iColumns):
#             grupo['kcLista'].append(float(self.tableWidget.item(0, column).text()))
#
#         grupo['kc'] = pickle.dumps(grupo['kcLista'], pickle.HIGHEST_PROTOCOL)
# grupo['fases'] = self.fases
#
# configuracao['nome'] = str(self.grupoLineEdit.text())
#
#
# @pyqtSlot("QString")
# def on_grupoLineEdit_textChanged(self, text):
#     self.updateUi()
#
# duracaoCiclo = sum([fase['duracao'] for fase in self.fases])
#         self.duracaoCicloLabel.setText(str(duracaoCiclo) + ' dias')
#         self.tableWidget.setColumnCount(duracaoCiclo//10 + 1)
#
#         grupoLineEdit = not (self.grupoLineEdit.text() == '')
#
# tableWidget = not self.checkTableIsEmpty()
# fasesLista = self.fasesLista.currentRow() != -1
#         ISNACheckbox = self.ISNACheckbox.isChecked()
#
# self.adicionarFaseButton.setEnabled(culturaComboBox & regiaoComboBox)
# self.removerFaseButton.setEnabled(culturaComboBox & regiaoComboBox)
# self.ISNAMinSpinBox.setEnabled(ISNACheckbox)
# self.ISNAMaxSpinBox.setEnabled(ISNACheckbox)
#
# self.visibilidadeFase(fasesLista)
#
# self.cursor.execute('''
#         INSERT OR IGNORE INTO grupo (nome, configuracaoRegional, ciclo, tipo_vrad, tipo_kc, kc, solo)
#         VALUES (?, ?, ?, ?, ?, ?, ?)''', (grupo['nome'], grupo['configuracao'], grupo['ciclo'],
#                             grupo['tipo_vrad'], grupo['tipo_kc'], sqlite3.Binary(grupo['kc']), sqlite3.Binary(grupo['solo'])))
#         grupo['id'] = self.cursor.lastrowid
#
# i = 1
# for fase in self.fases:
#     self.cursor.execute('''
#     INSERT OR IGNORE INTO fases (grupoID, nFase, duracao)
#     VALUES (?, ?, ?)''', (grupo['id'], i, fase['duracao']))
#     faseID = self.cursor.lastrowid
#
#     for restricao in fase['restricoes']:
#         self.cursor.execute('''
#         INSERT OR IGNORE INTO restricoes (tipo, faseID, valor_minimo, valor_maximo)
#         VALUES (?, ?, ?, ?)''', (
#         self.restricoes_tipo[restricao['tipoRestricao']], faseID, restricao['minimo'], restricao['maximo']))
