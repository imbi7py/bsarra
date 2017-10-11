# -*- coding: utf-8 -*-
import os.path
import sqlite3
import pandas as pd
from pandas import DataFrame
from calculos.balancoHidrico import balancoHidrico
from calculos.cultura import Cultura
from calculos.estacao import Estacao
from calculos.estrutura import ParamSimul


### Funcao que dispara a simulacao do balanco hidrico ###
def simular(estado,inisim,dataplantio,tiposolo,idgrupo,estoqueini,chuvalimite,mulch,rusurf,cad,escsup,anos, dados = 'agritempo'):
    #### Parâmetros a serem definidos pelo usuário

    inisimdia = int(inisim[8:10]) # Data de inicio da simulacao
    inisimmes = int(inisim[5:7])
    dataplantiodia = int(dataplantio[8:10]) # Data de inicio do plantio
    dataplantiomes = int(dataplantio[5:7])

    # anos.append(max(anos) + 1)
    # Datas
    inicioSimul = (inisimmes,inisimdia)
    inicioPlantio = (dataplantiomes, dataplantiodia)

    variaveis = ['EtrEtm'] # devem ser alteradas por tipo de plantacao?
    mediasDF = DataFrame(columns=['latitude', 'longitude'] + variaveis)
    parametros = ParamSimul() # Inicializando os parametros
    # Utilizar dados fornecidos pelo usuario
    parametros.chuvaLimite = chuvalimite
    parametros.ESTOQUEINICIAL = estoqueini
    parametros.escoamentoSuperficial = escsup # Porcentagem
    parametros.mulch = mulch
    parametros.RUSURF = rusurf # Reserva Útil superficial
    parametros.CAD = cad
    parametros.tipoSolo = tiposolo
    parametros.anosDadosHistoricos = list(map(int, anos))

    # Selecionar cultura
    cultura = Cultura()
    cultura.carregarDoBD(idgrupo)

    enderecoSaida = 'simulacoes/' + cultura.culturaNome + '/' + estado + '/' + dados + '/' + str(inicioPlantio[1]) + '-' + str(inicioPlantio[0]) + '/'
    #print(estado)
    #print(inicioSimul)
    #print(inicioPlantio)
    #print(variaveis)
    #print(parametros.chuvaLimite)
    #print(parametros.escoamentoSuperficial)
    #print(parametros.ESTOQUEINICIAL)
    #print(parametros.mulch)
    #print(parametros.RUSURF)
    #print(parametros.CAD)
    #print(parametros.tipoSolo)
    #print(parametros.anosDadosHistoricos)
    #print(cultura.culturaNome)

    if not os.path.exists(enderecoSaida):
        os.makedirs(enderecoSaida)


    #### Selecionar todos as estações de um estado
    conn = sqlite3.connect('sarra.db')
    cursor = conn.cursor()

    dados = dados.lower()

    if dados == 'agritempo': # Obter dados da estacao e dos municipios
        cursor.execute('''
        SELECT estacao.codigo, estacao.nome, estacao.latitude, estacao.longitude,
        estacao.altitude, estacao.municipio, municipio.nome, municipio.estado, estado.nome, estacao.dados
        FROM estacao, municipio, estado
        WHERE municipio.codigo = estacao.municipio AND municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))

    elif dados == 'hadgem' or dados == 'miroc': 
        cursor.execute('''
                SELECT municipio.codigo, municipio.nome, municipio.latitude, municipio.longitude,
                municipio.estado, estado.nome
                FROM municipio, estado
                WHERE municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))
    else: # Encontrar erros
        print('erro')



    estacoes = []

    for linha in cursor.fetchall():
        estacoes.append(Estacao(cursorSQL=linha, dados = dados))

    ########

    # Inicializar
    valoresDiarios = {}
    balancoHidricoNormal = {}

    ### Carregar dados de modelo ###
    # if dados == 'hadgem' or dados == 'miroc':
    #     arqPrec = 'ETA/' + dados + '/' + dados + '_prec_1961-1990.txt'
    #     arqtMax = 'ETA/' + dados + '/' + dados + '_tmax_1961-1990.txt'
    #     arqtMin = 'ETA/' + dados + '/' + dados + '_tmin_1961-1990.txt'
    #
    #     print('Carregar dados de Modelo - Precipitacao')
    #     precDF = pd.read_csv(arqPrec, delimiter='\\s+', header=None, names=['data', 'lat', 'long', 'prec'])
    #     precDF['data'] = pd.to_datetime(precDF['data'])
    #     print('Carregar dados de Modelo - Tmax')
    #     tMaxDF = pd.read_csv(arqtMax, delimiter='\\s+', header=None, names=['dataMax', 'lat', 'long', 'tmax'])
    #     print('Carregar dados de Modelo - Tmin')
    #     tMinDF = pd.read_csv(arqtMin, delimiter='\\s+', header=None, names=['dataMin', 'lat', 'long', 'tmin'])
    #
    #     dadosMetDF = pd.DataFrame(columns=['tmed', 'prec'])
    #
    #     print('Extraindo dados ...')
    #     for estacao in estacoes:
    #         print(estacao.nome)
    #         lat = precDF.loc[(precDF['lat'] - estacao.latitude).idxmin(), 'lat']
    #         long = precDF.loc[(precDF['lat'] - estacao.longitude).idxmin(), 'long']
    #
    #         indexes = (precDF['lat'] == lat) & (precDF['long'] == long) & ((precDF['data'].dt.year.isin(anos)) | ((precDF['data'].dt.year.isin(pd.Series(anos) + 1)) & (precDF['data'].dt.month == 1)))
    #         auxDF = pd.merge(precDF[indexes], tMaxDF[indexes], left_index=True, right_index=True, how='outer')[['data', 'prec', 'tmax']]
    #         auxDF = pd.merge(auxDF, tMinDF[indexes], left_index=True, right_index=True, how='outer')[['data', 'prec', 'tmin', 'tmax']]
    #
    #         auxDF['codigoMunicipio'] = estacao.codigo
    #
    #         dadosMetDF = dadosMetDF.append(auxDF)
    #
    #
    #     dadosMetDF['tmed'] = (dadosMetDF['tmax'] + dadosMetDF['tmin'])/2
    #
    #     print('Salvando dados...')
    #     dadosMetDF.to_csv('dadosMetTemp.csv')
    #
    #     del dadosMetDF, precDF, tMaxDF, tMinDF, auxDF, indexes


    nEstacoes = len(estacoes)
    n = 1

    for estacao in estacoes:
        print(estacao.nome + ': ' + str(n) + ' de ' + str(nEstacoes))
        # if os.path.isfile(endereco + str(estacao.codigo) + '.csv'):
        #     valoresDiarios[estacao.codigo] = pd.read_csv(endereco + str(estacao.codigo) + '.csv')
        # else:
        simulacao = balancoHidrico(cultura)
        simulacao.lerDadosMeteorologicos(estacao, parametros, dados)
        resultado = simulacao.simularBalancoHidrico(inicioSimul, inicioPlantio)


        if not isinstance(resultado, str):
            valoresDiarios[estacao.codigo] = resultado[0]
            balancoHidricoNormal[estacao.codigo] = resultado[1]

            valoresDiarios['latitude'] = estacao.latitude
            valoresDiarios['longitude'] = estacao.longitude
            medias = {}
            medias['latitude'] = estacao.latitude
            medias['longitude'] = estacao.longitude

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

if __name__ == '__main__':
    for mes in [str(i + 1).zfill(2) for i in range(12)]:
        for dia in ['01', '11', '21']:
            estado = 'AC'
            # inisim = '2000-01-01'
            inisim = '2000-' + mes + '-' + dia
            # dataplantio = '2000-01-01'
            dataplantio = '2000-' + mes + '-' + dia
            tiposolo = 1
            idgrupo = 25
            estoqueini = 0
            chuvalimite = 30
            mulch = 0.7
            rusurf = 20
            cad = 100
            escsup = 20
            anos = [ano for ano in range(1990, 2014)]

            simular(estado, inisim, dataplantio, tiposolo, idgrupo, estoqueini, chuvalimite, mulch, rusurf, cad, escsup, anos,
                    'agritempo')
