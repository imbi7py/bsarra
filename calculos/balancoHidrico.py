from datetime import date, timedelta

import numpy as np
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
    def __init__(self, cultura):

        self.cultura = cultura
        self.ETPsDecendiais = {}
        # self.valoresDiarios = {}
        self.columns = ['ETP', 'Esc', 'Apport', 'Kc', 'Evs', 'Hum', 'Dr', 'Vrad',
                        'StRurMax', 'Hr', 'Epc', 'Etr', 'Etm', 'Eps', 'StRur', 'StRuSurf',
                        'StRu', 'TP', 'EtrEtm', 'fase']
        # self.variaveisSaida = VariaveisSaida(columns=self.columns)
        self.variaveisSaida = pd.DataFrame(columns=self.columns)


    def lerDadosMeteorologicos(self, estacao, parametros, dados = 'agritempo'):
        self.parametros = parametros

        self.estacao = estacao

        self.parametros.RESERVAUTIL = self.cultura.reservaUtilSolo[self.parametros.tipoSolo - 1]
        self.parametros.PROFMAXIMA = self.parametros.RESERVAUTIL * 1000/self.parametros.CAD

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
        decendio = calculosDecendiais.converterToDataDecendio(dia)
        decendioFuturo = calculosDecendiais.proximoDecendio(decendio)
        etpAtual = self.ETPsDecendiais[decendio]
        etpFuturo = self.ETPsDecendiais[decendioFuturo]

        return (etpAtual + (etpFuturo - etpAtual) * ((dia - calculosDecendiais.inicioDecendio(dia)).days) / calculosDecendiais.diasNoDecendio(dia)) / 10



    def calcularEsc(self, diaAtual):
        enplus = self.dadosMeteorologicos['prec'][diaAtual] + self.dadosMeteorologicos['irrigacao'][diaAtual]
        esc = 0

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

        if StRu > self.parametros.RESERVAUTIL:
            Dr = StRu - self.parametros.RESERVAUTIL
            StRu = self.parametros.RESERVAUTIL

        Hum = max(Hum, StRu)
        return (StRu, Hum, Dr)

    def calcularKc(self, diaAtual, inicioPlantio):
        decendioAtual = (((diaAtual - inicioPlantio).days) // 10) + 1
        nDias = (diaAtual - inicioPlantio - timedelta((decendioAtual - 1) * 10)).days

        if decendioAtual - 1 < len(self.cultura.kc):
            kcAtual = self.cultura.kc[decendioAtual - 1]
        else:
            kcAtual = 1

        if decendioAtual < len(self.cultura.kc):
            kcProx = self.cultura.kc[decendioAtual]
        else:
            kcProx = 1

        return kcAtual + (kcProx - kcAtual)*nDias / calculosDecendiais.diasNoDecendio(diaAtual)

    def calcularVrad(self, Hum, StRurMax):
        vRad = 100*(Hum - StRurMax)/self.parametros.RESERVAUTIL
        deltaRur = min(Hum - StRurMax, vRad/1000*self.parametros.RESERVAUTIL)

        return vRad, deltaRur

    def calcularHr(self, StRur, StRurMax):
        Hr = 0

        if StRurMax > 0:
            Hr = StRur/StRurMax

        return Hr

    def calcularEtrEtm(self, Epc, ETP, Hr, Evs, StRur, Etm):
        Etr = Epc * (( -0.05 + 0.732/ETP) + (4.97 - 0.66*ETP) * Hr + (-8.57 + 1.56*ETP)*Hr*Hr + (4.35 - 0.88*ETP)*Hr*Hr*Hr)
        TP = Etr

        if Etr > Evs:
            Etm = Epc
            Etr = min(Etr, Etm)
            Etr = max(Etr, 0)
            Etr = min(StRur, Etr)
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
            varDiaAtual = VariaveisBalHidrico(self.parametros)

            varDiaAtual['ETP'] = self.calcularETP(diaAtual)
            varDiaAtual['Hr'] = varDiaAnterior['Hr']
            varDiaAtual['Kc'] = varDiaAnterior['Kc']

            varDiaAtual['Esc'] = self.calcularEsc(diaAtual)
            varDiaAtual['Apport'] = self.calcularApport(diaAtual, varDiaAtual['Esc'])

            varDiaAtual['Etm'] = self.calcularEps(varDiaAtual['ETP'])
            varDiaAtual['Eps'] = 0
            varDiaAtual['Epc'] = 0

            varDiaAtual['StRuSurf'] = min(varDiaAnterior['StRuSurf'] + varDiaAtual['Apport'], self.parametros.RUSURF)
            varDiaAtual['Evs'] = min(varDiaAtual['Etm'] * varDiaAtual['StRuSurf']/self.parametros.RUSURF, varDiaAtual['StRuSurf'])
            varDiaAtual['Etr'] = varDiaAtual['Evs']

            (varDiaAtual['StRu'], varDiaAtual['Hum'], varDiaAtual['Dr']) = self.rempliRu(varDiaAtual['Apport'], varDiaAnterior['StRu'], varDiaAnterior['Hum'])

            varDiaAtual['StRu'] = max(varDiaAtual['StRu'] - varDiaAtual['Etr'], 0)
            varDiaAtual['StRuSurf'] = max(varDiaAtual['StRuSurf'] - varDiaAtual['Etr'], 0)

            varDiaAtual['Vrad'] = varDiaAnterior['Vrad']
            varDiaAtual['StRur'] = varDiaAnterior['StRur']
            varDiaAtual['StRurMax'] = varDiaAnterior['StRurMax']
            varDiaAtual['TP'] = varDiaAnterior['TP']
            varDiaAtual['EtrEtm'] = 100*varDiaAtual['Etr']/varDiaAtual['Etm']

            return varDiaAtual

        def fasesFenologicas(diaAtual, varDiaAnterior, inicioPlantio):
            varDiaAtual = VariaveisBalHidrico(self.parametros)

            varDiaAtual['ETP'] = self.calcularETP(diaAtual)

            varDiaAtual['Esc'] = self.calcularEsc(diaAtual)
            varDiaAtual['Apport'] = self.calcularApport(diaAtual, varDiaAtual['Esc'])

            varDiaAtual['Kc'] = self.calcularKc(diaAtual, inicioPlantio)
            varDiaAtual['Eps'] = self.calcularEps(varDiaAtual['ETP'])
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
                (varDiaAtual['Vrad'], deltaRur) = self.calcularVrad(varDiaAtual['Hum'], varDiaAnterior['StRurMax'])
                varDiaAtual['StRurMax'] = varDiaAnterior['StRurMax'] + deltaRur
                varDiaAtual['StRur'] = min(varDiaAnterior['StRur'] + varDiaAtual['Apport'] + deltaRur, varDiaAtual['StRurMax'], varDiaAtual['StRu'])
                varDiaAtual['Hr'] = self.calcularHr(varDiaAtual['StRur'], varDiaAtual['StRurMax'])

                varDiaAtual['Epc'] = varDiaAtual['Kc']*varDiaAtual['ETP']

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

            for ano in self.parametros.anosDadosHistoricos:

                inicioSimul = date(ano, inicioSimulTuple[0], inicioSimulTuple[1])
                inicioPlantio = date(ano, inicioPlantioTuple[0], inicioPlantioTuple[1])
                fimSimul = inicioPlantio

                for fase in self.cultura.fases:
                    fimSimul += timedelta(days=fase)

                diaColheita = fimSimul - timedelta(days=1)

                if inicioSimul >= self.limitesDadosHistoricos[0] and fimSimul <= self.limitesDadosHistoricos[1]:

                    diaAtual = inicioSimul

                    varDiaAnterior = VariaveisBalHidrico(self.parametros)

                    # self.valoresDiarios[ano] = {}

                    while diaAtual < inicioPlantio:
                        varDiaAtual = preSemeio(diaAtual, varDiaAnterior)

                        self.variaveisSaida = self.variaveisSaida.append(VariaveisSaida(varDiaAtual, index=[diaAtual], columns=self.columns))

                        # self.valoresDiarios[ano][diaAtual] = varDiaAtual
                        diaAtual += timedelta(days=1)
                        varDiaAnterior = varDiaAtual



                    fase = 1
                    inicioFase = inicioPlantio
                    while diaAtual <= diaColheita:
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
    parametros = ParamSimul()
    estacao = Estacao()
    estacao.latitude = -22.8
    cultura = Cultura()
    cultura.carregarDoBD(1)

    simulacao = balancoHidrico(estacao, cultura)
    valoresDiarios = simulacao.simularBalancoHidrico(parametros)
    a = 1
