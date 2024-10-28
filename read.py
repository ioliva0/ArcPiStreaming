import cv2
import time
import logging
import socket
import time
import picamera2
import numpy

def estimatePoseSingleMarkers(corners, marker_size, mtx, distortion):
    marker_points = numpy.array([[-marker_size / 2, marker_size / 2, 0],
                              [marker_size / 2, marker_size / 2, 0],
                              [marker_size / 2, -marker_size / 2, 0],
                              [-marker_size / 2, -marker_size / 2, 0]], dtype=numpy.float32)
    
    success, rotation_vector, translation_vector = cv2.solvePnP(marker_points, corners, mtx, distortion, False, cv2.SOLVEPNP_IPPE_SQUARE)

    translation_vector = [int(pos[0] * 10) / 10 for pos in translation_vector]
    translation_vector = (translation_vector[0], translation_vector[2])

    rotation_vector = [int(angle[0] * 10) / 10 for angle in rotation_vector]
    rotation = rotation_vector[2]

    return translation_vector, rotation

print("Waiting for camera to intialize")
camera = picamera2.Picamera2()
config = camera.create_video_configuration(
    main={"size": (720,480), "format": "RGB888"}, buffer_count=6
)
camera.configure(config)
camera.set_controls({"ExposureTime": 130000})
camera.start()
time.sleep(1)  # sleep statement to allow camera to fully wake up
print("camera initialization complete")

#aruco tag stuff
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

while True:
    frame = camera.capture_array()

    corners, ids, rejected = detector.detectMarkers(frame)

    #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        #estimatePoseSingleMarkers(corners, 7.7, frame, distortion)
 
        print(ids)
        #print(cx, cy, "cx / cy")

    cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break

#m.land()
