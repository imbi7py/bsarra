import os
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import sqlite3

def agregarDados(variaveis, tipoFiltro, periodoFiltro = None):
    
    caminho = 'simulacoes/Milho/MG/1-1/'

    conn = sqlite3.connect('sarra.db')
    cursor = conn.cursor()



    mediasDF = DataFrame(columns = variaveis + ['latitude', 'longitude'])
    for filename in os.listdir(caminho):
        if ('9' in filename) and (not filename.endswith('BHN.csv')):
            codigo = filename[:-4]
            estacaoSeries = Series()

            cursor.execute('''
            SELECT estacao.latitude, estacao.longitude
            FROM estacao
            WHERE estacao.codigo = ?''', (codigo,))

            for linha in cursor:
                latitude = linha[0]
                longitude = linha[1]


            

            dados = pd.read_csv(caminho + filename, index_col=0)
            dados.index = pd.to_datetime(dados.index)
            dados['mes'] = dados.index.month
            dados['ano'] = dados.index.year

            for variavel in variaveis:
                agregado = dados

                if periodoFiltro is not None:
                    agregado = agregado.ix[agregado[tipoFiltro] == periodoFiltro][[variavel, 'ano']]

                if variavel == 'prec':
                    agregado = agregado.groupby(['ano']).aggregate({variavel: np.sum})
                else:
                    agregado = agregado.groupby(['ano']).aggregate({variavel: np.mean})


                estacaoSeries = estacaoSeries.append(np.mean(agregado))


            estacaoSeries['latitude'] = latitude
            estacaoSeries['longitude'] = longitude
            mediasDF = mediasDF.append(DataFrame(estacaoSeries, columns = [codigo]).T)


    mediasDF.to_csv(caminho + ''.join(variaveis) + 'medias.csv')



if __name__ == '__main__':
    # Fase
    agregarDados(['EtrEtm'], 'fase', 3)

    # Ano
    # agregarDados(['prec'], 'ano')

