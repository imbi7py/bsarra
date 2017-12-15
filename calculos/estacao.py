import csv
import datetime
import pandas as pd
import numpy as np
from calendar import monthrange

from calculos.estrutura import VariaveisSaida


class Estacao():
    def __init__(self, cursorSQL = None, dados = 'agritempo'):
        #Colunas existentes nos dados de estacao
        self.keys = ['data', 'tmin', 'tminEst', 'tmed', 'tmedEst',
                'tmax', 'tmaxEst', 'urMin', 'urMinEst',
                'urMax', 'urMaxEst', 'prec', 'precEst']

        self.usedKeys = [1, 3, 5, 11]
        self.numericalKeys = [1, 3, 5, 7, 9, 11]

        if cursorSQL:
            if dados == 'agritempo':
                self.codigo = cursorSQL[0]
                self.nome = cursorSQL[1]
                self.latitude = cursorSQL[2]
                self.longitude = cursorSQL[3]
                self.altitude = cursorSQL[4]
                self.municipioCodigo = cursorSQL[5]
                self.municipioNome = cursorSQL[6]
                self.estadoSigla = cursorSQL[7]
                self.estadoNome = cursorSQL[8]
                self.dados = cursorSQL[9]

            elif dados == 'hadgem' or dados == 'miroc':
                self.codigo = cursorSQL[0]
                self.nome = cursorSQL[1]
                self.latitude = cursorSQL[2]
                self.longitude = cursorSQL[3]
                self.estadoSigla = cursorSQL[4]
                self.estadoNome = cursorSQL[5]
                self.dados = 'dados/' + dados + '/' + self.codigo + '.csv'






    def lerDadosPrecTemp(self, dataInicial = None, dataFinal = None):

        # Se nenhuma data for especificada, pegar todos os dados disponíveis
        if dataInicial is None:
            dataInicial = datetime.date(1800, 1, 1)
            dataFinal = datetime.date(2500, 1, 1)

        if dataFinal is None:
            dataFinal = dataInicial

        precipitacao = {}
        temperatura = {}


        with open(self.dados) as arquivoDados:
            reader = csv.DictReader(arquivoDados, self.keys, delimiter=';')
            cabecalho = True
            data = None

            precipitacaof = np.zeros([12,31])

            for linha in reader:
                if cabecalho is False:
                    if data is None:
                        data = str(linha['data']).rstrip().lstrip()
                        dia = int(data[:2])
                        mes = int(data[3:5])
                        ano = int(data[6:])
                        data = datetime.date(ano, mes, dia)
                    else:
                        data = data - datetime.timedelta(days=1)

                    if data <= dataFinal and data >= dataInicial:

                        precipitacao[data] = None if linha['prec'] == '' else float(linha['prec'].replace(',','.'))
                        temperatura[data] = None if linha['tmed'] == '' else float(linha['tmed'].replace(',', '.'))

                    elif data < dataInicial:
                        break

                    precipitacaof[mes-1,dia-1] += precipitacao[data] #falta dividir por numero de anos


                else:
                    if str(linha['data']).rstrip(' ') == 'data':
                        cabecalho = False

            return (precipitacao, temperatura)

    def lerDadosMeteorologicos(self, anosLista, inicioPlantio, dados = 'agritempo'):

        if dados == 'agritempo':
            return self.lerDadosMeteorologicosAgritempo(anosLista, inicioPlantio)
        elif dados == 'hadgem' or dados == 'miroc':
            return self.lerDadosMeteorologicosHADMIROC()

    def lerDadosMeteorologicosHADMIROC(self): #EDITAR FDD
        dadosMet = pd.read_csv('dadosMetTemp.csv')

        dadosMet = dadosMet[dadosMet['codigoMunicipio'] == self.codigo]
        dadosMet.index = pd.to_datetime(dadosMet['data'])
        dadosMet = dadosMet.reindex(pd.date_range(min(dadosMet.index), max(dadosMet.index)))

        dadosMet['tmed'] = dadosMet['tmed'].interpolate()
        dadosMet['prec'] = (dadosMet['prec']/dadosMet.index.days_in_month).ffill()
        print(dadosMet[['prec','tmed']]) # ANALISAR O QUE TA SAINDO DE DADOS GERADOS PARA DEIXAR UM ANO SO
        return dadosMet[['prec', 'tmed']]

        a = 1






    def lerDadosMeteorologicosAgritempo(self, anosLista, inicioPlantio):

        dadosMeteorologicos = VariaveisSaida(columns=[self.keys[x] for x in self.usedKeys], index=[])
        precipitacao = np.zeros([12,31])
        temperatura = np.zeros([12, 31])

        anos = anosLista + [max(anosLista) + 1]

        with open(self.dados) as arquivoDados:
            reader = csv.DictReader(arquivoDados, self.keys, delimiter=';')
            cabecalho = True
            data = None

            for linha in reader:
                if cabecalho is False:
                    if data is None:
                        data = str(linha['data']).rstrip().lstrip()
                        dia = int(data[:2])
                        mes = int(data[3:5])
                        ano = int(data[6:])
                        data = datetime.date(ano, mes, dia)
                    else:
                        data = data - datetime.timedelta(days=1)

                    if data.year in anos:
                        #precipitacao[data] = None if linha['prec'] == '' else float(linha['prec'].replace(',', '.'))
                        #temperatura[data] = None if linha['tmed'] == '' else float(linha['tmed'].replace(',', '.'))
                        if not linha['prec'] == '':
                            precipitacao[data.month -1, data.day -1] += float(linha['prec'].replace(',', '.'))/len(anosLista)
                        if not linha['tmed'] == '':
                            temperatura[data.month -1, data.day -1] += float(linha['tmed'].replace(',', '.'))/len(anosLista)
                        #dataf = datetime.date(2000, data.month, data.day)
                        dadosMeteorologicos = dadosMeteorologicos.append(VariaveisSaida(linha, columns=[self.keys[x] for x in self.usedKeys], index=[data]))


                else:
                    if str(linha['data']).rstrip(' ') == 'data':
                        cabecalho = False

            indexes = [self.keys[x] for x in list(set(self.usedKeys) & set(self.numericalKeys))]

            for x in indexes:
                dadosMeteorologicos[x] = [y.replace(',', '.') for y in dadosMeteorologicos[x]]

            dadosMeteorologicos[indexes] = \
                dadosMeteorologicos[indexes].apply(pd.to_numeric, errors='coerce')

            # dadosMeteorologicos = dadosMeteorologicos.dropna('index', 'all')

            a = dadosMeteorologicos.first_valid_index()
            #print(a)
            b = dadosMeteorologicos.last_valid_index()
            #print(b)

            if a >= b:
                if (b.month >= inicioPlantio[0]) and (b.day > inicioPlantio[1]):
                    b = datetime.date(b.year + 1, inicioPlantio[0], inicioPlantio[1])
                else:
                    b = datetime.date(b.year, inicioPlantio[0], inicioPlantio[1])
                #if (a.month < 12) | (a.day < 31):
                #    a = datetime.date(a.year - 1, 12, 31)
                idx = [b + datetime.timedelta(days=c) for c in range((a-b).days + 1)]
            else:
                if (a.month >= inicioPlantio[0]) and (a.day > inicioPlantio[1]):
                    a = datetime.date(a.year + 1, inicioPlantio[0], inicioPlantio[1])
                else:
                    a = datetime.date(a.year, inicioPlantio[0], inicioPlantio[1])
                #if (b.month < 12) | (b.day < 31):
                #    b = datetime.date(b.year - 1, 12, 31)
                idx = [a + datetime.timedelta(days=c) for c in range((b-a).days + 1)]
            #print(a)
            #print(b)
            #print(idx)
            dadosMeteorologicos = dadosMeteorologicos.reindex(idx)
            dadosMeteorologicos.interpolate()
            #lista= range(a.year, b.year)
                #for year in anosLista:
                #    if dadosMeteorologicos[self.keys[x]][366*anosLista.index(year)].isnan():
                #        anosLista.remove(year)

                #anosli=[a.year : b.year]

            if dadosMeteorologicos.empty:
                return dadosMeteorologicos
            else:
                dadosmeteorologicosed = dadosMeteorologicos
                for i in range(365):
                    for x in self.usedKeys:
                        #vec = np.zeros(len(self.usedKeys))
                        j=0
                        l = len(dadosMeteorologicos[self.keys[x]])
                        dadosmeteorologicosed[self.keys[x]][i] = 0 #dadosMeteorologicos[self.keys[x]][i]
                        acum=0
                        for year in range(b.year, a.year+1):
                            if (year % 4 == 0)&((acum+i)<l):
                                if not np.isnan(dadosMeteorologicos[self.keys[x]][acum + i]):
                                    dadosmeteorologicosed[self.keys[x]][i] += dadosMeteorologicos[self.keys[x]][acum + i]
                                    j+=1
                                acum += 366
                            elif ((acum+i)<l):
                                if (i>59):
                                    if not np.isnan(dadosMeteorologicos[self.keys[x]][acum + i-1]):
                                        dadosmeteorologicosed[self.keys[x]][i] += dadosMeteorologicos[self.keys[x]][acum + i-1]
                                        j+=1
                                elif not np.isnan(dadosMeteorologicos[self.keys[x]][acum + i]):
                                    dadosmeteorologicosed[self.keys[x]][i] += dadosMeteorologicos[self.keys[x]][acum + i]
                                    j += 1
                                acum += 365
                        #print(dadosmeteorologicosed[self.keys[x]][i])
                        dadosmeteorologicosed[self.keys[x]][i]=dadosmeteorologicosed[self.keys[x]][i]/j

                #for mon in
                #dadosDesejados =
                dadosMeteorologicos = dadosmeteorologicosed[:][0:366]
                #dadosMeteorologicos = dadosMeteorologicos.reindex(ascending=True)
                return dadosMeteorologicos
            #return dadosMeteorologicos


if __name__ == '__main__':
    estacao = Estacao()

