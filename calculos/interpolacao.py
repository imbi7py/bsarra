import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile
from mpl_toolkits.basemap import Basemap
from calculos.interpolacaoIDW import interpolacaoIDW


def interpolar(estado, latitudesConhecidas, valoresConhecidos, labels, resolucao = 20000):


    valoresConhecidos = valoresConhecidos.as_matrix()

    ### Pegar shapefiles ###
    conn = sqlite3.connect('../sarra.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM estado
    WHERE sigla = ?''', (estado,))

    for linha in cursor.fetchall():
        estadoNome = linha[1]
        estadoShapeFile = linha[2]


    #### Mapa #####
    fig = plt.figure(figsize=(9, 6))
    sf = shapefile.Reader('../'+estadoShapeFile)
    m = Basemap(resolution='i',  # c, l, i, h, f or None
                projection='merc',
                llcrnrlon=sf.bbox[0], llcrnrlat=sf.bbox[1], urcrnrlon=sf.bbox[2], urcrnrlat=sf.bbox[3])

    ### Interpolação ####
    minX = 0
    minY = 0
    maxX, maxY = m(m.urcrnrlon, m.urcrnrlat)

    xGrid, yGrid = np.meshgrid(np.arange(minX, maxX + resolucao, resolucao), np.arange(minY, maxY + resolucao, resolucao))

    pontosConhecidos = pd.DataFrame(columns=['X', 'Y'])

    for indice in latitudesConhecidas.index:
        ponto = m(latitudesConhecidas['longitude'][indice], latitudesConhecidas['latitude'][indice])
        pontosConhecidos = pontosConhecidos.append({'X': ponto[0], 'Y': ponto[1]},ignore_index=True)

    # zGrid2 = griddata(pontosConhecidos, valoresConhecidos, (xGrid, yGrid), method='nearest')
    zGrid4 = interpolacaoIDW(pontosConhecidos, valoresConhecidos, xGrid, yGrid, metodo='linear', raioDeInfluencia=150)



    #### Plotar dados #####
    # m.fillcontinents(color='gray', lake_color='aqua', zorder=4)
    # m.drawmapboundary(fill_color='aqua', zorder=3)

    m.drawcoastlines()
    # for shape_rec in sf.shapeRecords():
    #     vertices = []
    #     codes = []
    #     pts = shape_rec.shape.points
    #     prt = list(shape_rec.shape.parts) + [len(pts)]
    #     for i in range(len(prt) - 1):
    #         for j in range(prt[i], prt[i + 1]):
    #             vertices.append((pts[j][0], pts[j][1]))
    #         codes += [Path.MOVETO]
    #         codes += [Path.LINETO] * (prt[i + 1] - prt[i] - 2)
    #         codes += [Path.CLOSEPOLY]
    #     clip = Path(vertices, codes)
    #     # clip = PathPatch(clip, transform = ax.transData)
    #     clip = PathPatch(clip)


    m.readshapefile('../' +estadoShapeFile, 'municipios')


    # clevs = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    clevs = [30, 40, 45, 55, 60, 70, 80, 90, 100]
    # clevs = [693,990,1140,1230,1315,1390,1520,1865]
    # clevs = [0, 45, 55, 100]
    cs = m.contourf(xGrid, yGrid, zGrid4, clevs, cmap=plt.cm.RdYlBu)
    # for contour in cs.collections:
    #     contour.set_clip_path(clip)
    m.scatter(pontosConhecidos['X'], pontosConhecidos['Y'],3, color = 'k',picker = True )
    m.colorbar(cs, location = 'bottom', pad = "5%")



    def pickEstacao(event):
        ind = event.ind
        # print(labels[ind][0])
        print(labels.iloc[ind])

    fig.canvas.mpl_connect('pick_event', pickEstacao)
    plt.show()

if __name__ == '__main__':
    estado = 'MG'

    variavel = 'EtrEtm'
    # mediasDF = pd.read_csv('simulacoes/Algodão/' + estado + '/EtrEtmmedias.csv',index_col=0)
    mediasDF = pd.read_csv('../simulacoes/Milho/' + estado + '/1-1/' + variavel + 'medias.csv', index_col=0)


    mediasDF = mediasDF.dropna()
    interpolar(estado, mediasDF[['latitude', 'longitude']], mediasDF[variavel], mediasDF[variavel])

