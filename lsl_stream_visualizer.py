# /usr/bin/python3
import os
import sys
import time
import numpy as np
import pickle
from collections import deque
from multiprocessing import Process, Queue, Manager
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QVBoxLayout

from PyQt5.QtGui import *

import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients
from pyqtgraph.opengl import GLViewWidget

from utils import dataReaderLSL, dataReaderTCP, dataReaderLSLWithChannelInfo, dataReaderLSLChunk

import argparse

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

timeFactor = 10000

class Plot2DViewer(object):

    def __init__(self, box, boxLayout, bufferSize = 500, maxChannelNum = 50, streamName=""):
        self.bufferSize = bufferSize
        self.channelNum = maxChannelNum
        self.box = box
        self.boxLayout = boxLayout

        self.setupUi()

        self.streamName = streamName
        self.queue = Queue()
        self.dataReaderProcess = None
        self.channelLabels = Manager().list()
        self.connect()


    def setupUi(self):
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        
        self._dynamic_ax = self.dynamic_canvas.figure.subplots()
        self.x = np.linspace(1, self.bufferSize, self.bufferSize)
        self.y = np.zeros((self.channelNum, self.bufferSize))
        self._dynamic_ax.plot(self.x, self.y[0, :])
        self._dynamic_ax.figure.canvas.draw()

        self.plotToolBar = NavigationToolbar(self.dynamic_canvas, self.box)
        self.boxLayout.addWidget(self.dynamic_canvas)
        self.boxLayout.addWidget(self.plotToolBar)


    def connect(self):
        self.dataReaderProcess = Process(target=dataReaderLSLWithChannelInfo, args=(self.streamName, self.queue, self.channelLabels))

        self.dynamic_canvas.timerEvent = self.update
        self.dynamic_canvas.startTimer(0.000001)
        self.dataReaderProcess.daemon = True
        self.dataReaderProcess.start()

    def update(self, event):
        try:
            if self.channelNum != len(list(self.channelLabels)):
                self.channelNum = len(list(self.channelLabels))
            self._dynamic_ax.clear()
            qs = self.queue.qsize()
            if qs > 0 and self.channelNum > 0:
                if qs <= self.bufferSize:
                    self.y[0:self.channelNum, 0:self.bufferSize-qs] = self.y[0:self.channelNum, -self.bufferSize+qs:]

                else:
                    for k in range(qs - self.bufferSize):
                        self.queue.get()
                    qs = self.bufferSize

                for k in range(self.bufferSize-qs, self.bufferSize):
                    s = self.queue.get()
                    self.y[0:self.channelNum, k] = s

                for i in range(self.channelNum):
                    a = self.y[i, :]
                    d = 2.*(a - np.min(a))/np.ptp(a)-1
                    self._dynamic_ax.plot(self.x, d - 2 * i, 'k')

                self._dynamic_ax.set_xlim([1, self.bufferSize])
                self._dynamic_ax.set_ylim([-2 * self.channelNum + 1, 1])
                self._dynamic_ax.set_yticks(range(-2 * self.channelNum + 2, 2, 2))
                self._dynamic_ax.set_yticklabels(list(self.channelLabels)[::-1])
                self._dynamic_ax.figure.canvas.draw()
            
        except Exception as e:
            print(traceback.format_exc())


    def disconnect(self):
        try:
            self.dataReaderProcess.terminate()
        except Exception as e:
            print(e)

    def __del__(self):
        try:
            self.dataReaderProcess.terminate()
            print("Data reader process terminated.")
        except Exception as e:
            print(e)


def main(streams, W):
    Max_Stream_Num = 4
    
    appQt = QtWidgets.QApplication(streams)
    MainWindow = QtWidgets.QMainWindow()
    MainWidget = QtWidgets.QWidget(MainWindow)
    layout = QGridLayout()

    Plot2DViewerList = []

    for i in range(min(len(streams), Max_Stream_Num)):
        stream = streams[i]
        tmpBox = QGroupBox(stream)
        tmpPlotBoxLayout = QVBoxLayout()
        tmpBox.setLayout(tmpPlotBoxLayout)
        layout.addWidget(tmpBox, 1 + i / 2, 1 + i % 2, 1, 1)
        tmpPlot2DViewer = Plot2DViewer(tmpBox, tmpPlotBoxLayout, W, streamName=stream)
        Plot2DViewerList.append(tmpPlot2DViewer)

    MainWidget.setLayout(layout)
    MainWindow.setCentralWidget(MainWidget)
    MainWindow.setObjectName("MainWindow")
    MainWindow.resize(800, 800)

    QtCore.QMetaObject.connectSlotsByName(MainWindow)
    MainWindow.show()

    try:
        appQt.exec_()
    except Exception as e:
            print(e)
    finally:
        print('finish')
        for tmpPlot2DViewer in Plot2DViewerList:
            del tmpPlot2DViewer


if __name__ == "__main__":
    W = 500

    parser = argparse.ArgumentParser(description='Visualize the LSL stream.')
    parser.add_argument('streams', metavar='strean_names', type=str, nargs='+',
                        help='Stream names to show. For example: python lsl_stream_visualizer.py Quick-30 HeartyPatch')
    parser.add_argument('-w', metavar='window_size', type=int, nargs='?',
                        help='Buffer window size. Default: 500.')

    args = parser.parse_args()
 
    if args.w != None:
        W = args.w

    sys.exit(main(args.streams, W))
