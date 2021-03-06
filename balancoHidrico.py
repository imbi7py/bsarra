from datetime import date, timedelta

import numpy as np
import math
import pandas as pd
from pyeto import deg2rad, daylight_hours, sunset_hour_angle, sol_dec

from calculos import calculosDecendiais
from calculos.cultura import Cultura
from calculos.estacao import Estacao
from calculos.estrutura import VariaveisBalHidrico, ParamSimul, VariaveisSaida


# A classe balancoHidrico efetua os calculos do balanco hidrico seguindo
# o modelo SARRA. A classe eh inicializada com dados da Estacao e
# da cultura. O metodo simularBalancoHidrico() realiza os calculos e retorna
# um DataFrame com os valores diarios das variaveis


class balancoHidrico():
    def __init__(self, estacao, cultura): # Inicializa objeto, como dataframe com variaveis de colunas

        self.cultura = cultura # Carrega cultura
        self.ETPsDecendiais = {}
        # self.valoresDiarios = {}
        self.columns = ['Data','ETP', 'Esc', 'Apport', 'Kc', 'Evs', 'Hum', 'Dr', 'Vrad',
                        'StRurMax', 'Hr', 'Epc', 'Etr', 'Etm', 'Eps', 'StRur', 'StRuSurf',
                        'StRu', 'TP', 'EtrEtm', 'fase']
        # self.variaveisSaida = VariaveisSaida(columns=self.columns)
        self.variaveisSaida = pd.DataFrame(columns=self.columns)

    def lerDadosMeteorologicos(self, estacao, parametros, dados = 'agritempo'):
        self.parametros = parametros

        self.estacao = estacao

        self.parametros.RESERVAUTIL = self.cultura.reservaUtilSolo[self.parametros.tipoSolo - 1] # Calcula reserva util
        self.parametros.PROFMAXIMA = self.parametros.RESERVAUTIL * 1000/self.parametros.CAD # Mais dados da reserva

        self.dadosMeteorologicos = self.estacao.lerDadosMeteorologicos(self.parametros.anosDadosHistoricos, dados)

        if not self.dadosMeteorologicos.empty:
            self.limitesDadosHistoricos = (self.dadosMeteorologicos.dropna(how='any').first_valid_index(),
                                           self.dadosMeteorologicos.dropna(how='any').last_valid_index())
            self.dadosMeteorologicos['irrigacao'] = 0

            if dados == 'hadgem' or dados == 'miroc':
                self.limitesDadosHistoricos = (self.limitesDadosHistoricos[0].date(), self.limitesDadosHistoricos[1].date())


            anosDisponiveis = [ano for ano in range(self.limitesDadosHistoricos[0].year, self.limitesDadosHistoricos[1].year + 1)]
            if self.limitesDadosHistoricos[0].day > 1 or self.limitesDadosHistoricos[0].month > 1:
                anosDisponiveis.remove(self.limitesDadosHistoricos[0].year)
            if self.limitesDadosHistoricos[1].day < 31 or self.limitesDadosHistoricos[1].month < 11:
                anosDisponiveis.remove(self.limitesDadosHistoricos[1].year)

            self.ETPsDecendiais = self.etp_Thornthwaite([ano for ano in self.parametros.anosDadosHistoricos if ano in anosDisponiveis])



    # Cálculo dos ETPs decendiais
    def etp_Thornthwaite(self, anosCalculoETP):
        latitudeRad = deg2rad(self.estacao.latitude)

        temperaturaMensalAcc = np.array([]).reshape(0, 12)
        temperaturaDecendioAcc = np.array([]).reshape(12, 3, 0)
        ETPs = {}

        # O ETP é calculado anualmente e o resultado final é a média desses cálculos
        # anosCalculoETP grava os anos selecionados pelo usuário para o cálculo do ETP
        if anosCalculoETP:
            for ano in anosCalculoETP:
                ### Calcula medias mensais e decendiais de temperatura para um ano ###
                diaAtual = date(ano, 1, 1)

                temperaturaAcum = 0
                temperaturaAcumMes = 0
                diasNoDecendio = 0
                diasNoMes = 0

                temperaturaMensal = []
                temperaturaDecendio = np.zeros((12, 3))


                while diaAtual.year == ano:
                    if self.dadosMeteorologicos['tmed'][diaAtual] is not None:
                        temperaturaAcum += self.dadosMeteorologicos['tmed'][diaAtual]
                        temperaturaAcumMes += self.dadosMeteorologicos['tmed'][diaAtual]
                        diasNoDecendio += 1
                        diasNoMes += 1

                    amanha = diaAtual + timedelta(days=1)


                    if amanha.month != diaAtual.month:
                        if diasNoMes > 0:
                            # Corrigir temperaturas negativas
                            temperaturaMensal.append(temperaturaAcumMes/diasNoMes * (temperaturaAcumMes >= 0))
                        else:
                            temperaturaMensal.append(25)

                        temperaturaAcumMes = 0
                        diasNoMes = 0

                    if amanha.day == 1 or amanha.day == 11 or amanha.day == 21:
                        decendioAtual = calculosDecendiais.converterToDataDecendio(diaAtual)
                        if diasNoDecendio > 0:
                            temperaturaDecendio[decendioAtual[0] - 1, decendioAtual[1] - 1] = (temperaturaAcum/diasNoDecendio) * (temperaturaAcum >= 0)
                        else:
                            temperaturaDecendio[decendioAtual[0] - 1, decendioAtual[1] - 1] = 25

                        temperaturaAcum = 0
                        diasNoDecendio = 0

                    diaAtual = amanha

                ###########
                temperaturaMensalAcc = np.vstack((temperaturaMensalAcc, temperaturaMensal))
                temperaturaDecendioAcc = np.dstack((temperaturaDecendioAcc, temperaturaDecendio))



            temperaturaMensalMedia = np.mean(temperaturaMensalAcc, axis=0)
            temperaturaDecendioMedia = np.mean(temperaturaDecendioAcc, axis=2)

            # Calcula o heat index a partir das temperaturas
            self.temperaturaMensalMedia = temperaturaMensalMedia
            I = 0.0
            for Tai in temperaturaMensalMedia:
                if Tai / 5.0 > 0.0:
                    I += (Tai / 5.0) ** 1.514

            a = (6.75e-07 * I ** 3) - (7.71e-05 * I ** 2) + (1.792e-02 * I) + 0.49239

            diaAtual = date(2000, 1, 1)


            horasDeSolAcum = 0
            diasNoDecendio = 0

            # Calcula o valor dos ETPs decendiais
            while diaAtual.year == 2000:
                sd = sol_dec(int(diaAtual.strftime('%j')))
                sha = sunset_hour_angle(latitudeRad, sd)
                horasDeSolAcum += daylight_hours(sha)


                diasNoDecendio += 1

                amanha = diaAtual + timedelta(days=1)

                if amanha.day == 1 or amanha.day == 11 or amanha.day == 21:
                    horasDeSolMedia = horasDeSolAcum/diasNoDecendio

                    decendioAtual = calculosDecendiais.converterToDataDecendio(diaAtual)
                    ETPs[decendioAtual] = 1.6 * (horasDeSolMedia / 12.0) * (diasNoDecendio / 30.0) * ((10.0 * temperaturaDecendioMedia[decendioAtual[0] - 1, decendioAtual[1] - 1] / I) ** a) * 10.0
                    horasDeSolAcum = 0
                    diasNoDecendio = 0

                diaAtual = amanha

        return ETPs


    # Calcula o valor do ETP diario interpolando valores decendiais
    def calcularETP(self, dia):
        decendio = calculosDecendiais.converterToDataDecendio(dia) # passa de dia para decendio
        decendioFuturo = calculosDecendiais.proximoDecendio(decendio)
        etpAtual = self.ETPsDecendiais[decendio] # recebe dado
        etpFuturo = self.ETPsDecendiais[decendioFuturo]
        # retorna ETP estimado
        return (etpAtual + (etpFuturo - etpAtual) * ((dia - calculosDecendiais.inicioDecendio(dia)).days) / calculosDecendiais.diasNoDecendio(dia)) / 10



    def calcularEsc(self, diaAtual):
        # Soma dados de precipitacao e irrigacao
        enplus = self.dadosMeteorologicos['prec'][diaAtual] + self.dadosMeteorologicos['irrigacao'][diaAtual]
        esc = 0
        # Se a agua que entrou no sistema eh maior que o que ele pode armazenar, ha escoamento
        # Ele eh encontrado em funcao do parametro escoamento superficial e a agua que esta transbordando
        if enplus > self.parametros.chuvaLimite:
            esc = (enplus - self.parametros.chuvaLimite) * self.parametros.escoamentoSuperficial/100

        return esc


    def calcularApport(self, diaAtual, Esc):
        return self.dadosMeteorologicos['prec'][diaAtual] + self.dadosMeteorologicos['irrigacao'][diaAtual] - Esc


    def calcularEps(self, etp):
        return self.parametros.mulch * etp

    def rempliRu(self, Apport, StRu, Hum):

        # Alteração. Notou-se que esse valor é fixo e igual à Reserva Útil. O cálculo não precisa ser feito sempre
        # StRuMax = self.parametros.RESERVAUTIL*self.parametros.PROFMAXIMA/1000
        StRu = StRu + Apport
        Dr = 0

        # if StRu > StRuMax:
        #     Dr = StRu - StRuMax
        #     StRu = StRuMax

        if StRu > self.parametros.RESERVAUTIL: # Valores maiores do que a reserva util
            Dr = StRu - self.parametros.RESERVAUTIL # O quanto sobra
            StRu = self.parametros.RESERVAUTIL # StRu maximo deve ser a reserva util

        Hum = max(Hum, StRu) # Atualiza HUM como sempre o maximo de reserva util
        return (StRu, Hum, Dr)

    def calcularKc(self, diaAtual, inicioPlantio):
        decendioAtual = (((diaAtual - inicioPlantio).days) // 10) + 1 # Transforma em decendio onde o inicio do plantio eh o zero
        nDias = (diaAtual - inicioPlantio - timedelta((decendioAtual - 1) * 10)).days # Dias total desde que o decendio comecou

        if decendioAtual - 1 < len(self.cultura.kc): # Se o decendio faz parte do ciclo
            kcAtual = self.cultura.kc[decendioAtual - 1] # Kc eh calculado por decendio, acessado a partir de zero
        else: # Esse decendio eh invalido
            kcAtual = 1

        if decendioAtual < len(self.cultura.kc): # Se o decendio faz parte do ciclo
            kcProx = self.cultura.kc[decendioAtual] # Proximo Kc ja eh definido
        else:
            kcProx = 1

        # Kc final eh determinado como o Kc do inicio do decendio mais uma proporcao de variacao em funcao dos dias que se passaram
        return kcAtual + (kcProx - kcAtual)*nDias / calculosDecendiais.diasNoDecendio(diaAtual)

    def calcularVrad(self, Hum, StRurMax):
        vRad = 100*(Hum - StRurMax)/self.parametros.RESERVAUTIL
        deltaRur = (Hum - StRurMax)/10
        #deltaRur = min(Hum - StRurMax, vRad/1000*self.parametros.RESERVAUTIL) # Nao faz sentido, sempre vai dar um decimo de (Hum - StRURMAx)

        return vRad, deltaRur

    def calcularHr(self, StRur, StRurMax):
        Hr = 0

        if StRurMax > 0:
            Hr = StRur/StRurMax

        return Hr

    def calcularEtrEtm(self, Epc, ETP, Hr, Evs, StRur, Etm): #ISNA
        # Formula da evapotranspiracao REAL
        Etr = Epc * (( -0.05 + 0.732/ETP) + (4.97 - 0.66*ETP) * Hr + (-8.57 + 1.56*ETP)*Hr*Hr + (4.35 - 0.88*ETP)*Hr*Hr*Hr)
        TP = Etr

        if Etr > Evs:
            Etm = Epc
            Etr = min(Etr, Etm) # ETR nao pode ser maior que a maxima
            Etr = max(Etr, 0) # ETR nao pode ser negativa
            Etr = min(StRur, Etr) # ETR nao pode ser maior que St Reserva Util R
        else:
            Etr = Evs

        return Etr, Etm, TP

    def encontrarEstacaoUmida(self, P_ETP):
        mesAtual = 0
        mesInicio = 0
        mesFim = 0
        melhorMesInicio = 0
        melhorMesFim = 0
        melhorAcc = 0
        P_ETP_Acc = 0
        while 1:
            if P_ETP[mesAtual % 12] >= 0:
                P_ETP_Acc = P_ETP_Acc + P_ETP[mesAtual % 12]
                mesFim = mesAtual

                if mesAtual == mesInicio + 12:
                    break

            else:
                if P_ETP_Acc > melhorAcc:
                    melhorMesInicio = mesInicio
                    melhorMesFim = mesFim
                    melhorAcc = P_ETP_Acc

                P_ETP_Acc = 0
                mesInicio = mesAtual + 1

                if mesInicio > 11:
                    break

            mesAtual = (mesAtual + 1)

        melhorMesFim = melhorMesFim % 12

        return (melhorMesInicio + 1, melhorMesFim + 1)


    def balancoHidricoNormal(self):
        balancoHidricoNormalDF = self.dadosMeteorologicos
        balancoHidricoNormalDF.index = pd.to_datetime(balancoHidricoNormalDF.index)

        balancoHidricoNormalDF['ano'] = balancoHidricoNormalDF.index.year
        balancoHidricoNormalDF['mes'] = balancoHidricoNormalDF.index.month

        balancoHidricoNormalDF = balancoHidricoNormalDF.groupby(['ano', 'mes']).aggregate({'prec': np.sum, 'mes': np.mean}).groupby(['mes']).aggregate(
            {'prec': np.mean})

        ETPMensal = {}

        for mes in range(1, 13):
            ETPMensal[mes] = self.ETPsDecendiais[(mes, 1)] + self.ETPsDecendiais[(mes, 2)] + self.ETPsDecendiais[(mes, 3)]

        balancoHidricoNormalDF = pd.concat([balancoHidricoNormalDF, pd.Series(ETPMensal, name='ETP')], axis=1)
        balancoHidricoNormalDF['P - ETP'] = balancoHidricoNormalDF['prec'] - balancoHidricoNormalDF['ETP']

        # Encontrar o último mês da estação seca
        (inicioEstacaoUmida, fimEstacaoUmida) = self.encontrarEstacaoUmida(balancoHidricoNormalDF['P - ETP'].tolist())
        balancoHidricoNormalDF['ARM'] = 0
        balancoHidricoNormalDF['Neg'] = 0
        balancoHidricoNormalDF['Alt'] = 0
        balancoHidricoNormalDF['Etr'] = 0
        balancoHidricoNormalDF['Def'] = 0
        balancoHidricoNormalDF['Exc'] = 0


        # Inicializar o BH
        if (np.sum(balancoHidricoNormalDF['P - ETP']) >= 0) or \
                (np.sum(balancoHidricoNormalDF['P - ETP']) < 0 and \
                         np.sum(balancoHidricoNormalDF.loc[balancoHidricoNormalDF['P - ETP'] > 0, 'P - ETP']) >= self.parametros.CAD):
            balancoHidricoNormalDF.loc[fimEstacaoUmida, 'ARM'] = self.parametros.CAD
        else:
            balancoHidricoNormalDF.loc[fimEstacaoUmida, 'Neg'] = self.parametros.CAD*np.log((np.sum(balancoHidricoNormalDF.loc[balancoHidricoNormalDF['P - ETP'] > 0, 'P - ETP'])/self.parametros.CAD)/ \
                  (1 - np.exp(np.sum(balancoHidricoNormalDF.loc[balancoHidricoNormalDF['P - ETP'] < 0, 'P - ETP'])/self.parametros.CAD)))

            balancoHidricoNormalDF.loc[fimEstacaoUmida, 'ARM'] = self.parametros.CAD*np.exp(balancoHidricoNormalDF['Neg'][fimEstacaoUmida]/self.parametros.CAD)

        for mes in range(fimEstacaoUmida + 1, fimEstacaoUmida + 13):
            if mes <= 12:
                mesAtual = mes
                mesAnterior = mesAtual - 1
            else:
                mesAtual = mes % 12

                if mesAtual == 1:
                    mesAnterior = 12
                elif mesAtual == 0:
                    mesAtual = 12
                    mesAnterior = 11
                else:
                    mesAnterior = mesAtual - 1

            if balancoHidricoNormalDF['P - ETP'][mesAtual] < 0:
                balancoHidricoNormalDF.loc[mesAtual, 'Neg'] = balancoHidricoNormalDF['Neg'][mesAnterior] + \
                                                              balancoHidricoNormalDF['P - ETP'][mesAtual]
                balancoHidricoNormalDF.loc[mesAtual, 'ARM'] = self.parametros.CAD * np.exp(
                    balancoHidricoNormalDF['Neg'][mesAtual] / self.parametros.CAD)

            else:
                balancoHidricoNormalDF.loc[mesAtual, 'ARM'] = min(
                    balancoHidricoNormalDF['ARM'][mesAnterior] + balancoHidricoNormalDF['P - ETP'][mesAtual], self.parametros.CAD)
                balancoHidricoNormalDF.loc[mesAtual, 'Neg'] = self.parametros.CAD * np.log(
                    balancoHidricoNormalDF['ARM'][mesAtual] / self.parametros.CAD)

            balancoHidricoNormalDF.loc[mesAtual, 'Alt'] = balancoHidricoNormalDF['ARM'][mesAtual] - \
                                                          balancoHidricoNormalDF['ARM'][mesAnterior]

            if balancoHidricoNormalDF['P - ETP'][mesAtual] >= 0:
                balancoHidricoNormalDF.loc[mesAtual, 'Etr'] = balancoHidricoNormalDF['ETP'][mesAtual]
            else:
                balancoHidricoNormalDF.loc[mesAtual, 'Etr'] = balancoHidricoNormalDF['prec'][mesAtual] + abs(
                    balancoHidricoNormalDF['Alt'][mesAtual])

            balancoHidricoNormalDF.loc[mesAtual, 'Def'] = balancoHidricoNormalDF['ETP'][mesAtual] - \
                                                          balancoHidricoNormalDF['Etr'][mesAtual]

            if balancoHidricoNormalDF['ARM'][mesAtual] == self.parametros.CAD:
                balancoHidricoNormalDF.loc[mesAtual, 'Exc'] = balancoHidricoNormalDF['P - ETP'][mesAtual] - \
                                                              balancoHidricoNormalDF['Alt'][mesAtual]

        return balancoHidricoNormalDF





                ### Realiza os calculos do balanco hidrico com os dados especificados ###
    def simularBalancoHidrico(self, inicioSimulTuple, inicioPlantioTuple):


        def preSemeio(diaAtual, varDiaAnterior):
            varDiaAtual = VariaveisBalHidrico(self.parametros) # Receber parametros

            # Calcula ETP em funcao de decendios
            varDiaAtual['ETP'] = self.calcularETP(diaAtual)
            varDiaAtual['Hr'] = varDiaAnterior['Hr']
            varDiaAtual['Kc'] = varDiaAnterior['Kc']

            #Calcula escoamento superficial em funcao da agua em excesso que entrou no sistema
            varDiaAtual['Esc'] = self.calcularEsc(diaAtual)
            # Calcula Apport como precipitação + irrigação - escoamento superficial
            varDiaAtual['Apport'] = self.calcularApport(diaAtual, varDiaAtual['Esc'])

            # Calcula evapotranspiracao maxima como mulch vezes a evapotranspiração potencial
            varDiaAtual['Etm'] = self.calcularEps(varDiaAtual['ETP'])
            varDiaAtual['Eps'] = 0
            varDiaAtual['Epc'] = 0

            # St reserva util superficial como o minimo entre valor calculado e tabelado
            varDiaAtual['StRuSurf'] = min(varDiaAnterior['StRuSurf'] + varDiaAtual['Apport'], self.parametros.RUSURF)
            # EVS recebe o minimo entre valor de St Reserva Util e seu valor calculado a partir da evapotranspiracao maxima
            varDiaAtual['Evs'] = min(varDiaAtual['Etm'] * varDiaAtual['StRuSurf']/self.parametros.RUSURF, varDiaAtual['StRuSurf'])
            varDiaAtual['Etr'] = varDiaAtual['Evs'] # Evapotranspiracao REAL eh encontrada por EVS

            # StRu eh ele antigo + apport ou o valor maximo de RU, DR representa a lamina de irrigacao, HUM o maior valor entre StRu e DR
            (varDiaAtual['StRu'], varDiaAtual['Hum'], varDiaAtual['Dr']) = self.rempliRu(varDiaAtual['Apport'], varDiaAnterior['StRu'], varDiaAnterior['Hum'])

            varDiaAtual['StRu'] = max(varDiaAtual['StRu'] - varDiaAtual['Etr'], 0) # Diminuir ETR de StRU
            varDiaAtual['StRuSurf'] = max(varDiaAtual['StRuSurf'] - varDiaAtual['Etr'], 0) # Diminuir ETR de StRU superficial

            # Atualizando valores
            varDiaAtual['Vrad'] = varDiaAnterior['Vrad']
            varDiaAtual['StRur'] = varDiaAnterior['StRur']
            varDiaAtual['StRurMax'] = varDiaAnterior['StRurMax']
            varDiaAtual['TP'] = varDiaAnterior['TP']
            varDiaAtual['EtrEtm'] = 100*varDiaAtual['Etr']/varDiaAtual['Etm'] # ISNA esta feito em porcentagem

            return varDiaAtual

        def fasesFenologicas(diaAtual, varDiaAnterior, inicioPlantio):
            # Inicializa HUM e St RU com valores do estoque, Kc é 1 e o resto comeca em zero
            varDiaAtual = VariaveisBalHidrico(self.parametros)

            ## Agora as outras variaveis sao determinadas pelas funcoes ja vistas
            varDiaAtual['ETP'] = self.calcularETP(diaAtual) # em decendio
            varDiaAtual['Esc'] = self.calcularEsc(diaAtual) # funcao da agua em excesso
            varDiaAtual['Apport'] = self.calcularApport(diaAtual, varDiaAtual['Esc']) # funcao da precipitacao, irrigacao e escoamento
            varDiaAtual['Kc'] = self.calcularKc(diaAtual, inicioPlantio) # Calculado para o dia especifico, com aproximacoes de dados fornecidos
            varDiaAtual['Eps'] = self.calcularEps(varDiaAtual['ETP']) # mulch * ETP atual
            varDiaAtual['Etm'] = varDiaAtual['Eps']

            varDiaAtual['StRuSurf'] = min(varDiaAnterior['StRuSurf'] + varDiaAtual['Apport'], self.parametros.RUSURF)
            varDiaAtual['Evs'] = min(varDiaAtual['Eps'] * varDiaAtual['StRuSurf'] / self.parametros.RUSURF, varDiaAtual['StRuSurf'])
            varDiaAtual['Etr'] = varDiaAtual['Evs']

            (varDiaAtual['StRu'], varDiaAtual['Hum'], varDiaAtual['Dr']) = self.rempliRu(varDiaAtual['Apport'], varDiaAnterior['StRu'],
                                                                                varDiaAnterior['Hum'])

            if diaAtual == inicioPlantio:
                varDiaAtual['Vrad'] = varDiaAnterior['Vrad']
                varDiaAtual['StRurMax'] = varDiaAnterior['StRurMax']
                varDiaAtual['Hr'] = varDiaAnterior['Hr']
                varDiaAtual['Epc'] = 0
                varDiaAtual['TP'] = varDiaAnterior['TP']
                varDiaAtual['StRur'] = varDiaAnterior['StRur']
            else:
                # Vrad eh proporcao de HUM para StRUR máximo sobre o valor tabelado, deltaRUR eh um decimo disso (1 dia do decendio)
                (varDiaAtual['Vrad'], deltaRur) = self.calcularVrad(varDiaAtual['Hum'], varDiaAnterior['StRurMax'])
                varDiaAtual['StRurMax'] = varDiaAnterior['StRurMax'] + deltaRur # Atualiza valor do dia a partir de dados decendiais
                # StRUR eh calculado, mas nao pode ultrapassar StRUR máximo nem StRU
                varDiaAtual['StRur'] = min(varDiaAnterior['StRur'] + varDiaAtual['Apport'] + deltaRur, varDiaAtual['StRurMax'], varDiaAtual['StRu'])
                varDiaAtual['Hr'] = self.calcularHr(varDiaAtual['StRur'], varDiaAtual['StRurMax']) # umidade relativa = StRUR/StRURMaximo

                varDiaAtual['Epc'] = varDiaAtual['Kc']*varDiaAtual['ETP'] # Evapotranspiracao de Cultura (nao leva em conta restricao hidrica)

                (varDiaAtual['Etr'], varDiaAtual['Etm'], varDiaAtual['TP']) = self.calcularEtrEtm(varDiaAtual['Epc'], varDiaAtual['ETP'], varDiaAtual['Hr'], varDiaAtual['Evs'], varDiaAtual['StRur'], varDiaAtual['Etm'])

                varDiaAtual['Eps'] = varDiaAtual['StRurMax'] - varDiaAtual['StRur']
                varDiaAtual['StRur'] = max(varDiaAtual['StRur'] - varDiaAtual['Etr'], 0)

            varDiaAtual['StRuSurf'] = max(varDiaAtual['StRuSurf'] - varDiaAtual['Etr'], 0)
            varDiaAtual['StRu'] = max(varDiaAtual['StRu'] - varDiaAtual['Etr'], 0)
            varDiaAtual['EtrEtm'] = 100 * varDiaAtual['Etr'] / varDiaAtual['Etm']



            return varDiaAtual

        def posColheita(diaAtual, varDiaAnterior):
            varDiaAtual = VariaveisBalHidrico(self.parametros)

            varDiaAtual['ETP'] = self.calcularETP(diaAtual)
            varDiaAtual['Hr'] = 0
            varDiaAtual['Kc'] = 1

            varDiaAtual['Esc'] = self.calcularEsc(diaAtual)
            varDiaAtual['Apport'] = self.calcularApport(diaAtual, varDiaAtual['Esc'])

            varDiaAtual['Etm'] = self.calcularEps(varDiaAtual['ETP'])
            varDiaAtual['Epc'] = 0

            varDiaAtual['StRuSurf'] = min(varDiaAnterior['StRuSurf'] + varDiaAtual['Apport'], self.parametros.RUSURF)
            varDiaAtual['Evs'] = min(varDiaAtual['Etm'] * varDiaAtual['StRuSurf']/ self.parametros.RUSURF, varDiaAtual['StRuSurf'])
            varDiaAtual['Etr'] = varDiaAtual['Evs']

            (varDiaAtual['StRu'], varDiaAtual['Hum'], varDiaAtual['Dr']) = self.rempliRu(varDiaAtual['Apport'],varDiaAnterior['StRu'],
                                                                                varDiaAnterior['Hum'])

            varDiaAtual['StRu'] = max(varDiaAtual['StRu'] - varDiaAtual['Etr'], 0)
            varDiaAtual['StRuSurf'] = max(varDiaAtual['StRuSurf'] - varDiaAtual['Etr'], 0)
            varDiaAtual['Eps'] = 0
            varDiaAtual['Vrad'] = 0
            varDiaAtual['StRur'] = varDiaAnterior['StRur']
            varDiaAtual['StRurMax'] = varDiaAnterior['StRurMax']
            varDiaAtual['TP']= varDiaAnterior['TP']
            varDiaAtual['EtrEtm'] = 100 * varDiaAtual['Etr'] / varDiaAtual['Etm']

            return varDiaAtual



        ## Começo da função balancoHidrico()
        if self.ETPsDecendiais:
            #anos=len(self.parametros.anosDadosHistoricos)
            #for ano in self.parametros.anosDadosHistoricos:
                #anos+=1
                #if ano in self.estacao.dados['data']:
                #    print(self.estacao.dados['data'])
                #else:
                #print(self.estacao.dados)
            #ano=2000 #ano fixo, somente um

            # Para cada ano desejado, faz-se uma simulacao
            #jm = self.dadosMeteorologicos.index(inicioSimulTuple[0])
            #ano=self.dadosMeteorologicos[:][jm].year
            inicioSimul = date(2000, inicioSimulTuple[0], inicioSimulTuple[1])
            inicioPlantio = date(2000, inicioPlantioTuple[0], inicioPlantioTuple[1])
            fimSimul = inicioPlantio

            for fase in self.cultura.fases:
                fimSimul += timedelta(days=fase) # Inicio do plantio + dias que sao fase = Data final do plantio
                #timedelta é uma funcao

            diaColheita = fimSimul - timedelta(days=1)

            # Se a data de inicio esta dentro do desejado
            if inicioSimul >= self.limitesDadosHistoricos[0] and fimSimul <= self.limitesDadosHistoricos[1]:

                diaAtual = inicioSimul # Inicia dia
                #print(diaAtual)
                varDiaAnterior = VariaveisBalHidrico(self.parametros)  # Inicializa variaveis de saida e coloca alguns valores delas

                # self.valoresDiarios[ano] = {}

                while diaAtual < inicioPlantio:
                    # Realiza o pre semeio: reserva util, evapotranspiracao, etc
                    varDiaAtual = preSemeio(diaAtual, varDiaAnterior)
                    # Atualizar variaveis de saida a cada dia calculado
                    self.variaveisSaida = self.variaveisSaida.append(VariaveisSaida(varDiaAtual, index=[diaAtual], columns=self.columns))

                    # self.valoresDiarios[ano][diaAtual] = varDiaAtual
                    diaAtual += timedelta(days=1)
                    varDiaAnterior = varDiaAtual

                fase = 1
                inicioFase = inicioPlantio
                while diaAtual <= diaColheita:
                    # Para todos os dias eh feita :
                    varDiaAtual = fasesFenologicas(diaAtual, varDiaAnterior, inicioPlantio)


                    if diaAtual == inicioFase + timedelta(days=self.cultura.fases[fase - 1]):
                        fase += 1
                        inicioFase = diaAtual

                    varDiaAtual['fase'] = fase

                    self.variaveisSaida = self.variaveisSaida.append(VariaveisSaida(varDiaAtual, index=[diaAtual], columns=self.columns))

                    # self.valoresDiarios[ano][diaAtual] = varDiaAtual
                    diaAtual += timedelta(days=1)
                    varDiaAnterior = varDiaAtual

                while diaAtual < fimSimul:
                    varDiaAtual = posColheita(diaAtual, varDiaAnterior)

                    self.variaveisSaida = self.variaveisSaida.append(VariaveisSaida(varDiaAtual, index=[diaAtual], columns=self.columns))

                    # self.valoresDiarios[ano][diaAtual] = varDiaAtual

                    diaAtual += timedelta(days=1)
                    varDiaAnterior = varDiaAtual



            self.balancoHidricoNormalDF = self.balancoHidricoNormal()


            if not self.variaveisSaida.empty:

                return (pd.concat([self.variaveisSaida, self.dadosMeteorologicos], axis = 1), self.balancoHidricoNormalDF)


        return 'Dados insuficientes'



if __name__ == '__main__':
    parametros = ParamSimul() # Inicializa parametros
    estacao = Estacao()
    #estacao.latitude = -22.8
    cultura = Cultura()
    cultura.carregarDoBD(1) # id do grupo
    print(cultura.fases)

    simulacao = balancoHidrico(estacao, cultura)
    valoresDiarios = simulacao.simularBalancoHidrico(parametros)
    a = 1
