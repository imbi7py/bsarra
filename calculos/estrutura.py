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
    varSaida['ik']=0

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
        self.anosDadosHistoricos = [ano for ano in range(1980, 2012)]
        #self.anosDadosHistoricos = [2013]

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

# Restricoes para culturas anuais
def mediasDecendiais(valoresDiarios, estacao, fases, Risna, Rtemp, Rtmm, TMM, riscoGeada, precMin):
    n = 1+ (valoresDiarios['fase'].last_valid_index().year - valoresDiarios['fase'].first_valid_index().year) # Coletando numero de dias com dados validos para analise
    isna = list(np.zeros(n*math.ceil(fases[2]/10)))  # Lista de decendios da fase 3 com todos os anos
    if (fases[2]%10 != 0): isna.append(0)
    tempMN = list(np.zeros(n*math.ceil(fases[2]/10)))
    tempMD = list(np.zeros(n*math.ceil(sum(fases)/10)))
    tempMX = list(np.zeros(n*math.ceil(fases[2]/10)))
    anof = 0  # Contagem de anos
    i=0
    iMX=0
    iMD=0
    iMN=0
    alerta=[]
    y1=0
    prec=[]
    for j in range(len(valoresDiarios['fase'])):  # Para todos os dados
        if valoresDiarios['fase'][j]>0: # Dados que fazem parte do periodo da cultura
            if (iMD%sum(fases))==0:
                iMD=0
                y1+=1
                prec.append(0)
            prec[y1 - 1] = prec[y1 - 1] + valoresDiarios['prec'][j] # Precipitacao eh a soma de prec em todo o periodo da cultura (cada coluna eh um ano)
            if (math.isnan(valoresDiarios['tmed'][j])) | (valoresDiarios['tmed'][j] == 0):
                x=0 # Nao faz nada
            else: # Temperatura media decendial para todo o periodo da cultura e todo os anos
                if (((iMD // 10) + 1) == (sum(fases)// 10)) and ((sum(fases)% 10) != 0) and iMD>0:
                    iMD += 10 - (iMD % 10)
                    tempMD[iMD // 10] += valoresDiarios['tmed'][j] / (sum(fases) % 10)
                else:
                    tempMD[iMD // 10] += valoresDiarios['tmed'][j] / 10
                iMD += 1
        if (valoresDiarios['fase'][j] == 3) and (i+10<=len(isna)*10):
            # Isna, Temperatura Minima e Temperatura Maxima sao calculados decendiais apenas nas fases 3 de cada ano
            if (math.isnan(valoresDiarios['EtrEtm'][j])) | (valoresDiarios['EtrEtm'][j]==0): #ISNA
                alerta.append(i//10)
                i+=1
            else:
                if i>0 and (i%fases[2])==0 and (fases[2]%10)!=0:
                    i+=10-(i%10)
                    #y2+=1
                if (((i//10)+1)==(fases[2]//10))&((fases[2]%10)!=0):
                    isna[i//10] += valoresDiarios['EtrEtm'][j]/(fases[2]%10)
                    i += 1
                else:
                    isna[i//10] += valoresDiarios['EtrEtm'][j]/10
                    i += 1
            if (math.isnan(valoresDiarios['tmax'][j])) | (valoresDiarios['tmax'][j]==0): # Temperatura Maxima
                x=0
            else:
                if iMX>0 and (iMX%fases[2])==0 and (fases[2]%10)!=0:
                    iMX+=10-(iMX%10)
                    #y3+=1
                if (((iMX//10)+1)==(fases[2]//10))&((fases[2]%10)!=0):
                    tempMX[iMX//10] += valoresDiarios['tmax'][j]/(fases[2]%10)
                    iMX+=1
                else:
                    tempMX[iMX//10] += valoresDiarios['tmax'][j]/10
                    iMX += 1
        #elif (valoresDiarios['fase'][j] == 1):
            if (math.isnan(valoresDiarios['tmin'][j])) | (valoresDiarios['tmin'][j]==0): # Temperatura Minima
                x=0
            else:
                if iMN>0 and (iMN%fases[2])==0 and (fases[2]%10)!=0:
                    iMN+=10-(iMD%10)
                    #y4+=1
                if (((iMN//10)+1)==(fases[2]//10))&((fases[2]%10)!=0):
                    tempMN[iMN//10] += valoresDiarios['tmin'][j]/(fases[2]%10)
                else:
                    tempMN[iMN//10] += valoresDiarios['tmin'][j]/10
                iMN += 1
    #tempMD=list(map(lambda x: x/y1, tempMD))
    #isna=list(map(lambda x: x/y2, isna))
    #tempMX=list(map(lambda x: x/y3, tempMX))
    #tempMN=list(map(lambda x: x/y4, tempMN))
    isnaf = 1
    RG=0
    if riscoGeada:
        #Calculo padronizado com base no cafe
        RG = -270.571 - 10.3 * estacao.latitude - 0.214 * estacao.longitude + 0.073 * estacao.altitude
        if RG>riscoGeada: # Restricao percentual
            print('Risco de Geada')
            if valoresDiarios['mes'][0] in [5, 6, 7, 8, 9]:
                isnaf=0

    #ANALISE DA TEMPERATURA NA FASE 3
    tmp1=0
    tmp=0
    for tm in range(len(tempMX)):
        if (tempMX[tm]!=0) and (tempMN[tm]!=0):
            tmp+=1
            if (tempMX[tm]>float(Rtemp[2])) | (tempMN[tm]<float(Rtemp[0])): tmp1+=1
            #if (tempMX[tm]>(float(Rtemp[1])+float(Rtemp[2]))) | (tempMN[tm]<(float(Rtemp[0])-float(Rtemp[2]))): tmp2+=1
    #if (tmp2 / tmp)>0.2:
        #isnaf = 0
        #print('Temperatura de risco na fase 3')
    print(tmp1/tmp)
    if (tmp1/tmp)>0.2:
        print(tempMN)
        print(tempMX)
        isnaf=0
        print('Temperatura de risco na fase 3')

    tot=0
    val=0
    isnam=[]

    for i in range(len(isna)):
        if (i not in alerta) and (isna[i]>0):
            #print('valido')
            isnam.append(isna[i])
            tot+=1
            if  isna[i] < int(Risna[0]): # RISCO ALTO = valor especifico da cultura
                val+=1
            elif isna[i] < int(Risna[1]): # RISCO MEDIO
                val+=1
    if tot==0: isnaf=isnaf*0.5
    if tot!=0 and (val/tot)>0.2: isnaf=0
    j=0
    t=0
    t2=0
    #Calculo da incidencia de temperaturas abaixo da restricao minima
    #Calculo da incidencia de precipitacao abaixo do esperado para valor "anual" (cultivo)
    for k in range(len(prec)):
        if prec[k]<precMin: j += 1
    #Calculo da incidencia de temperaturas medias mensais fora dos padroes
    tempanalise = TMM[0:(sum(fases)//30)+1][:]
    for m in range(len(tempanalise)):
        for n in range((sum(fases)//30)+1):
            if (tempanalise[m][n] < float(Rtmm[0])) | (tempanalise[m][n]> float(Rtmm[1])): t+=1 # Restricao de risco BAIXO
            if (tempanalise[m][n] < float(Rtmm[0])-float(Rtmm[2])) | (tempanalise[m][n]> float(Rtmm[1])+float(Rtmm[2])): t2+=1 # +margem = restricao de risco MEDIO
    if (t/(((sum(fases)//30)+1)*len(tempanalise)))>0.2:
        isnaf =0
        print('Temperatura mensal fora do padrão')
    elif (t2/(((sum(fases)//30)+1)*len(tempanalise)))>0.2:
        isnaf=isnaf*0.5
        print('Temperatura mensal risco médio')
    #if (min(TMM[:][0:(sum(fases)//30)+1])<float(Rtmm[0]))|(max(TMM[:][0:(sum(fases)//30)+1])>float(Rtmm[1])): isnaf=0 and print('Temp fora dos limites')
    if (j/len(prec))>0.2:
        isnaf=0
        print('Sem chuva suficiente')

    var2 = [estacao.latitude, estacao.longitude]
    columns = ['latitude', 'longitude']
    columns.append('resultado')
    var2.append(isnaf*100)
    columns.append('media isna')
    columns.append('prova isna')
    columns.append('risco geada')
    columns.append('prec fora')
    var2.append(np.mean(isnam)) if tot!=0 else var2.append(50)
    var2.append((1 - 2.5 * val / tot) * 100) if tot!=0 else var2.append(50)
    var2.append(RG)
    var2.append(j/len(prec))


    print(var2)
    media = DataFrame(data=[var2],
                      columns=columns)

    return media

# Restricoes de culturas perenes
def restricoesPerenes(valoresDiarios, BHN, estacao, fases, Risna, Rtemp, Rtmm, TMM, Rtma, riscoGeada, RAlt, RDHA, anoslista):
    isna=100
    isnag=100
    isnat=100
    tm=0
    tmn=0
    for i in range(len(TMM)):
        for j in range(len(TMM[0][:])):
            if len(Rtmm[j])>1: # Restricao de temperatura minima e maxima mensal
                if (TMM[i][j]<float(Rtmm[j][0]))|(TMM[i][j]>float(Rtmm[j][1])): tm+=1
        # Restricao Temperatura no Mes Mais Frio
        if min(TMM[i][:])<float(Rtmm[12]): tmn+=1
    if (tm/(len(TMM)*len(TMM[:][0])))>0.2:
        isna=0
        print("Temperatura Mensal fora do padrão")
    if (tmn/len(TMM))>0.2:
        isna=0
        print('Temperatura do mês mais frio abaixo do normal')
    te=0
    TMA=[]
    if len(Rtma)>1: # Restricao de Temperatura Media Anual
        for t in range(len(TMM)):
            TMA.append(sum(TMM[t][0:12])/12)
            if (TMA[t]<float(Rtma[0]))|(TMA[t]>float(Rtma[1])): te+=1
    if (te/len(TMA))>0.2:
        isna=0
        isnat=0
        print('Temperatura anual fora do padrão')
    #if (te / len(TMA)) > 0.5:
        #isnag=0
        #isna=0

    # Restricao de altitude
    if (estacao.altitude < float(RAlt[0])) | (estacao.altitude > float(RAlt[1])): isna=0
    de=0
    det=0
    isnad=100
    if RDHA:
        #print(BHN)
        for ano in anoslista:
            det+=1
            if ((sum(BHN['Def'][ano]))>float(RDHA)): de+=1
        if (de/det)>0.2:
            isnad=0
            isna=0
    print(tm/(len(TMM)*len(TMM[:][0]))) # Temperatura Media Mensal fora do padrao
    print(tmn/len(TMM)) # Temperatura do mes mais frio fora do padrao
    print(te/len(TMA)) # Temperatura Media Anual fora do padrao
    print(TMA)
    print(sum(BHN['Def'])) # Deficiencia Hidrica Anual
    if riscoGeada:  # Calculo para o cafe
        # PARA TEMPERATURAS ABAIXO DE 0 GRAU
        a = -246.64
        b = 0.0568
        c = 0.1217
        d = 0.0221
        # PARA TEMPERATURAS ABAIXO DE 1 GRAU
        # a = -325.13   b = 0.0606  c = 0.1572  d = 0.0348
        # PARA TEMPERATURAS ABAIXO DE 2 GRAUS
        # a = -374;45   b = 0.0616  c = 0.1808  d = 0.0446
        RG = a + b * estacao.altitude + c * abs(estacao.latitude) * 60 + d * abs(estacao.longitude) * 60
        RG2 = -270.571 - 10.3 * estacao.latitude - 0.214 * estacao.longitude + 0.073 * estacao.altitude
        if RG > riscoGeada:
            isna = 0
            isnag = 0
        print(RG)  # RISCO DE GEADA
        print(RG2)

    var2 = [estacao.latitude, estacao.longitude]
    columns = ['latitude', 'longitude']
    columns.append('total')
    columns.append('geada')
    columns.append('riscoDHA')
    #columns.append('DHA')
    columns.append('tma')
    var2.append(isna)
    var2.append(isnag)
    var2.append(isnad)
    #var2.append(sum(BHN['Def']))
    var2.append(isnat)
    if riscoGeada:
        var2.append(RG)
        columns.append('RG')
    if RDHA:
        var2.append(de/det)
        columns.append('DHA')
    print(var2)
    media = DataFrame(data=[var2],
                      columns=columns)
    #print(media)

    return media
