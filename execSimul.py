# -*- coding: utf-8 -*-
import os.path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame
from calculos.balancoHidrico import balancoHidrico
from calculos.balancoHidrico import balancoHidrico
from calculos.cultura import Cultura
from calculos.estacao import Estacao
from calculos.estrutura import ParamSimul, mediasDecendiais, restricoesPerenes
import math
import numpy
import datetime


### Funcao que dispara a simulacao do balanco hidrico ###
def simular(estado,inisim,dataplantio,tiposolo,idgrupo,estoqueini,chuvalimite,mulch,rusurf,escsup,anos, dados = 'agritempo'):
    #### Parâmetros a serem definidos pelo usuário

    inisimdia = int(inisim[8:10]) # Data de inicio da simulacao
    inisimmes = int(inisim[5:7])
    dataplantiodia = int(dataplantio[8:10]) # Data de inicio do plantio
    dataplantiomes = int(dataplantio[5:7])

    # anos.append(max(anos) + 1)
    # Datas juntas: mes, dia
    inicioSimul = (inisimmes,inisimdia)
    inicioPlantio = (dataplantiomes, dataplantiodia)

    #variaveis = ['EtrEtm'] # ISNA final, variáveis desejadas
    parametros = ParamSimul() # Inicializando os parametros
    # Utilizar dados fornecidos pelo usuario, dados de entrada da funcao
    parametros.chuvaLimite = chuvalimite
    parametros.ESTOQUEINICIAL = estoqueini
    parametros.escoamentoSuperficial = escsup # Porcentagem
    parametros.mulch = mulch
    parametros.RUSURF = rusurf # Reserva Útil superficial
    parametros.CAD = 100
    parametros.tipoSolo = tiposolo
    parametros.anosDadosHistoricos = list(map(int, anos))

    # Selecionar cultura
    cultura = Cultura()
    cultura.carregarDoBD(idgrupo) #carregar dados de acordo com as configs de cultura
    #parametros.CAD=cultura.reservaUtilSolo[tiposolo-1]

    #print(cultura.reservaUtilSolo)
    #print(parametros.CAD)

    #fazer o endereco da planilha com base na cultura, estado, banco de dados e data
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


    #### Selecionar todas as estações de um estado
    conn = sqlite3.connect('sarra.db')
    cursor = conn.cursor()

    dados = dados.lower() #deixar todas as letras em minusculo

    if dados == 'agritempo': # Obter dados da estacao e dos municipios pelo bd de culturas anuais
        cursor.execute('''
        SELECT estacao.codigo, estacao.nome, estacao.latitude, estacao.longitude,
        estacao.altitude, estacao.municipio, municipio.nome, municipio.estado, estado.nome, estacao.dados
        FROM estacao, municipio, estado
        WHERE municipio.codigo = estacao.municipio AND municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))

    elif dados == 'hadgem' or dados == 'miroc': # Obter dados de outro banco de dados, CADE ESTACAO.DADOS?
        cursor.execute('''
                SELECT municipio.codigo, municipio.nome, municipio.latitude, municipio.longitude,
                municipio.estado, estado.nome
                FROM municipio, estado
                WHERE municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))
    else: # Encontrar erros
        print('erro')



    # Fazer lista com estacoes para a regiao
    estacoes = []

    for linha in cursor.fetchall():
        estacoes.append(Estacao(cursorSQL=linha, dados = dados)) # Junta tabelas


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
    medias = pd.DataFrame()

    #Atualmente gerando apenas o isna para controle de valores

    for estacao in estacoes:
        print(estacao.nome + ': ' + str(n) + ' de ' + str(nEstacoes))
        # if os.path.isfile(endereco + str(estacao.codigo) + '.csv'):
        #     valoresDiarios[estacao.codigo] = pd.read_csv(endereco + str(estacao.codigo) + '.csv')
        # else:
        simulacao = balancoHidrico(estacao, cultura) # Define o balanco hidrico, inicializa nomes das colunas
        simulacao.lerDadosMeteorologicos(estacao, parametros, inicioSimul, dados) # Carrega dados de acordo com o banco de dados usado
        #simulacao.temperaturaMensalMedia
        #print(simulacao.dadosMeteorologicos)
        #diasmes = [0,31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        #print(sum(simulacao.dadosMeteorologicos['prec'][200:205]))
        #if estacao.codigo==9001125:
            #print(simulacao.dadosMeteorologicos['tmed'][:3])
            #diasmes = [0,31,28,31,30,31,30,31,31,30,31,30,31]
            #meses = ['Jan','Fev','Mar', 'Abr','Maio','Jun','Julho','Ago','Set','Out','Nov','Dez']
            #temp = numpy.zeros(12)
            #irr = numpy.zeros(12)

        #temp = numpy.zeros((len(simulacao.dadosMeteorologicos['tmed']))+1)
        #irr = numpy.zeros((len(simulacao.dadosMeteorologicos['tmed'])) + 1)
        #for k in range(len(simulacao.dadosMeteorologicos['tmed'])//10):
        #    if k!=(len(simulacao.dadosMeteorologicos['tmed'])//10):
        #        temp[k] = sum(simulacao.dadosMeteorologicos['tmed'][k:k+10])/10
        #        irr[k] = sum(simulacao.dadosMeteorologicos['prec'][k:k+10])/10
        #    else:
        #        temp[k] = sum(simulacao.dadosMeteorologicos['tmed'][k:k + len(simulacao.dadosMeteorologicos['tmed'])%10])/(len(simulacao.dadosMeteorologicos['tmed'])%10)
        #        irr[k] = sum(simulacao.dadosMeteorologicos['prec'][k:k + len(simulacao.dadosMeteorologicos['tmed'])%10])/(len(simulacao.dadosMeteorologicos['tmed'])%10)
        #extra = pd.DataFrame(data=[temp, irr], columns=['temp dec', 'prec dec'])
        #extra.to_csv(enderecoSaida + 'total.csv')
            #plt.plot(range(12),temp)
            #plt.grid(True)
            #plt.ylabel('Temperatura Mensal')
            #plt.show()
            #plt.plot(range(12),irr)
            #plt.grid(True)
            #plt.ylabel('Precipitacao')
            #plt.show()
        resultado = simulacao.simularBalancoHidrico(inicioSimul, inicioPlantio) # Gera os valores do balanco hidrico
        #print(resultado)
        #jm = simulacao.dadosMeteorologicos.index(datetime.date(2011,5,3))
        # ano=self.dadosMeteorologicos[:][jm].year
        #print(jm)
        if not isinstance(resultado, str):
            print('ok')
            valoresDiarios[estacao.codigo] = resultado[0]
            #print(simulacao.dadosMeteorologicos)
            #print(valoresDiarios[estacao.codigo][250:320])
            balancoHidricoNormal[estacao.codigo] = resultado[1]
            if idgrupo<=48:
                media = mediasDecendiais(valoresDiarios[estacao.codigo],estacao,cultura.fases,cultura.restricoesISNA,
                                         cultura.restricoesTEMP, cultura.restricoesTMM, simulacao.temperaturaMensalMedia)
            else:
                media = restricoesPerenes(valoresDiarios[estacao.codigo], estacao, cultura.fases, cultura.restricoesISNA,
                                          cultura.restricoesTEMP, cultura.restricoesTMM, simulacao.temperaturaMensalMedia,
                                          cultura.restricoesTMA, cultura.riscoGeada)
            #print(media)
            valoresDiarios['latitude'] = estacao.latitude
            valoresDiarios['longitude'] = estacao.longitude
            #print(resultado[0])
            temp = numpy.zeros((len(resultado[0]['tmed']))//10 + 2)
            irr = numpy.zeros((len(resultado[0]['tmed']))//10 + 2)
            etr=numpy.zeros((len(resultado[0]['tmed']))//10 + 2)
            etm=numpy.zeros((len(resultado[0]['tmed']))//10 + 2)
            etp=numpy.zeros((len(resultado[0]['tmed']))//10 + 2)
            isna=numpy.zeros((len(resultado[0]['tmed']))//10 + 2)
            for k in range(len(resultado[0]['tmed'])//10+1):
                if k != (len(resultado[0]['tmed']) // 10):
                    temp[k] = sum(resultado[0]['tmed'][k*10:k*10+10]) / 10
                    irr[k] = sum(resultado[0]['prec'][k*10:k*10+10])
                    etr[k] = sum(resultado[0]['Etr'][k*10:k*10+10])/10
                    etm[k] = sum(resultado[0]['Etm'][k*10:k*10+10]) / 10
                    etp[k] = sum(resultado[0]['ETP'][k*10:k*10+10]) / 10
                    isna[k] = sum(resultado[0]['EtrEtm'][k*10:k*10+10]) / 10
                else:
                    temp[k] = sum(resultado[0]['tmed'][k*10:k*10 + len(resultado[0]['tmed']) % 10]) / (len(resultado[0]['tmed']) % 10)
                    irr[k] = sum(resultado[0]['prec'][k*10:k*10 + len(resultado[0]['tmed']) % 10])
                    etr[k]=sum(resultado[0]['Etr'][k*10:k*10 + len(resultado[0]['tmed']) % 10]) / (len(resultado[0]['tmed']) % 10)
                    etm[k] = sum(resultado[0]['Etm'][k*10:k*10 + len(resultado[0]['tmed']) % 10]) / (len(resultado[0]['tmed']) % 10)
                    etp[k] = sum(resultado[0]['ETP'][k*10:k*10 + len(resultado[0]['tmed']) % 10]) / (len(resultado[0]['tmed']) % 10)
                    isna[k] = sum(resultado[0]['EtrEtm'][k*10:k*10 + len(resultado[0]['tmed']) % 10]) / (len(resultado[0]['tmed']) % 10)
            extra = pd.DataFrame(data=[temp, irr, etr, etm, etp, isna], index=['temp dec', 'prec dec', 'ETR', 'ETM', 'ETP', 'ISNA']).T
            extra.to_csv('simulacoes/analise/'+ str(estacao.codigo) +'.csv')


            #CALCULAR MEDIA DO ISNA POR DECENDIO
            #j=0
            #isna=numpy.zeros(100) # Lista de dias da fase 3 .: Substituir 100 por dias da fase 3 para cultura especifica
            #anoi=1200 # Ano atual
            #anof=0 # Contagem de anos
            #f=valoresDiarios[estacao.codigo]['ano']
            #while (j < len(valoresDiarios[estacao.codigo]['fase'])): # Para todos os dados
            #    if not (valoresDiarios[estacao.codigo]['fase'][j]!=3)|(math.isnan(valoresDiarios[estacao.codigo]['EtrEtm'][j])):
            #        if (int(valoresDiarios[estacao.codigo]['ano'][j])!=anoi): # Reiniciar ano, reiniciar fase
            #            i=0
            #            anof+=1 # Contagem de anos válidos
            #        isna[i]+=valoresDiarios[estacao.codigo]['EtrEtm'][j]
            #        i+=1
            #        anoi=valoresDiarios[estacao.codigo]['ano'][j] # Atualizar ano a ser analizado

            #    j+=1
            #isna=isna/anof # Media dos anos
            #isnaf=numpy.zeros(10) # deixar em função do tamanho de ISNA
            #for k in range(len(isna)):
            #    if (k//10)==(len(isna)//10):
            #        isnaf[k//10]+=isna[k]/(len(isna)%10)
            #    else:
            #        isnaf[k//10]+=isna[k]/10
            #temp=[estacao.latitude, estacao.longitude]
            #var2=numpy.concatenate((temp, isnaf), axis=0)

            #media=pd.DataFrame(data=[var2],columns=['latitude','longitude','isna','isna','isna','isna','isna','isna','isna','isna','isna','isna'])
            #print(media)

            medias = medias.append(media)
            #print(medias)


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
    medias.to_csv(enderecoSaida + 'total.csv')

if __name__ == '__main__':
    for mes in [str(i + 1).zfill(2) for i in range(11,12)]:
        for dia in ['21']:
            estado = 'SP'
            messim = int(mes) - 1
            # inisim = '2000-01-01'
            inisim = '2000-' + mes + '-' + dia
            #inisim = '2000-' + str(messim).zfill(2) + '-' + dia #inisim = min(estacao.dados.data) # ANO, atualmente eh 2000 mesmo
            # dataplantio = '2000-01-01'
            dataplantio = '2000-' + mes + '-' + dia
            tiposolo = 1
            idgrupo = 25
            estoqueini = 0
            chuvalimite = 30
            mulch = 0.7
            rusurf = 20
            escsup = 20
            anos = [ano for ano in range(1990, 2016)] # editar para pertencer aos dados

            simular(estado, inisim, dataplantio, tiposolo, idgrupo, estoqueini, chuvalimite, mulch, rusurf, escsup, anos,'agritempo')
