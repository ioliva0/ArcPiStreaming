import picamera2

# This is server code to send video frames over UDP
import cv2, imutils, socket
import numpy as np
import time
import base64

BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)

server_socket.bind(('192.168.1.102', 9999))

camera = picamera2.PiCamera2()
camera.start()
time.sleep(1)

while (cv2.getKey(10) & 0xFF) != ord("q"):
    image = camera.capture_array()
    
    msg,client_addr = server_socket.recvfrom(BUFF_SIZE)
    print('GOT connection from ',client_addr)

    encoded,buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,80])
    message = base64.b64encode(buffer)
    server_socket.sendto(message,client_addr)

    cv2.imshow('TRANSMITTING VIDEO',image)