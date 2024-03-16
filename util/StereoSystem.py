
import socket                
import pickle
import time
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2
import numpy as np
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

# this class has its own thread
class CameraThread(QThread): #Inheriting QThread
    # create a signal for displaying image
    imageSignal = pyqtSignal('QImage')
    # create a signal to show the end of calibration process
    terminationSignal = pyqtSignal([int])
    
    def __init__(self, mutex, condition):
        super().__init__()
        self.mutex = mutex
        self.condition = condition
        self.Stop = False
        self.compute_salients = True
        self.ID_salient = 0
    
    #overriding QThread function run() function
    def run(self): 
        self.cap = cv2.VideoCapture(0)
        print("[info] Video Captured...")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        try:
            while True:
                
                if self.Stop:
                    self.cap.release()
                    print("[info] Video Released...")
                    break
                    
                ret, img_rgb = self.cap.read()
                if ret:
                    if self.compute_salients:
                        gray = cv2.cvtColor(img_rgb,cv2.COLOR_BGR2GRAY)
                        corners = cv2.goodFeaturesToTrack(gray,20,0.01,10)
                        corners = np.int0(corners)
                        for i in corners:
                            x,y = i.ravel()
                            cv2.circle(img_rgb,(x,y),3,255,-1)

                    else:
                        
                        #maximum number of salient points reached 19
                        # so terminate calibration process
                        if self.ID_salient > 19:
                            
                            print("[info] Calibration done...")
                            self.terminationSignal.emit(-1)
                            self.terminate()
                            break

                        x,y = corners[self.ID_salient].ravel()
                        cv2.circle(img_rgb,(x,y),3,255,-1)
                        
                    rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
                    convert = QImage(rgb.data, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
                    self.imageSignal.emit(convert) # send image signal for display
                    self.condition.wait(self.mutex)# # unlock the mutex to display image
                    
        except:
            print('[info] error from CamThread')
    
    # return XYZ world coordinate system
    def GetXYZ(self): 
        #not implemented for the sake of simplicity
        
    def update(self,ID):
        print("Salinet Point update:{}".format(ID))
        self.ID_salient = ID
    
    def StartCalibration(self):
        self.compute_salients = False
        
    def Terminate(self):
        self.Stop = True
        self.cap.release()
        print("[info] Video Released...")



        
        
        
