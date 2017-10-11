from pandas import DataFrame
from datetime import date, timedelta

# Variaveis calculadas diariamente no balanco hidrico
def VariaveisBalHidrico(parametros):

    varSaida = {}
    #
    varSaida['ETP'] = 0
    varSaida['Esc'] = 0
    varSaida['Apport'] = 0

    varSaida['Kc'] = 1
    varSaida['Evs'] = 0
    varSaida['Hum'] = parametros.ESTOQUEINICIAL
    varSaida['Dr'] = 0
    varSaida['Vrad'] = 0
    varSaida['StRurMax'] = 0
    varSaida['Hr'] = 0
    varSaida['Epc'] = 0
    varSaida['Etr'] = 0
    varSaida['Etm'] = 0
    varSaida['Eps'] = 0
    varSaida['StRur'] = 0
    varSaida['StRuSurf'] = 0
    varSaida['StRu'] = parametros.ESTOQUEINICIAL
    varSaida['TP'] = 0
    varSaida['EtrEtm'] = 0
    varSaida['fase'] = 0

    return varSaida



# Parametros de simulacao do balanco hidrico
class ParamSimul():
    def __init__(self):
        ### Valores default para as seguintes variaveis. O usuario pode alterar esses valores
        self.ESTOQUEINICIAL = 0
        self.chuvaLimite = 30 #30
        self.escoamentoSuperficial = 20 # Porcentagem 20
        self.mulch = 0.7
        self.RUSURF = 20 # Reserva util superficial
        self.CAD = 100
        self.tipoSolo = 1
        # self.anosDadosHistoricos = [ano for ano in range(1980, 2012)]
        self.anosDadosHistoricos = [2013]

        ### As datas de plantio e colheita devem ser definidas pelo usuario
        # self.inicioSimul = (1, 1)
        # # self.fimSimul = (12, 31)
        # self.inicioPlantio = (1, 6)
        # self.diaColheita = (4, 15)

class VariaveisSaida(DataFrame):
    def calcularMedia(self, variaveis, cultura, paramSimul, inicioPlantioTuple, estacao, tipoPeriodo, periodo):
        # A variavel tipo Periodo pode ter o valor de 'fase' ou 'mes'
        # Para o valor 'fase', a variavel periodo guarda o numero da fase para a qual deve-se calcular a media
        limitesDadosHistoricos = (min(self.index), max(self.index))
        medias = DataFrame(columns=variaveis)

        if tipoPeriodo == 'fase':

            for ano in list(set(range(limitesDadosHistoricos[0].year, limitesDadosHistoricos[1].year + 1)) & set(paramSimul.anosDadosHistoricos)):
                inicioPlantio = date(ano, inicioPlantioTuple[0], inicioPlantioTuple[1])
                inicioPeriodo = inicioPlantio
                fimPeriodo = inicioPeriodo + timedelta(days=cultura.fases[0] - 1)

                for i in range(periodo - 1): # Calcula o tempo em dias 
                    inicioPeriodo += timedelta(days=cultura.fases[i])
                    fimPeriodo += timedelta(days=cultura.fases[i+1])
                # Calcula medias a partir dos dados, por todo o periodo
                medias = medias.append(DataFrame(self[variaveis].loc[inicioPeriodo:fimPeriodo].mean(),  columns=[ano]).T)

            return DataFrame(medias.mean(), columns=[estacao.codigo]).T
