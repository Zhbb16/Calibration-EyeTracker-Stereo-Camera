#!/usr/bin/env python
from __future__ import print_function
import socket                
import time
import numpy as np
from PyQt5.QtCore import QThread
from ctypes import *
import numpy as np
import os 

# for decoding the socket buffer
class GazeData(Structure):
    _fields_ = [("gazeVector_x", c_float),
                ("gazeVector_y", c_float),
                ("gazeVector_z", c_float)]

class FacelabThread(QThread):

    def __init__(self, IP, PORT, OUTPUTPATH, fusedSensorData):

        super(FacelabThread,self).__init__()

        self.outputPath = OUTPUTPATH
        self.fusedSensorData = fusedSensorData
        self.terminateFlag = False
        self.gazeData = []
        self.collectionFlag = False
        self.readingSocketFlag = False
        self.ID = 0

        try:
            self.socket = socket.socket()          
            self.socket.connect((IP, PORT))
            print("[INFO] Connected to FaceLab Server on Port: {}".format(PORT))
        except:
            print("[INFO] FaceLab server not found...".format(PORT))
            
    def run(self):

        while self.readingSocketFlag:

            if self.terminateFlag:
                print("[INFO] FaceLab data collection is terminated..") 
                self.socket.close() 
                break

            buff = self.socket.recv(sizeof(GazeData))
            GazeData_in = GazeData.from_buffer_copy(buff)
            gazeData = np.array([GazeData_in.gazeVector_x, GazeData_in.gazeVector_y, GazeData_in.gazeVector_z],dtype=np.float32)

            if self.collectionFlag:
                self.UpdateGazeData(gazeData)
                filteredGazeData = self.GetGazeData()
                self.fusedSensorData.UpdateGazeVector(filteredGazeData)
                self.ID += 1
                self.collectionFlag = False

            time.sleep(0.1)

    # this function runs when GUI Start button pushed
    def StartReadingSocket(self):
        self.readingSocketFlag = True

    # this function runs when GUI Stop button pushed
    def Terminate(self):
        self.terminateFlag = True

    def Collect(self):
        self.collectionFlag = True

    def UpdateGazeData(self, gazeData):
        self.gazeData.append(gazeData)

    def GetGazeData(self):
        gazeMedian = np.median(np.array(self.gazeData), axis=0)
        self.SaveGazeData(gazeMedian)
        return gazeMedian.tolist()
    
    def SaveGazeData(self, gazeData):
        fileName = "GazeData" + str(self.ID) + ".out"
        savePath = os.path.join(self.outputPath, fileName)
        np.savetxt(savePath, gazeData, delimiter=',',  fmt='%1.3f')