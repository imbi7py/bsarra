# -*- coding: utf-8 -*-
from PyQt5.uic import loadUiType
from mpl_toolkits.basemap import Basemap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
FigureCanvasQTAgg as FigureCanvas,
NavigationToolbar2QT as NavigationToolbar)
import os
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import numpy as np
Ui_MainWindow, QMainWindow = loadUiType('interfaces/sarraqt.ui')

dirculturassimuladas = 'simulacoes/'

def drawstates():
    shapefile='/home/daniel/Desktop/tcc/shapeSP/shapeestado'
    m = Basemap(projection='merc', llcrnrlat=-40, urcrnrlat=5,
    llcrnrlon=-80, urcrnrlon=-20, resolution='l')
    m.fillcontinents()
    m.drawcountries()
    shp = m.readshapefile(shapefile, 'states', drawbounds=True)
    for info, shape in zip(m.states_info, m.states):
        x, y = zip(*shape)
        ax1f1.plot(x, y, marker=None,color='m')
    m.ax = ax1f1


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.cboxCultura.clear()
        self.cboxEstado.clear()
        root, dirs, files = next(os.walk(dirculturassimuladas))
        self.cboxCultura.addItems(dirs)
        self.cboxCultura.currentIndexChanged.connect(self.carregaEstados)
        self.cboxEstado.currentIndexChanged.connect(self.carregaShape)

    def carregaShape(self):
        subprocess.call(('/home/daniel/Desktop/tcc/shapeSP/recorteSP.R',self.cboxEstado.currentText(), self.cboxCultura.currentText()))
        MainWindow.rmmpl()
        drawstates()
        MainWindow.addmpl(fig1)


    def carregaEstados(self):
        self.cboxEstado.clear()
        direstado = dirculturassimuladas + "/" + self.cboxCultura.currentText()
        root, dirs, files = os.walk(direstado).next()
        self.cboxEstado.addItems(dirs)


    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.show()
        #self.toolbar = NavigationToolbar(self.canvas)#, self.mplwindow
        #self.mplvl.addWidget(self.toolbar)

        #self.canvas.mpl_connect('pick_event', self.on_pick)

    def rmmpl(self):
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        fig1.clf()
        #self.mplvl.removeWidget(self.toolbar)
        #self.toolbar.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    MainWindow = MainWindow()
    fig1 = plt.figure()
    ax1f1 = fig1.add_subplot(111)
    #drawstates()
    MainWindow.addmpl(fig1)


    MainWindow.show()
    sys.exit(app.exec_())





#import csv



#with open('municipiosSPtemp.csv','rb') as arqtemp:
#	temperaturas = csv.reader(arqtemp, delimiter=',')
#	w = []
#	for row in temperaturas:
#		w.extend(row)

#print w


#plt.show()
