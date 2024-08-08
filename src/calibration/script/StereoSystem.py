# import pyrealsense2 as rs
from __future__ import print_function
import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QThread, pyqtSignal
from collections import Counter
import random
import os 

class CameraThread(QThread): 

    # For Communicating with Main Thread
    imgSignalQt = pyqtSignal('QImage')
    
    def __init__(self, videoPath, outputPath, fusedSensorData): 

        super(CameraThread,self).__init__()

        self.outputPath = outputPath
        self.videoPath = videoPath
        self.fusedSensorData = fusedSensorData
        self.depth = [] #concatenating depth of one salient point, used in filtering noisy data
        self.objectPoints = []#concatenating (x,y,z) of one salient point
        self.terminatFlag = False
        self.startCollectFlag = False
        self.videoShowFlag = False
        self.ID = 0
        self.IDsthreshold = 50
        self.cornerComputFlag = True

    def run(self): 
        self.cap = cv2.VideoCapture(self.videoPath)
        print("[info] Video Captured...")  

        while self.videoShowFlag:
            
            ret, imgBGR = self.cap.read()
            if self.terminatFlag or not ret:
                self.cap.release()
                print("[info] Video Released...")
                break

            # runs only for the first frame
            if self.cornerComputFlag:
                gray = cv2.cvtColor(imgBGR,cv2.COLOR_BGR2GRAY)
                corners = cv2.goodFeaturesToTrack(gray,self.IDsthreshold,0.01,60)
                corners = np.int0(corners)
                for i in corners:
                    cornerX, cornerY = i.ravel() 
                    cv2.circle(imgBGR, (cornerX, cornerY), 15, (0, 0, 255), -1) 
                self.cornerComputFlag = False 

            else:
                
                cornerX, cornerY = corners[self.ID].ravel()
                cv2.circle(imgBGR, (cornerX, cornerY), 15, (0, 0, 255), -1) #draw the obj point on img

                if self.startCollectFlag:
                    # hard code obj point values, synthetic data
                    randomVal = random.uniform(0, 1)
                    self.UpdateObjectPoint([0.5 + randomVal, 0.6 + randomVal, 1. + randomVal]) 
                    filteredObjPoint = self.GetObjectPoint() 
                    self.fusedSensorData.UpdateObjPoints(filteredObjPoint)
                    self.ID += 1
                    self.startCollectFlag = False 

            imgRGB = cv2.cvtColor(imgBGR, cv2.COLOR_BGR2RGB)
            imgQt = QImage(imgRGB.data, imgRGB.shape[1], imgRGB.shape[0], QImage.Format_RGB888)
            imgQt.scaledToWidth (640,QtCore.Qt.SmoothTransformation)
            imgQt.scaledToHeight(480,QtCore.Qt.SmoothTransformation)
            imgQtScaled = imgQt.scaled(640, 480, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.imgSignalQt.emit(imgQtScaled)

    def StartVideoCapture(self):
        self.videoShowFlag = True

    def Collect(self):
        self.startCollectFlag = True
        
    def UpdateObjectPoint(self,objPoint):
        
        self.depth.append(objPoint[2]) #concatenate depth value
        self.objectPoints.append(objPoint)

    def GetObjectPoint(self): 
        '''
        return xyz point, the most occurred value (mode). 
        Then flush the lists
        '''
        objectPoint = self.FindMode2Filter() # filtering the noisy data

        filename = "objPoint" + str(self.ID) + ".txt"
        savedPath = os.path.join(self.outputPath, filename)

        with open(savedPath, 'w') as fileHandler:
            for index, item in enumerate(self.objectPoints):
                fileHandler.write("{}. {}\n\n".format(index + 1, item))

        self.depth = [] 
        self.objectPoints = [] 
        return objectPoint

    def FindMode2Filter(self):
        tmp = Counter(self.depth)
        mode_element = tmp.most_common()[0][0]
        if mode_element == 0 and len(tmp.most_common()) >1: 
            mode_element = tmp.most_common()[1][0]
        index_mode   = self.depth.index(mode_element)
        return self.objectPoints[index_mode]

    def Terminate(self):
        self.terminatFlag = True
        self.cap.release()