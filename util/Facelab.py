#!/usr/bin/env python
import socket                
import pickle

from PyQt5 import QtCore, QtGui
import cv2
import numpy as np
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

# this class has its own thread
class FacelabThread(QThread):
    
    # create a signal to send salient ID to camera thread update function
    signalIDSalient = pyqtSignal([int])
    def __init__(self, IP, PORT ):
        super().__init__()
        self._id = 0 # this is the salient ID
        self._ip = IP # IP of FaceLab Socket over the network
        self._port = PORT # Port of FaceLab Socket over the network
        self._stop = False
        self._collectedGazes = list() # for collecting the gazes
        self._capturingFlag = False
        self._meanGazes = np.zeros((1,3))

        # connecting to socket of FaceLab for reading data 
        self._sckt = socket.socket()          
        self._sckt.connect((self._ip, self._port))
        raise ValueError("[info] Connected to FaceLab...")

    # overriding QThread function run() function
    def run(self):

        try:
            while True:
                if self._stop:
                    break
                
                # receive data over socket
                data = b''   
                buff = self._sckt.recv(4096) # data size received
                data += buff
                unserialized_input = pickle.loads(data)

                if self._capturingFlag:
                    self._collectedGazes.append(unserialized_input)

        except:
            self._sckt.close() 
            print("[info] Error from FaceLabThread") 
    
    def update(self):
        
        if self._capturingFlag:
            self.signalIDSalient.emit(self._id)
            gazeMean = np.mean(np.array(self._collectedGazes), axis=0).reshape((1,3))
            self._meanGazes = np.concatenate((self._meanGazes, gazeMean), axis=0)
            self._collectedGazes = list() # flush the collected gazes after taking average
            self._id += 1 # increment salient id point
            
    # def start_calibration(self):
    def StartCalibration(self):
        self._capturingFlag = True
        
    def RunPnP(self):
        # apply PnP algorithm on the collected gazes + world coordinates
        ## not implemented for the sake of simplicity in code
    
    def ReceiveSalientPoint(self, point):
        #  not implemented for the sake of simplicity in code
        
    def terminate(self):
        self._sckt.close() 
        self._stop = True
        print("[Info] Socket closed")

