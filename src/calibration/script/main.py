#!/usr/bin/env python

#///////////////////////////////////////////////////////////////////////////
#////////                                                           ////////              
#////////                                                           ////////              
#////////                    Zahra Habibi                           ////////              
#////////       PyQt GUI interface used for calibration             ////////              
#//////// between Face Lab eye-tracker and Intel Real-Sense Cameras ////////             
#////////                using PnP OpenCV algorithm                 ////////               
#////////                                                           ////////              
#////////                                                           ////////   
#////////                      2024-03-11                           ////////            
#////////                                                           ////////             
#///////////////////////////////////////////////////////////////////////////

import roslib
import rospy
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from Facelab import FacelabThread
from StereoSystem import CameraThread
from PnP import PerspectiveNPoint  
from SharedData import FusedSensorsData

# IP = '192.168.65.127'
IP = "127.0.0.1"
PORT= 2002
VIDEOPATH = "/home/zahra/catkin_ws/src/calibration/script/video/test.mp4"
OUTPUTPATH = "/home/zahra/catkin_ws/src/calibration/script/output"
# VIDEOPATH = 0

class Ui_MainWindow():
    
    def SetupUI(self, MainWindow):
        
        ## Obtained from QtDesigner
        ## defining the relavent Qt objects related to the UI buttons/texts/bars
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphicsView.setGeometry(QtCore.QRect(5, 5, 900, 500))
        self.graphicsView.setObjectName("graphicsView")
        
        newfont = QtGui.QFont("Times", 10, QtGui.QFont.Bold) 
        self.VideoText = QtWidgets.QLabel(self.centralwidget)
        self.VideoText.setGeometry(QtCore.QRect(5, 530, 141, 41))
        self.VideoText.setObjectName("VideoCapture")
        self.VideoText.setFont(newfont)

        self.StartVideoButton = QtWidgets.QPushButton(self.centralwidget)
        self.StartVideoButton.setGeometry(QtCore.QRect(5, 570, 141, 41))
        self.StartVideoButton.setObjectName("Start")

        self.StopVideoButton = QtWidgets.QPushButton(self.centralwidget)
        self.StopVideoButton.setGeometry(QtCore.QRect(5, 610, 141, 41))
        self.StopVideoButton.setObjectName("Stop")
        
        self.FaceLabText = QtWidgets.QLabel(self.centralwidget)
        self.FaceLabText.setGeometry(QtCore.QRect(200, 530, 141, 41))
        self.FaceLabText.setObjectName("Facelab")
        self.FaceLabText.setFont(newfont)
        
        self.FaceLabStartButton = QtWidgets.QPushButton(self.centralwidget)
        self.FaceLabStartButton.setGeometry(QtCore.QRect(200, 570, 141, 41))
        self.FaceLabStartButton.setObjectName("Start")

        self.FaceLabStopButton = QtWidgets.QPushButton(self.centralwidget)
        self.FaceLabStopButton.setGeometry(QtCore.QRect(200, 610, 141, 41))
        self.FaceLabStopButton.setObjectName("Stop")

        self.CollectButton = QtWidgets.QPushButton(self.centralwidget)
        self.CollectButton.setGeometry(QtCore.QRect(380, 570, 141, 41))
        self.CollectButton.setObjectName("Collect")

        self.CalibrateButton = QtWidgets.QPushButton(self.centralwidget)
        self.CalibrateButton.setGeometry(QtCore.QRect(520, 570, 141, 41))
        self.CalibrateButton.setObjectName("Calibrate")

        MainWindow.setCentralWidget(self.centralwidget)
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
               
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")

        self.subMenu = QtWidgets.QMenu(self.menubar)
        self.subMenu.setObjectName("menuMenu")
        self.subMenu.addAction(self.actionQuit)
        self.menubar.addAction(self.subMenu.menuAction())

        self.RetranslateUIText(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        ## Connecting Qt Button to their associated functions
        ## requires function reference to connect
        self.actionQuit.triggered.connect(self.ExitApp)
        self.StartVideoButton.clicked.connect(self.LaunchCameraThread)
        self.StopVideoButton.clicked.connect(self.TerminateCameraThread)
        self.FaceLabStartButton.clicked.connect(self.LaunchFaceLabThread)
        self.FaceLabStopButton.clicked.connect(self.TerminateFaceLabThread)
        self.CollectButton.clicked.connect(self.CollectAndFuseData)
        self.CalibrateButton.clicked.connect(self.Calibrate)
        
        # for fusing data from the 2 threads
        self.fusedSensorData = FusedSensorsData()
        # define 2 threads for handling camera and facelab eye tracker
        self.threadFaceLab = None 
        self.threadCamera = None

    #runs when collect GUI button pushed
    def CollectAndFuseData(self):
        self.threadFaceLab.Collect()
        self.threadCamera.Collect()

    # runs when Calibrate GUI button pushed
    def Calibrate(self):
        self.RunPnP()

    ## generated by QtDesigner for defining text in the Qlabel objects
    ## obtained from QtDesigner
    def RetranslateUIText(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        
        self.subMenu.setTitle(_translate("MainWindow", "Menu"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        
        self.FaceLabText.setText(_translate("MainWindow", "EyeTracker"))
        self.FaceLabStartButton.setText(_translate("MainWindow", "Start"))
        self.FaceLabStopButton.setText(_translate("MainWindow", "Stop"))
        self.CollectButton.setText(_translate("MainWindow", "Collect")) 
        self.CalibrateButton.setText(_translate("MainWindow", "Calibrate")) 

        self.VideoText.setText(_translate("MainWindow", "VideoCapture"))
        self.StartVideoButton.setText(_translate("MainWindow", "Start"))
        self.StopVideoButton.setText(_translate("MainWindow", "Stop"))
    
    #launch FaceLab thread
    def LaunchFaceLabThread(self):
        self.threadFaceLab = FacelabThread(IP, PORT, OUTPUTPATH, self.fusedSensorData) 
        self.threadFaceLab.StartReadingSocket()
        self.threadFaceLab.start()
    
    # terminate facelab thread
    def TerminateFaceLabThread(self):
        self.threadFaceLab.Terminate()
    
    #launch camera thread
    def LaunchCameraThread(self):
        self.threadCamera = CameraThread(VIDEOPATH, OUTPUTPATH, self.fusedSensorData)
        self.threadCamera.StartVideoCapture()
        self.threadCamera.imgSignalQt.connect(self.ShowImgQt)
        self.threadCamera.start()    

    #terminate camera thread
    def TerminateCameraThread(self):
        self.threadCamera.Terminate()

    def RunPnP(self):

        objectPoints = np.array(self.fusedSensorData.GetObjectPoint())
        gazeVectors = np.array(self.fusedSensorData.GetGazeVector())

        PnP = PerspectiveNPoint(gazeVectors, objectPoints)
        (errorPnP,errorPnPRansac,Rt_pnp,translation_vector_pnp,Rt_Ransac,translation_vector_Ransac)= PnP.Run()
        print("[INFO] Reprojection error from PnP()={}".format(errorPnP))
        print("[INFO] Reprojection error from PnPRansac()={}".format(errorPnPRansac))
        print("[INFO] Rt={}".format(Rt_pnp))
        print("[INFO] T={}".format(translation_vector_pnp))
        print("[INFO] calibration Done")
        
    ## Show camera frame in UI real-time
    def ShowImgQt(self, image):
        scene = QtWidgets.QGraphicsScene()
        item = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(image))
        scene.addItem(item)
        self.graphicsView.setScene(scene)

    ## exit UI
    def ExitApp(self):
        try:
            if self.threadCamera is not None:
                self.TerminateCameraThread()

            if self.threadFaceLab is not None:
                self.TerminateFaceLabThread()
        finally:
            QtWidgets.QApplication.quit()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    UI = Ui_MainWindow()
    UI.SetupUI(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())