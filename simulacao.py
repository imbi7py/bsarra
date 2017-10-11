from PyQt5.uic import loadUiType
from PyQt5 import QtCore, QtGui, QtWidgets
import subprocess
import sys
import execSimul
import sqlite3, pickle

### Interface para disparar simulacoes ###

Ui_MainWindow, QMainWindow = loadUiType('interfaces/menuqt.ui')

tipossolo = ['1','2','3'] # Opcoes
anos = list()
conn = sqlite3.connect('sarra.db') # Carregando banco de dados
cursor = conn.cursor()


# Carregar culturas e estados
cursor.execute('''
SELECT cultura.nome, configuracaoRegional.nomeConfiguracao, configuracaoRegional.id, grupo.nome, grupo.ID
FROM cultura, configuracaoRegional, grupo
WHERE cultura.id = configuracaoRegional.culturaID
AND configuracaoRegional.id = grupo.culturaRegiao
''')

tuplas = cursor.fetchall()

cursor.execute('''
SELECT estado.sigla
FROM estado
''')
estados = cursor.fetchall()
estadotmp = list()
for estado in estados:
    estadotmp.append(estado[0])
estados = estadotmp # Lista com estados

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(MainWindow, self).__init__()
        self.setupUi(self) # Inicializar janela
        # Definir botoes e caixas
        self.btnSimular.clicked.connect(self.simular)
        self.btnAnos.clicked.connect(self.anoswindow)
        self.btnAddAno.clicked.connect(self.adicionaano)
        self.btnRmAno.clicked.connect(self.removeano)
        self.btnFechadock.clicked.connect(self.escondedock)
        self.cboxCultura.currentIndexChanged.connect(self.carregaConfReg)
        self.dwAnos.hide()
        self.cboxEstado.clear()
        self.cboxEstado.addItems(estados)
        self.cboxSolo.clear()
        self.cboxSolo.addItems(tipossolo)
        self.cboxConfReg.clear()
        self.cboxGrupo.clear()
        self.cboxConfReg.currentIndexChanged.connect(self.carregaGrupo)
        culturas = {tupla[0] for tupla in tuplas}
        self.cboxCultura.addItems(culturas)

    def simular(self):
        #print("simulando")
        # Variaveis recebem dados fornecidos pelo usuario
        estado = str(self.cboxEstado.currentText())
        inisim = str(self.dteIniSim.date().toPyDate())
        dataplantio = str(self.dtePlantio.date().toPyDate())
        tiposolo = int(self.cboxSolo.currentText())
        tipocultura = str(self.cboxCultura.currentText())
        confregional = str(self.cboxConfReg.currentText())
        estoqueini = int(self.sbEstoqueInicial.value())
        chuvalimite = int(self.sbChuvaLimite.value())
        mulch = float(self.sbMulch.value())
        rusurf = int(self.sbRUSURF.value())
        cad = int(self.sbCAD.value())
        escsup = int(self.sbEscoamentoSup.value())
        # Gera o ID correspondente com a cultura, grupo e regiao, buscando as configuracoes identicas na lista
        for tupla in tuplas:
            if tupla[0] == self.cboxCultura.currentText() and tupla[1] == self.cboxConfReg.currentText() and tupla[3] == self.cboxGrupo.currentText():
                idgrupo = tupla[4]


        execSimul.simular(estado, inisim, dataplantio, tiposolo, idgrupo, estoqueini, chuvalimite, mulch, rusurf, cad, escsup, anos)



        # QtCore.QCoreApplication.instance().quit()

    def carregaConfReg(self): # Define a lista de regioes a partir da cultura escolhida
        self.cboxConfReg.clear()
        confreglist = []
        for tupla in tuplas:
            if tupla[0] == self.cboxCultura.currentText():
                confreglist.append(tupla[1])
        confreglist = set(confreglist)
        self.cboxConfReg.addItems(confreglist)

    def carregaGrupo(self): # Define as opcoes de grupos a partir da regiao escolhida
        self.cboxGrupo.clear()
        grupolist = []
        for tupla in tuplas:
            if tupla[1] == self.cboxConfReg.currentText():
                grupolist.append(tupla[3])
        grupolist = set(grupolist)
        self.cboxGrupo.addItems(grupolist)

    def anoswindow(self):
        isVis = self.dwAnos.isVisible()
        if(isVis == True):
            self.dwAnos.hide()
        else:
            self.dwAnos.show()
            self.dwAnos.move(self.btnAnos.mapToGlobal(QtCore.QPoint(30,30)))

    def adicionaano(self):
        self.lvAnos.addItem(str(self.sbAnos.value()))
        anos.append(int(self.sbAnos.value()))

    def removeano(self):
            if(len(self.lvAnos.selectedIndexes()) > 0):
                item = self.lvAnos.currentItem()
                value = item.text()
                anos.remove(str(value))
                self.lvAnos.takeItem(self.lvAnos.currentRow())


    def escondedock(self):
        self.dwAnos.hide()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
