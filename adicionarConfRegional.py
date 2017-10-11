import sqlite3
import sys
from PyQt5.uic import loadUiType
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QApplication, QDialogButtonBox

from adicionargrupo import AdicionarGrupo
# from interfaces.ui_adicionarConfRegional import Ui_AdicionarConfDlg

Ui_AdicionarConfDlg, QDialog = loadUiType('interfaces/adicionarConfRegional.ui')

class AdicionarConfRegional(QDialog, Ui_AdicionarConfDlg):

    # Construtor
    def __init__(self, cultura, configuracao = None, parent = None):
        super(AdicionarConfRegional, self).__init__(parent)

        self.setupUi(self)

        self.setWindowTitle('Adicionar Configuração Regional: ' + cultura['nome'])

        # Configura conexão ao banco de dados
        self.conn = sqlite3.connect('sarra.db')
        self.cursor = self.conn.cursor()

        self.estados = {'AC', 'AM', 'AP', 'PA', 'RR', 'RO', 'TO', 'MA', 'PI', 'CE', 'RN', 'PE', 'PB', 'SE', 'AL', 'BA',
                        'MG', 'SP', 'RJ', 'ES', 'MS', 'MT', 'GO', 'DF', 'RS', 'PR', 'SC'}


        self.grupos = []



        # Tipos de crescimento radicular
        self.cursor.execute('''
                SELECT * FROM tipo_vrad
                ORDER BY id''')
        for linha in self.cursor.fetchall():
            self.tipoVradComboBox.addItem(linha[1])

        # Listas de estados
        self.naoInclusosLista.addItems(self.estados)
        self.naoInclusosLista.sortItems()




        if configuracao is not None:

            self.ID = configuracao['id']
            self.novaRegiaoLineEdit.setText(configuracao['nome'])

            for row in range(self.naoInclusosLista.count() - 1, -1, -1):
                estado = self.naoInclusosLista.item(row).text()
                if estado in configuracao['estados']:
                    self.inclusosLista.addItem(estado)
                    self.naoInclusosLista.takeItem(row)

            self.inclusosLista.sortItems()

            self.soloSpinBox1.setValue(configuracao['solo'][0])
            self.soloSpinBox2.setValue(configuracao['solo'][1])
            self.soloSpinBox3.setValue(configuracao['solo'][2])

            self.tipoVradComboBox.setCurrentIndex(configuracao['tipo_vrad'] - 1)

            for grupo in configuracao['grupos']:
                self.gruposLista.addItem(grupo['nome'])

            self.grupos[:] = configuracao['grupos']
        else:
            self.ID = 0

        self.updateUi()



    @pyqtSlot()
    def on_includeToolButton_clicked(self):
        itemsSelecionados = self.naoInclusosLista.selectedItems()
        estadosAIncluir = [self.naoInclusosLista.indexFromItem(estado).data() for estado in itemsSelecionados]
        for item in itemsSelecionados:
            self.naoInclusosLista.takeItem(self.naoInclusosLista.indexFromItem(item).row())
        self.inclusosLista.addItems(estadosAIncluir)
        self.inclusosLista.sortItems()

        self.updateUi()



    @pyqtSlot()
    def on_removeToolButton_clicked(self):
        itemsSelecionados = self.inclusosLista.selectedItems()
        estadosAExcluir = [self.inclusosLista.indexFromItem(estado).data() for estado in itemsSelecionados]
        for item in itemsSelecionados:
            self.inclusosLista.takeItem(self.inclusosLista.indexFromItem(item).row())
        self.naoInclusosLista.addItems(estadosAExcluir)
        self.naoInclusosLista.sortItems()

        self.updateUi()


    @pyqtSlot('QString')
    def on_novaRegiaoLineEdit_textChanged(self, text):
        self.updateUi()

    @pyqtSlot()
    def on_adicionarGrupoButton_clicked(self):
        novoGrupo = AdicionarGrupo(parent=self)

        if novoGrupo.exec_():
            self.grupos.append(novoGrupo.getGrupo())
            self.gruposLista.addItem(self.grupos[-1]['nome'])

    @pyqtSlot()
    def on_removerGrupoButton_clicked(self):
        indice = self.gruposLista.currentRow()

        if indice >= 0:
            self.gruposLista.takeItem(indice)
            del self.grupos[indice]

        a = 1

    @pyqtSlot()
    def on_editarGrupoButton_clicked(self):
        indice = self.gruposLista.currentRow()
        editarGrupo = AdicionarGrupo(self.grupos[indice], self)

        if editarGrupo.exec_():
            self.grupos[indice].update(editarGrupo.getGrupo())
            self.gruposLista.item(indice).setText(self.grupos[indice]['nome'])


    def updateUi(self):
        inclusosLista = not (self.inclusosLista.count() == 0)

        okbutton = self.buttonBox.button(QDialogButtonBox.Ok)
        okbutton.setEnabled(inclusosLista)



    # Pega valores e retorna dicionário
    def getConfiguracao(self):
        configuracao = {}
        configuracao['id'] = self.ID
        configuracao['nome'] = self.novaRegiaoLineEdit.text()

        configuracao['estados'] = []
        for i in range(self.inclusosLista.count()):
            configuracao['estados'].append(self.inclusosLista.item(i).text())



        configuracao['grupos'] = self.grupos



        configuracao['solo'] = [self.soloSpinBox1.value(), self.soloSpinBox2.value(),
                              self.soloSpinBox3.value()]

        configuracao['tipo_vrad'] = int(self.tipoVradComboBox.currentIndex()) + 1


        return configuracao


    def accept(self):

        self.conn.commit()
        self.conn.close()

        QDialog.accept(self)

    def reject(self):
        self.conn.rollback()
        self.conn.close()
        QDialog.reject(self)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    cultura = {'nome': 'Feijão', 'id': 3}
    janela = AdicionarConfRegional(cultura)
    janela.show()
    app.exec_()