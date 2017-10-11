import numpy as np


def interpolacaoIDW(pontosConhecidos, valoresConhecidos, xGrid, yGrid, metodo = 'linear', raioDeInfluencia = 1000):
    matrizShape = np.shape(xGrid)
    nPontosConhecidos = len(valoresConhecidos)
    zGrid = np.zeros(shape=matrizShape)

    for i in range(matrizShape[0]):

        dX = np.repeat([xGrid[i, :]], nPontosConhecidos, axis=0) - np.repeat(pontosConhecidos['X'].as_matrix()[:, None],
                                                                             matrizShape[1], axis=1)
        dY = np.repeat([yGrid[i, :]], nPontosConhecidos, axis=0) - np.repeat(pontosConhecidos['Y'].as_matrix()[:, None],
                                                                             matrizShape[1], axis=1)
        distancias = np.sqrt(dX ** 2 + dY ** 2)


        zGrid[i, np.where(distancias == 0)[1]] = valoresConhecidos[np.where(distancias == 0)[0]]



        if metodo == 'quadrado':
            w = 1/(distancias ** 2)
        else:
            w = 1/distancias


        for j in np.where((distancias <= raioDeInfluencia * 1000) & (distancias > 0))[1]:

            w[distancias[:, j] > raioDeInfluencia * 1000, j] = 0

        zGrid[i, :] = np.dot(valoresConhecidos, w) / np.sum(w, axis=0)







    return zGrid