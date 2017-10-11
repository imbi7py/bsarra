import os.path
import sqlite3

from pandas import DataFrame

from calculos.balancoHidrico import balancoHidrico
from calculos.cultura import Cultura
from calculos.estacao import Estacao
from calculos.estrutura import ParamSimul

#### Parâmetros a serem definidos pelo usuário
estado = 'SP'
dados = 'agritempo'

# Datas
inicioSimul = (1,1)
inicioPlantio = (1, 1)


variaveis = ['EtrEtm']
mediasDF = DataFrame(columns=['latitude', 'longitude'] + variaveis)
parametros = ParamSimul()
parametros.chuvaLimite = 30
parametros.escoamentoSuperficial = 20

# Selecionar cultura
cultura = Cultura()
cultura.carregarDoBD(25)

enderecoSaida = 'simulacoes/' + cultura.culturaNome + '/' + estado + '/' + dados + '/' + str(inicioPlantio[1]) + '-' + str(inicioPlantio[0]) + '/'

if not os.path.exists(enderecoSaida):
    os.makedirs(enderecoSaida)


#### Selecionar todos as estações de um estado
conn = sqlite3.connect('sarra.db')
cursor = conn.cursor()

cursor.execute('''
SELECT estacao.codigo, estacao.nome, estacao.latitude, estacao.longitude,
estacao.altitude, estacao.municipio, municipio.nome, municipio.estado, estado.nome, estacao.dados
FROM estacao, municipio, estado
WHERE municipio.codigo = estacao.municipio AND municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))

estacoes = []

for linha in cursor.fetchall():
    estacoes.append(Estacao(cursorSQL=linha))

########

valoresDiarios = {}
balancoHidricoNormal = {}




# estacoes = estacoes[-4:]

nEstacoes = len(estacoes)
n = 1

for estacao in estacoes:
    print(estacao.nome + ': ' + str(n) + ' de ' + str(nEstacoes))
    # if os.path.isfile(endereco + str(estacao.codigo) + '.csv'):
    #     valoresDiarios[estacao.codigo] = pd.read_csv(endereco + str(estacao.codigo) + '.csv')
    # else:
    simulacao = balancoHidrico(cultura)
    simulacao.lerDadosMeteorologicos(estacao, parametros)
    (valoresDiarios[estacao.codigo], balancoHidricoNormal[estacao.codigo]) = simulacao.simularBalancoHidrico(inicioSimul, inicioPlantio)
    valoresDiarios['latitude'] = estacao.latitude
    valoresDiarios['longitude'] = estacao.longitude
    medias = {}
    medias['latitude'] = estacao.latitude
    medias['longitude'] = estacao.longitude

    if not isinstance(valoresDiarios[estacao.codigo], str):
        valoresDiarios[estacao.codigo].to_csv(enderecoSaida + str(estacao.codigo) + '.csv')
        balancoHidricoNormal[estacao.codigo].to_csv(enderecoSaida + str(estacao.codigo) + 'BHN.csv')
        # medias['media'] = valoresDiarios[estacao.codigo].calcularMedia(variaveis, cultura, parametros, inicioPlantio, estacao, 'fase', 3)
    # else:
    #     medias['media'] = DataFrame(columns=variaveis)

    # pd.concat([mediasDF, DataFrame(medias['media'], index=[estacao.codigo])], axis = 1)
    # a = pd.concat([DataFrame(medias, columns=['latitude', 'longitude'], index), medias['media']], axis=1)
    # mediasDF = mediasDF.append(pd.concat([DataFrame(medias, columns=['latitude', 'longitude'], index=[estacao.codigo]), medias['media']], axis=1))
    n+=1
# mediasDF.to_csv(enderecoSaida + 'Medias.csv')



