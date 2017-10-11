import pickle
import sqlite3
import sys
from PyQt5.Qt import Qt
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QApplication, QTreeWidgetItem, QTreeWidget, QDialogButtonBox
from PyQt5.uic import loadUiType
from adicionarConfRegional import AdicionarConfRegional
from adicionargrupo import AdicionarGrupo
# from interfaces.ui_crudCulturas import Ui_crudCulturasDialog


Ui_crudCulturasDialog, QDialog = loadUiType('interfaces/crudCulturas.ui')


class CrudCultura(QDialog, Ui_crudCulturasDialog):

    def __init__(self, parent = None):
        super(CrudCultura, self).__init__(parent)

        self.setupUi(self)

        self.conn = sqlite3.connect('sarra.db')
        self.cursor = self.conn.cursor()
        self.loadCulturas()

        self.treeWidget.setEditTriggers(QTreeWidget.NoEditTriggers)

        self.treeWidget.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.aplicar)
        self.updateUI()



    def loadCulturas(self):

        # Carregar culturas
        self.culturas = []
        self.cursor.execute('''
        SELECT * FROM cultura''')

        for linha in self.cursor.fetchall():
            self.culturas.append({'nome': linha[0], 'id': linha[1]})


        # Carregar informacoes regionais
        for cultura in self.culturas:

            cultura['configuracoes'] = []
            self.cursor.execute('''
            SELECT * FROM configuracaoRegional
            WHERE culturaID = ?''', (cultura['id'],))

            for linha in self.cursor.fetchall():
                cultura['configuracoes'].append({'id': linha[0],
                                                 'nome': linha[2],
                                                 'estados': pickle.loads(linha[3]),
                                                 'tipo_vrad': linha[4],
                                                 'solo': pickle.loads(linha[6])
                                                 # 'vrad': linha,
                                                 })

        # Carregar grupos
        for cultura in self.culturas:
            for configuracao in cultura['configuracoes']:
                configuracao['grupos'] = []

                self.cursor.execute('''
                SELECT * FROM grupo
                WHERE culturaRegiao = ?''', (configuracao['id'],))

                for linha in self.cursor.fetchall():
                    configuracao['grupos'].append({'id': linha[0],
                                                   'nome': linha[1],
                                                   'ciclo': linha[3],
                                                   'tipoKc': linha[4],
                                                   'kc': pickle.loads(linha[5]),
                                                   'fases': pickle.loads(linha[6])})


        # Exibir informacoes
        for cultura in self.culturas:
            itemCultura = QTreeWidgetItem()
            itemCultura.setText(0, cultura['nome'])
            itemCultura.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)
            self.treeWidget.addTopLevelItem(itemCultura)
            cultura['item'] = itemCultura

            for configuracao in cultura['configuracoes']:
                itemConf = QTreeWidgetItem()
                itemConf.setText(0, configuracao['nome'])
                itemConf.setText(1, ', '.join(configuracao['estados']))
                itemConf.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                itemCultura.addChild(itemConf)
                configuracao['item'] = itemConf

                for grupo in configuracao['grupos']:
                    itemGrupo = QTreeWidgetItem()
                    itemGrupo.setText(0, grupo['nome'])
                    itemGrupo.setText(1, str(grupo['ciclo']) + ' dias')
                    itemGrupo.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                    itemConf.addChild(itemGrupo)
                    grupo['item'] = itemGrupo



        self.treeWidget.resizeColumnToContents(0)



    @pyqtSlot('QModelIndex')
    def on_treeWidget_expanded(self, indice):
        self.treeWidget.resizeColumnToContents(0)

    @pyqtSlot('QModelIndex')
    def on_treeWidget_collapsed(self, indice):
        self.treeWidget.resizeColumnToContents(0)


    def on_treeWidget_itemDoubleClicked(self, item, column):
        self.on_editarItemButton_clicked()

    def on_selectionChanged(self):
        self.updateUI()


    def on_treeWidget_itemChanged(self, item):
        itemsAbove = [item]
        texto = item.text(0)
        while itemsAbove[-1] is not None:
            itemsAbove.append(itemsAbove[-1].parent())

        level = len(itemsAbove)
        culturaAEditar = [cultura for cultura in self.culturas \
                          if cultura['item'] == itemsAbove[-2]]
        if level == 2:
            culturaAEditar[0]['nome'] = texto

            self.cursor.execute('''
            UPDATE cultura
            SET nome = ?
            WHERE id = ?''', (culturaAEditar[0]['nome'], culturaAEditar[0]['id']))

        self.treeWidget.resizeColumnToContents(0)



    @pyqtSlot()
    def on_novaCulturaButton_clicked(self):
        novaCultura = QTreeWidgetItem()
        novaCultura.setText(0, 'Nova Cultura')
        novaCultura.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)

        self.cursor.execute('''
        INSERT OR IGNORE INTO cultura (nome)
        VALUES (?)''', ('Nova Cultura',))

        self.culturas.append({'item': novaCultura,
                              'nome': 'Nova Cultura',
                              'id': self.cursor.lastrowid,
                              'configuracoes': []})

        self.treeWidget.addTopLevelItem(novaCultura)
        self.treeWidget.editItem(novaCultura)

    @pyqtSlot()
    def on_novaConfButton_clicked(self):
        items = [self.treeWidget.currentItem()]

        while items[-1] is not None:
            items.append(items[-1].parent())

        cultura = [cult for cult in self.culturas \
                   if cult['item'] == items[-2]][0]

        novaConfWindow = AdicionarConfRegional(cultura)
        if novaConfWindow.exec_():
            novaConfiguracao = self.insertConfiguracao(novaConfWindow.getConfiguracao(), cultura)
            cultura['configuracoes'].append(novaConfiguracao)
            cultura['item'].addChild(novaConfiguracao['item'])

            for grupo in novaConfiguracao['grupos']:
                grupo = self.insertGrupo(grupo, novaConfiguracao)
                novaConfiguracao['item'].addChild(grupo['item'])



    @pyqtSlot()
    def on_novoGrupoButton_clicked(self):
        items = [self.treeWidget.currentItem()]

        while items[-1] is not None:
            items.append(items[-1].parent())

        cultura = [cult for cult in self.culturas \
                   if cult['item'] == items[-2]][0]

        configuracao = [conf for conf in cultura['configuracoes'] \
                        if conf['item'] == items[-3]][0]

        novoGrupoWindow = AdicionarGrupo()
        if novoGrupoWindow.exec_():
            novoGrupo = self.insertGrupo(novoGrupoWindow.getGrupo(), configuracao)
            configuracao['item'].addChild(novoGrupo['item'])



    @pyqtSlot()
    def on_editarItemButton_clicked(self):
        items = [self.treeWidget.currentItem()]

        while items[-1] is not None:
            items.append(items[-1].parent())

        cultura = [cult for cult in self.culturas \
                   if cult['item'] == items[-2]][0]

        level = len(items) - 1

        if level == 1:
            self.treeWidget.editItem(items[0])

        else:
            configuracao = [conf for conf in cultura['configuracoes'] \
                            if conf['item'] == items[-3]][0]
            if level == 2:

                editarConfiguracao = AdicionarConfRegional(cultura, configuracao)

                if editarConfiguracao.exec_():
                    novaConfiguracao = editarConfiguracao.getConfiguracao()

                    self.cursor.execute('''
                    UPDATE configuracaoRegional
                    SET nomeConfiguracao = ?, estados = ?, tipo_vrad = ?, solo = ?
                    WHERE ID = ?''', (novaConfiguracao['nome'], sqlite3.Binary(pickle.dumps(novaConfiguracao['estados'], pickle.HIGHEST_PROTOCOL)),
                                      novaConfiguracao['tipo_vrad'], sqlite3.Binary(pickle.dumps(novaConfiguracao['solo'], pickle.HIGHEST_PROTOCOL)),
                                      novaConfiguracao['id']))

                    configuracao['item'].setText(0, novaConfiguracao['nome'])
                    configuracao['item'].setText(1, ', '.join(novaConfiguracao['estados']))

                    gruposAIncluir = [grupo for grupo in novaConfiguracao['grupos'] \
                                      if grupo['id'] == 0]

                    for grupo in gruposAIncluir:
                        grupo = self.insertGrupo(grupo, configuracao)
                        configuracao['item'].addChild(grupo['item'])

                    gruposAAlterar = [grupo for grupo in novaConfiguracao['grupos'] \
                                      if grupo not in gruposAIncluir]

                    for grupo in gruposAAlterar:
                        self.cursor.execute('''
                        UPDATE grupo
                        SET nome = ?, ciclo = ?, tipo_kc = ?, kc = ?, fases = ?
                        WHERE ID = ?''', (grupo['nome'], grupo['ciclo'], grupo['tipoKc'],
                                          sqlite3.Binary(pickle.dumps(grupo['kc'], pickle.HIGHEST_PROTOCOL)),
                                          sqlite3.Binary(pickle.dumps(grupo['fases'], pickle.HIGHEST_PROTOCOL)),
                                          grupo['id']))

                        grupo['item'].setText(0, grupo['nome'])
                        grupo['item'].setText(1, str(grupo['ciclo']) + ' dias')

                    novosGruposIDs = [grupo['id'] for grupo in novaConfiguracao['grupos']]
                    gruposAExcluir = [grupo for grupo in configuracao['grupos'] \
                                      if grupo['id'] not in novosGruposIDs]

                    for grupo in gruposAExcluir:
                        self.cursor.execute('''
                        DELETE FROM grupo
                        WHERE ID = ?''', (grupo['id'],))

                        configuracao['item'].removeChild(grupo['item'])

                    configuracao.update(novaConfiguracao)

            else:
                grupo = [gru for gru in configuracao['grupos'] \
                         if gru['item'] == items[-4]][0]

                editarGrupoWindow = AdicionarGrupo(grupo)

                if editarGrupoWindow.exec_():
                    novoGrupo = editarGrupoWindow.getGrupo()

                    self.cursor.execute('''
                    UPDATE grupo
                    SET nome = ?, ciclo = ?, tipo_kc = ?, kc = ?, fases = ?
                    WHERE ID = ?''', (novoGrupo['nome'], novoGrupo['ciclo'], novoGrupo['tipoKc'],
                                      sqlite3.Binary(pickle.dumps(novoGrupo['kc'], pickle.HIGHEST_PROTOCOL)),
                                      sqlite3.Binary(pickle.dumps(novoGrupo['fases'], pickle.HIGHEST_PROTOCOL)),
                                      novoGrupo['id']))

                    grupo['item'].setText(0, novoGrupo['nome'])
                    grupo['item'].setText(1, str(novoGrupo['ciclo']) + ' dias')
                    grupo.update(novoGrupo)

    @pyqtSlot()
    def on_removerItemButton_clicked(self):
        items = [self.treeWidget.currentItem()]

        while items[-1] is not None:
            items.append(items[-1].parent())

        cultura = [cult for cult in self.culturas \
                   if cult['item'] == items[-2]][0]

        level = len(items) - 1

        if level == 1:
            for configuracao in cultura['configuracoes']:
                for grupo in configuracao['grupos']:

                    self.cursor.execute('''
                    DELETE FROM grupo
                    WHERE id = ?''', (grupo['id'],))

                self.cursor.execute('''
                DELETE FROM configuracaoRegional
                WHERE id = ?''', (configuracao['id'],))

            self.cursor.execute('''
            DELETE FROM cultura
            WHERE id = ?''', (cultura['id'],))


            self.treeWidget.takeTopLevelItem(self.treeWidget.indexOfTopLevelItem(items[0]))
            self.culturas.remove(cultura)

        else:
            configuracao = [conf for conf in cultura['configuracoes'] \
                            if conf['item'] == items[-3]][0]

            if level == 2:
                for grupo in configuracao['grupos']:
                    self.cursor.execute('''
                    DELETE FROM grupo
                    WHERE id = ?''', (grupo['id'],))

                self.cursor.execute('''
                DELETE FROM configuracaoRegional
                WHERE id = ?''', (configuracao['id'],))

                cultura['item'].removeChild(configuracao['item'])
                cultura['configuracoes'].remove(configuracao)

            else:
                grupo = [gru for gru in configuracao['grupos'] \
                         if gru['item'] == items[-4]][0]

                self.cursor.execute('''
                DELETE FROM grupo
                WHERE id = ?''', (grupo['id'],))

                configuracao['item'].removeChild(grupo['item'])
                configuracao['grupos'].remove(grupo)




    def insertGrupo(self, grupo, configuracao):
        novoGrupoItem = QTreeWidgetItem()
        novoGrupoItem.setText(0, grupo['nome'])
        novoGrupoItem.setText(1, str(grupo['ciclo']) + ' dias')
        novoGrupoItem.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.cursor.execute('''
        INSERT OR IGNORE INTO grupo (nome, culturaRegiao, ciclo, tipo_kc, kc, fases)
        VALUES (?, ?, ?, ?, ?, ?)''', (grupo['nome'], configuracao['id'],
                                    grupo['ciclo'], grupo['tipoKc'],
                                    sqlite3.Binary(pickle.dumps(grupo['kc'], pickle.HIGHEST_PROTOCOL)),
                                    sqlite3.Binary(pickle.dumps(grupo['fases'], pickle.HIGHEST_PROTOCOL))))

        grupo.update({'id': self.cursor.lastrowid,
                      'item': novoGrupoItem})

        return grupo

    def insertConfiguracao(self, configuracao, cultura):
        novaConfItem = QTreeWidgetItem()
        novaConfItem.setText(0, configuracao['nome'])
        novaConfItem.setText(1, ', '.join(configuracao['estados']))
        novaConfItem.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.cursor.execute('''
        INSERT OR IGNORE INTO configuracaoRegional (culturaID, nomeConfiguracao, estados, tipo_vrad, solo)
        VALUES (?, ?, ?, ?, ?)''', (cultura['id'], configuracao['nome'], sqlite3.Binary(pickle.dumps(configuracao['estados'], pickle.HIGHEST_PROTOCOL)),
                                    configuracao['tipo_vrad'], sqlite3.Binary(pickle.dumps(configuracao['solo']))))

        configuracao.update({'id': self.cursor.lastrowid,
                                 'item': novaConfItem})

        return configuracao

    def updateUI(self):
        item = self.treeWidget.selectedItems()

        if item:
            while item[-1] is not None:
                item.append(item[-1].parent())

            level = len(item) - 1


            self.novoGrupoButton.setEnabled(level > 1)
            self.novaConfButton.setEnabled(True)
            self.editarItemButton.setEnabled(True)
            self.removerItemButton.setEnabled(True)
        else:
            self.novaConfButton.setEnabled(False)
            self.novoGrupoButton.setEnabled(False)
            self.editarItemButton.setEnabled(False)
            self.removerItemButton.setEnabled(False)

    def aplicar(self):
        self.conn.commit()

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
    janela = CrudCultura()
    janela.show()
    app.exec_()