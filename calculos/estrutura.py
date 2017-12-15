from pandas import DataFrame
from datetime import date, timedelta
import numpy as np
import math

# Variaveis calculadas diariamente no balanco hidrico, quase todas inicializadas em zero
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
        self.mulch = 0.7 #0.2
        self.RUSURF = 20 # Reserva util superficial
        self.CAD = 100
        self.tipoSolo = 1
        # self.anosDadosHistoricos = [ano for ano in range(1980, 2012)]
        self.anosDadosHistoricos = [2013]

        ### As datas de plantio e colheita devem ser definidas pelo usuario
        # self.inicioSimulTuple = (1, 1)
        # # self.fimSimul = (12, 31)
        # self.inicioPlantioTuple = (1, 6)
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

def mediasDecendiais(valoresDiarios, estacao, fases, Risna, Rtemp, Rtmm, TMM):
    isna = list(np.zeros(fases[2]//10))  # Lista de decendios da fase 3
    if (fases[2]%10 != 0): isna.append(0)
    tempMN = list(np.zeros(fases[2]//10))
    if (fases[2] % 10 != 0): tempMN.append(0)
    tempMD = list(np.zeros(sum(fases)//10))
    if (sum(fases) % 10 != 0): tempMD.append(0)
    tempMX = list(np.zeros(fases[2]//10))  # Lista de decendios da fase 3
    if (fases[2]%10 != 0): tempMX.append(0)
    #print(sum(fases))
    anof = 0  # Contagem de anos
    i=0
    iMX=0
    iMD=0
    iMN=0
    alerta=[]
    #valoresDiarios['EtrEtm'].remove(0)
    for j in range(len(valoresDiarios['fase'])):  # Para todos os dados
        if valoresDiarios['fase'][j]>0:
            if (math.isnan(valoresDiarios['tmed'][j])) | (valoresDiarios['tmed'][j] == 0):
                alerta.append(iMD// 10)
            else:
                if (((iMD // 10) + 1) == (sum(fases)// 10)) & ((sum(fases)% 10) != 0):
                    tempMD[iMD // 10] += valoresDiarios['tmed'][j] / (sum(fases) % 10)
                else:
                    tempMD[iMD // 10] += valoresDiarios['tmed'][j] / 10
                iMD += 1
        if (valoresDiarios['fase'][j] == 3):
            if (math.isnan(valoresDiarios['EtrEtm'][j])) | (valoresDiarios['EtrEtm'][j]==0):
                alerta.append(i//10)
            else:
                if (i%fases[2])==0:
                    i=0
                    #anof+=1
                if (((i//10)+1)==(fases[2]//10))&((fases[2]%10)!=0):
                    isna[i//10] += valoresDiarios['EtrEtm'][j]/(fases[2]%10)
                else:
                    isna[i//10] += valoresDiarios['EtrEtm'][j]/10
                i += 1
            if (math.isnan(valoresDiarios['tmax'][j])) | (valoresDiarios['tmax'][j]==0):
                alerta.append(iMX//10)
            else:
                if (iMX%fases[2])==0:
                    iMX=0
                    #anof+=1
                if (((iMX//10)+1)==(fases[2]//10))&((fases[2]%10)!=0):
                    tempMX[iMX//10] += valoresDiarios['tmax'][j]/(fases[2]%10)
                else:
                    tempMX[iMX//10] += valoresDiarios['tmax'][j]/10
                iMX += 1
        #elif (valoresDiarios['fase'][j] == 1):
            if (math.isnan(valoresDiarios['tmin'][j])) | (valoresDiarios['tmin'][j]==0):
                alerta.append(iMN//10)
            else:
                if (iMN%fases[2])==0:
                    iMN=0
                    #anof+=1
                if (((iMN//10)+1)==(fases[2]//10))&((fases[2]%10)!=0):
                    tempMN[iMN//10] += valoresDiarios['tmin'][j]/(fases[2]%10)
                else:
                    tempMN[iMN//10] += valoresDiarios['tmin'][j]/10
                iMN += 1
    print(alerta)
    #isna = isna / anof  # Media dos anos
    isnaf=1
    #isna=0.6*isna
    if range(len(isna)) in alerta:
        isnaf = 10
    for i in range(len(isna)):
        if i not in alerta:
            if  isna[i] < int(Risna[0]): # RISCO ALTO = depois substituir por valor especifico da cultura
                isnaf=isnaf*0
            elif isna[i] < int(Risna[1]): # RISCO MEDIO
                isnaf=isnaf*0.5
        #elif (math.isnan(isna[i])):
            #isnaf=5 # Dados incompletos

    print(isna)
    print(isnaf)
    print(tempMX)
    print(tempMD)
    print(tempMN)
    #if (max(tempMX)>=float(Rtemp[2])) and (Rtemp[2]!='0'): isnaf=0 and print('Exc Temp max')
    #if (min(tempMD)<=float(Rtemp[1])) and (Rtemp[1]!='0'): isnaf=0 and print('Exc Temp med')
    #if (min(tempMN)<=float(Rtemp[0])) and (Rtemp[0]!='0'): isnaf=0 and print('Exc Temp min')
    print(TMM)
    if (min(TMM)<float(Rtmm[0]))|(max(TMM)>float(Rtmm[1])): isnaf=0 and print('Temp fora dos limites')
    if sum(valoresDiarios['prec'][0:sum(fases)])<500: isnaf=0 and print('Sem chuva suficiente')
    var2 = [estacao.latitude, estacao.longitude]
    #print(len(isnaf))
    #isna[0]=isnaf*100
    columns = ['latitude', 'longitude']
    columns.append('dec1')
    var2.append(isnaf*100)

    for i in range(len(isna)):
        dec = "dec" + str(i+2)
        columns.append(dec)
        var2.append(isna[i])




    #print(columns)
    print(var2)
    media = DataFrame(data=[var2],
                      columns=columns)
    #print(media)

    return media


def restricoesPerenes(valoresDiarios, estacao, fases, Risna, Rtemp, Rtmm, TMM, Rtma, riscoGeada):
    isna=100
    for k in Rtmm: Rtmm[Rtmm.index(k)] = k.split("/")
    for i in range(len(Rtmm)):
        if len(Rtmm[i])>1:
            if (TMM[i]<float(Rtmm[i][0]))|(TMM[i]>float(Rtmm[i][1])): isna=0
        elif i==len(Rtmm[i]):
            if min(TMM)<float(Rtmm[i]): isna=0

    if len(Rtma)>1:
        TMA=sum(TMM)/len(TMM)
        if (TMA<float(Rtma[0]))|(TMA>float(Rtma[1])): isna=0

    if riscoGeada:
        RG = -270.571 - 10.3 * estacao.latitude - 0.214 * estacao.longitude + 0.073 * estacao.altitude
        if RG>riscoGeada: isna=0



    var2 = [estacao.latitude, estacao.longitude]
    columns = ['latitude', 'longitude']
    columns.append('dec1')
    var2.append(isna)
    print(var2)
    media = DataFrame(data=[var2],
                      columns=columns)
    #print(media)

    return media
