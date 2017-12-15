import sqlite3
import csv
import datetime
import numpy
import pandas as pd
import functools
def reduce_concat(x, sep=""):
    return functools.reduce(lambda x, y: str(x) + sep + str(y), x)

def paste(*lists, sep=" ", collapse=None):
    result = map(lambda x: reduce_concat(x, sep=sep), zip(*lists))
    if collapse is not None:
        return reduce_concat(result, sep=collapse)
    return list(result)


class Cidade():
    def __init__(self, cursorSQL = None, dados = 'agritempo'):
        #Colunas existentes nos dados de estacao
        self.keys = ['data', 'tmin', 'tminEst', 'tmed', 'tmedEst',
                'tmax', 'tmaxEst', 'urMin', 'urMinEst',
                'urMax', 'urMaxEst', 'prec', 'precEst']

        self.usedKeys = [3, 11]
        self.numericalKeys = [1, 3, 5, 7, 9, 11]

        self.codigo = cursorSQL[0]
        self.nome = cursorSQL[1]
        self.latitude = cursorSQL[2]
        self.longitude = cursorSQL[3]

#conn = sqlite3.connect('sarra.db') # Carregando banco de dados
#cursor = conn.cursor()
#estado='MG'
#cursor.execute('''
#SELECT estacao.codigo, estacao.nome, estacao.latitude, estacao.longitude,
#estacao.altitude, estacao.municipio, municipio.nome, municipio.estado, estado.nome, estacao.dados
#FROM estacao, municipio, estado
#WHERE municipio.codigo = estacao.municipio AND municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))

#com = sqlite3.connect('testando.db')
#cur = com.cursor()
#cur.execute("CREATE TABLE carros(id INT, nome TEXT)")
#cur.execute("INSERT INTO carros VALUES(1, 'Audi')")
#cur.execute('''SELECT * FROM carros''')
#print(cur.fetchall())

### TRATAR BANCO DE DADOS HADGEM
#Abrir banco de dados sarra.db
## Fazer lista de latitudes e longitudes -> for lat in dados['Lat'] for long in dados['Long']
#Encontrar codigo correspondente -> para 'latitude'=lat e 'longitude'=long (talvez considerar so primeira casa decimal)
#Para todos os dados com 'Lat'=lat e 'Long'=long, concatenar no dataframe
#Exportar dataframe para excel com referencia "dados/hadgem/~codigo"

#local_old = "C:/Users/minmedeiros/Documents/analise_dados/"
local_old = "/home/danielbarbosa/ZonCep_novo/novoSarra/"
local_new = "/home/danielbarbosa/ZonCep_novo/novoSarra/hadgem/"
#local_new = "C:/Users/minmedeiros/Documents/novoSarra/dados/hadgem/"
#local_header = "C:/Users/minmedeiros/Documents/analise_dados"

#estacoes = list.files(path="/home/daniel/Desktop/SP/", recursive=FALSE)

conn = sqlite3.connect('sarra.db')
cursor = conn.cursor()

dados = 'hadgem'
cursor.execute('''
        SELECT municipio.codigo, municipio.nome, municipio.latitude, municipio.longitude
        FROM municipio, estado''')

cidades = []

for linha in cursor.fetchall():
    cidades.append(Cidade(cursorSQL=linha, dados = 'hadgem')) # Junta tabelas

colnames = ["data", "tMin", "tMin Estimada", "tMed", "tMed Estimada", "tMax", "tMax Estimada", "urMin", "urMin Estimada", "urMax", "urMax Estimada", "precipitacao", "precipitacao Estimada"]


#chunk_size = 10**5
#tmin = pd.concat([chunk for chunk in pd.read_csv(local_old + 'MNTP_Diario_1961_1990.txt', chunksize=1000)],
               #ignore_index=False)
#tmin.info()

tmin = pd.read_table(local_old + 'MNTP_Diario_1961_1990.txt', sep=' ', header=1)
tmin.columns = ['data','lat','long','tMin']
tmax = pd.read_table(local_old + 'MXTP_Diario_1961_1990.txt', sep=' ', header=1)
tmax.columns = ['data','lat','long','tMax']
prec = pd.read_table(local_old + 'PREC_Diario_1961_1990.txt', sep=' ', header=1)
prec.columns = ['data','lat','long','prec']


print(len(cidades))
#print(tmin['data'][[2,3]])

for est in cidades:
    #print(prec['lat'])
    idxlat = list(numpy.where(prec['lat'] == round(est.latitude,1))[0])
    idxlat += list(numpy.where(prec['lat'] == round(est.latitude+0.1, 1))[0])
    idxlat += list(numpy.where(prec['lat'] == round(est.latitude-0.1, 1))[0])
    idxlong = list(numpy.where(prec['long'] == round(est.longitude,1))[0])
    idxlong += list(numpy.where(prec['long'] == round(est.longitude+0.1, 1))[0])
    idxlong += list(numpy.where(prec['long'] == round(est.longitude-0.1, 1))[0])
    #print(numpy.where(tmin['lat'] == est.latitude)) #.tolist())
    idx = []
    if (len(idxlat)>2) and (len(idxlong)>2):
        #print(idxlat)
        for x in idxlat:
            if (x in idxlong) and not (prec['data'][x] in list(prec['data'][idx])):
                idx.append(x)
                #print('foi')
                #print(x)

    #tmax = pd.read_table(local_old + '/MXTP_Diario_1961_1990.txt', delim_whitespace=True, names=('Data', 'Lat', 'Long', 'MXTP'))
    #prec = pd.read_table(local_old + '/PREC_Diario_1961_1990.txt', delim_whitespace=True, names=('Data', 'Lat', 'Long', 'PREC'))
    estimada=[]
    if len(idx)>=1:
        for i in range(len(idx)):
            estimada.append("não")
        #print(estimada)
        zero = list(numpy.zeros(len(idx)))
        #print(idx)
        #print(tmin['data'][idx])
        df = pd.DataFrame(data=[list(prec['data'][idx]), list(tmin['tMin'][idx]), estimada, zero, estimada, list(tmax['tMax'][idx]), estimada, zero, estimada, zero, estimada, list(prec['prec'][idx]), estimada], index=["data","tMin","tMin Estimada","tMed","tMed Estimada","tMax","tMax Estimada","urMin","urMin Estimada","urMax","urMax Estimada","precipitacao","precipitacao Estimada"]).T
        df.to_csv(path_or_buf=local_new + str(est.codigo) + '.csv', sep='\t')
        print(cidades.index(est))
