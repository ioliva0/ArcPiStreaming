import picamera2

# This is server code to send video frames over UDP
import cv2, socket
import numpy as np
import time
from struct import pack

from Consts import *

print("initializing socket")
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,PACK_SIZE)

server_socket.bind(('0.0.0.0', 9999))
print("socket initialization complete")

def packet(starting : bool, ending : bool, id : int, data : bytes):
    code = 0
    if starting:
        code += Code.FRAME_START.value
    if ending:
        code += Code.FRAME_END.value

    return pack("BHs", code, id, data)

def send(packet, address):
    server_socket.sendto(packet, address)

def terminate():
    return pack("B", Code.CONNECTION_END.value)

print("Waiting for camera to intialize")
camera = picamera2.Picamera2()
camera.start()
time.sleep(1)#sleep statement to allow camera to fully wake up
print("Camera initialization complete")

msg,client_addr = server_socket.recvfrom(PACK_SIZE)
print('GOT connection from ',client_addr)

while (cv2.waitKey(10) & 0xFF) != ord("q"):
    image = camera.capture_array()

    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,80])

    packet_id = 0
    
    while len(buffer) > 0:

        starting = False
        ending = False

        if packet_id == 0:
            starting = True
        if len(buffer) < DATA_SIZE:
            ending = True

        data = packet(starting, ending, packet_id, buffer[:DATA_SIZE])

        send(data, client_addr)

        buffer = buffer[DATA_SIZE:]
        packet_id += 1

    cv2.imshow('TRANSMITTING VIDEO',image)