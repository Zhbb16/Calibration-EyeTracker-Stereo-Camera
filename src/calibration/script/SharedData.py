from PyQt5 import QtCore
import time

class FusedSensorsData:

    def __init__(self):
        self.gazeVectors = [] 
        self.objPoints = [] 
        self.mutex = QtCore.QMutex()
        self.condition = QtCore.QWaitCondition() 
        self.syncFlag = False 

    # this thread executes by eyeTracker thread
    def UpdateGazeVector(self, gazeVector):

        with QtCore.QMutexLocker(self.mutex): 
            timeStamp = time.time()
            self.gazeVectors.append(gazeVector)
            self.syncFlag = True
            self.condition.wakeAll()
        
        #mutex unlock
        print("[INFO] Thread eyeTracker: collected gazeData= {} / {} / {} at timeStamp {}".format(gazeVector[0], gazeVector[1], gazeVector[2], timeStamp))

    # executes by Camera thread
    def UpdateObjPoints(self, objPoint):
        
        with QtCore.QMutexLocker(self.mutex): 

            while not self.syncFlag:
                self.condition.wait(self.mutex) 

            timeStamp = time.time()
            self.objPoints.append(objPoint) 
            self.syncFlag = False
        
        print("[INFO] Thread Camera: collected objectPoint= {} / {} / {}  at {}".format(objPoint[0], objPoint[1], objPoint[2], timeStamp))

    def GetGazeVector(self):
        assert len(self.gazeVectors) == len(self.objPoints)
        return self.gazeVectors
    
    def GetObjectPoint(self):
        assert len(self.gazeVectors) == len(self.objPoints)
        return self.objPoints

