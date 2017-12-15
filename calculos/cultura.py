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
                grupo.nome, grupo.ciclo, configuracaoRegional.solo, grupo.tipo_kc, grupo.kc, configuracaoRegional.tipo_vrad, configuracaoRegional.vrad, grupo.fases,
                configuracaoRegional.restricoesISNA, configuracaoRegional.restricoesTEMP, configuracaoRegional.TMM, configuracaoRegional.TMA, configuracaoRegional.riscoGeada
        FROM grupo, cultura, configuracaoRegional
        WHERE grupo.ID = ? AND grupo.culturaRegiao = configuracaoRegional.id AND cultura.id = configuracaoRegional.culturaID''', (grupoID,))
        # Coloca os dados em variaveis da classe
        for linha in cursor.fetchall():
            self.culturaNome = linha[0]
            self.regiaoNome = linha[1]
            self.estados = pickle.loads(linha[2])
            self.grupoNome = linha[3]
            self.duracaoCiclo = linha[4]
            self.reservaUtilSolo = list(map(int, linha[5].split(",")))
            self.tipoKc = linha[6]
            self.tipoVrad = linha[8]
            self.fases = pickle.loads(linha[10]) # esta em binario comprimido
            self.restricoesISNA = linha[11].split(",")
            self.restricoesTEMP = linha[12].split(",")
            self.restricoesTMM = linha[13].split(",")
            if linha[14]: self.restricoesTMA = linha[14].split(",")
            self.riscoGeada = linha[15]
            #ADICIONAR RESTRICAO DE ISNA FASE 3 DO BANCO DE DADOS


            if self.tipoKc == 1:
                self.kc = pickle.loads(linha[7])





if __name__ == '__main__':
    cultura = Cultura()
    cultura.carregarDoBD(2)
    print('1')
