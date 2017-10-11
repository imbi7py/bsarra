import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QMainWindow, QApplication, QDockWidget
from PyQt5.Qt import Qt


class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent) # Inicializa janela

        self.figure = plt.figure(figsize=(10,6)) # Define figura e seu tamanho
        # Caracteristicas do mapa
        m = Basemap(resolution='i',  # c, l, i, h, f or None
                    projection='merc',
                    lat_0=-22.525, lon_0=-48.865,
                    llcrnrlon=-53.25, llcrnrlat=-25.1, urcrnrlon=-44.48, urcrnrlat=-19.5)

        m.drawmapboundary(fill_color='aqua') # Contorno
        m.fillcontinents(color='gray', lake_color='aqua') # Continente
        m.drawcoastlines() # Costa

        m.readshapefile('SP_Municipios/Sao_Paulo_Municipios', 'Sao_Paulo_Municipios')

        self.canvas = FigureCanvas(self.figure)

        self.setCentralWidget(self.canvas)



        simulParamDockWidget = QDockWidget('Simulação', self)
        simulParamDockWidget.setObjectName('simulParamDockWidget')
        simulParamDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|
                                             Qt.RightDockWidgetArea)
        simulParamDockWidget.setFeatures(QDockWidget.DockWidgetFloatable |
                                         QDockWidget.DockWidgetMovable)

app = QApplication(sys.argv)
form = MainWindow()
form.show()
app.exec_()
