import csv
import datetime
import pandas as pd
from calendar import monthrange

from calculos.estrutura import VariaveisSaida


class Estacao():
    def __init__(self, cursorSQL = None, dados = 'agritempo'):
        self.keys = ['data', 'tmin', 'tminEst', 'tmed', 'tmedEst',
                'tmax', 'tmaxEst', 'urMin', 'urMinEst',
                'urMax', 'urMaxEst', 'prec', 'precEst']

        self.usedKeys = [3, 11]
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


                else:
                    if str(linha['data']).rstrip(' ') == 'data':
                        cabecalho = False

            return (precipitacao, temperatura)

    def lerDadosMeteorologicos(self, anosLista, dados = 'agritempo'):

        if dados == 'agritempo':
            return self.lerDadosMeteorologicosAgritempo(anosLista)
        elif dados == 'hadgem' or dados == 'miroc':
            return self.lerDadosMeteorologicosHADMIROC()

    def lerDadosMeteorologicosHADMIROC(self):
        dadosMet = pd.read_csv('dadosMetTemp.csv')

        dadosMet = dadosMet[dadosMet['codigoMunicipio'] == self.codigo]
        dadosMet.index = pd.to_datetime(dadosMet['data'])
        dadosMet = dadosMet.reindex(pd.date_range(min(dadosMet.index), max(dadosMet.index)))

        dadosMet['tmed'] = dadosMet['tmed'].interpolate()
        dadosMet['prec'] = (dadosMet['prec']/dadosMet.index.days_in_month).ffill()

        return dadosMet[['prec', 'tmed']]

        a = 1






    def lerDadosMeteorologicosAgritempo(self, anosLista):

        dadosMeteorologicos = VariaveisSaida(columns=[self.keys[x] for x in self.usedKeys], index=[])
        precipitacao = {}
        temperatura = {}

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

                        precipitacao[data] = None if linha['prec'] == '' else float(linha['prec'].replace(',', '.'))
                        temperatura[data] = None if linha['tmed'] == '' else float(linha['tmed'].replace(',', '.'))
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
            if dadosMeteorologicos.empty:
                return dadosMeteorologicos
            else:
                a = dadosMeteorologicos.first_valid_index()
                b = dadosMeteorologicos.last_valid_index()
                if a >= b:
                    idx = [b + datetime.timedelta(days=c) for c in range((a-b).days + 1)]
                else:
                    idx = [a + datetime.timedelta(days=c) for c in range((b-a).days + 1)]
                dadosMeteorologicos = dadosMeteorologicos.reindex(idx)
                dadosMeteorologicos.interpolate()
                return dadosMeteorologicos


if __name__ == '__main__':
    estacao = Estacao()

