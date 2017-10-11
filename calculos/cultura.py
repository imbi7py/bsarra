import sqlite3, pickle

class Cultura():
    def __init__(self):
        pass

    def carregarDoBD(self, grupoID):
        conn = sqlite3.connect('sarra.db')
        cursor = conn.cursor()
        # Obtem dados da cultura, grupo, solo e regiao
        cursor.execute('''
        SELECT cultura.nome, configuracaoRegional.nomeConfiguracao, configuracaoRegional.estados,
                grupo.nome, grupo.ciclo, configuracaoRegional.solo, grupo.tipo_kc, grupo.kc, configuracaoRegional.tipo_vrad, configuracaoRegional.vrad, grupo.fases
        FROM grupo, cultura, configuracaoRegional
        WHERE grupo.ID = ? AND grupo.culturaRegiao = configuracaoRegional.id AND cultura.id = configuracaoRegional.culturaID''', (grupoID,))
        # Coloca os dados em variaveis da classe
        for linha in cursor.fetchall():
            self.culturaNome = linha[0]
            self.regiaoNome = linha[1]
            self.estados = pickle.loads(linha[2])
            self.grupoNome = linha[3]
            self.duracaoCiclo = linha[4]
            self.reservaUtilSolo = pickle.loads(linha[5])
            self.tipoKc = linha[6]
            self.tipoVrad = linha[8]
            self.fases = pickle.loads(linha[10])

            if self.tipoKc == 1:
                self.kc = pickle.loads(linha[7])





if __name__ == '__main__':
    cultura = Cultura()
    cultura.carregarDoBD(2)
    print('1')
