import numpy as np
import cv2
import random

class PerspectiveNPoint(object):
    
    def __init__(self, gazeVector, objectPoints):
        '''
        Initilization of GazeVector and World Coordinate and camera matrix
        '''

        self.gazeVector = np.array(gazeVector)[:, 0:3]
        self.objPoints = objectPoints
        self.FilterNoises()
        self.cameraMatrix = np.array([ [1, 0, 0],
                           [0, 1, 0],
                           [0, 0, 1]], dtype = "double")
        self.distortionCoeff = np.zeros((4,1)) # Assuming no lens distortion

    def FilterNoises(self):
        '''
        remove the data that have high head displacement as well as does not have depth information
        sometimes, Intel Realsense sends zero (X, Y, Z)
        '''
        noise_indices = []

        #check if StereoSystem is returning zero values
        for (index,point) in enumerate(self.objPoints):
            if point[0] == 0 and point[1] == 0 and point[2] == 0:
                noise_indices.append(index)
            if point[2] > 6000:
                noise_indices.append(index)

        self.IDs = self.gazeVector.shape[0]

    def CrossSectionPoints(self, gazeVector):
        '''
        Compute intersection of whole gaze vectors with the virtual plane and return numpy array
        '''
        ImagePoints = np.zeros((gazeVector.shape[0],2),dtype="double")
        for i in range(gazeVector.shape[0]):
            ImagePoints[i,:] = self.CrossSectionPoint(gazeVector[i,:])

        return ImagePoints
    
    def CrossSectionPoint(self,GazeVec):
        '''
        Computer intersection of only one gaze vector and return to a single point (x,y)
        '''
        t= 1/(GazeVec[2].astype('double'))
        X_sec = GazeVec[0] * t
        Y_sec = GazeVec[1] * t
        return X_sec,Y_sec
    
    def PnP(self, objPoints, ImagePoints):
        '''
        Apply PnP routine and return rotation and translation matrices
        '''
        
        # PnP don't work on the synthetic data
        return -1, -1
    
        if self.IDs > 3:

            (retval,rvecs, tvecs) = cv2.solvePnP(objPoints,ImagePoints, self.cameraMatrix, 
                                        self.distortionCoeff, flags=cv2.SOLVEPNP_EPNP)
            Rt, _ = cv2.Rodrigues(rvecs)
            return Rt, tvecs

        else:
            print("[INFO] Too few points, calibration cannot be done ...")
            return -1, -1
    
    def PnPRansac(self, objPoints, ImagePoints):
        '''
        Apply PnPRansac routine and return rotation and translation matrices
        PnPRansac is less sensitive to errors
        '''
        if self.IDs > 3:
            (_, rvecs, tvecs, inliers) = cv2.solvePnPRansac(objPoints, ImagePoints, self.cameraMatrix, 
                                                        self.distortionCoeff)
            Rt, _ = cv2.Rodrigues(rvecs)
            return Rt, tvecs
        else:
            print("[INFO] Too few points, calibration cannot be done ...")
            return None    
    

    def GetScaleFactor(self,Rt,translation_vector):
        '''
        Compute the unknown scale factor 
        '''
        
        scalefactor = np.zeros((self.objPoints.shape[0],1))
        for i in range(self.objPoints.shape[0]):
            Sample_3Dpoint = self.objPoints[i].reshape(3,1)
            R_s = np.dot(Rt,Sample_3Dpoint).reshape(3,1) + translation_vector.reshape(3,1)
            Pixel_coord = np.dot(self.cameraMatrix,R_s)
            scalefactor[i] = Pixel_coord[2]
        return scalefactor
    
    def Reprojection(self,ImagePoints,S,Rt,translation_vector):
        '''
        Reproject Image points into 3D world coordinate systems to measure error
        '''
        ReprojectionPoints = np.zeros((self.IDs,3))
        ImagePoints_conc = np.concatenate((ImagePoints, np.array([1] * self.IDs).reshape(self.IDs,1) ), axis=1) 
        ImagePoints_scale = np.multiply(ImagePoints_conc,S)
        
        for i in range(self.IDs):
            first_part = np.dot(np.linalg.inv(Rt),np.linalg.inv(self.cameraMatrix))
            secon_part = np.dot(first_part, ImagePoints_scale[i])
            third_part = np.dot(np.linalg.inv(Rt),translation_vector)
            ReprojectionPoints[i,:] =  np.transpose((secon_part.reshape(3,1) - third_part))
            
        return ReprojectionPoints
    
    
    def Error(self,ImagePoints_noise,Rt,translation_vector):
        '''
        Compute the reprojection error
        '''
        if False: # not working on the synthetic data
            S = self.GetScaleFactor(Rt,translation_vector) 
            ReprojectionPoints = self.Reprojection(ImagePoints_noise, S,Rt,translation_vector)
            reprojection_error = self.objPoints - ReprojectionPoints
            
            return reprojection_error
        
        return 0.
    
    def Run(self):
        '''
         Measure the error as sum of square root of the difference 
         between 3D projected and noisless 3D points
        '''

        return (-1, -1, -1 ,-1, -1, -1)
    
        if False:
            ImagePoints= self.CrossSectionPoints(self.gazeVector) 
            Rt_pnp,translation_vector_pnp = self.PnP(self.objPoints,ImagePoints)
            Rt_Ransac,translation_vector_Ransac = self.PnPRansac(self.objPoints,ImagePoints)
            PnP_diff = self.Error(ImagePoints,Rt_pnp,translation_vector_pnp)
            Ransac_diff = self.Error(ImagePoints,Rt_Ransac,translation_vector_Ransac)
            error_PnP = np.average(np.linalg.norm(PnP_diff, axis=1))
            error_PnPRansac = np.average(np.linalg.norm(Ransac_diff, axis=1))
            
            return (error_PnP,error_PnPRansac,Rt_pnp,translation_vector_pnp,Rt_Ransac,translation_vector_Ransac)
    

        
