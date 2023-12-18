import picamera2

# This is server code to send video frames over UDP
import cv2, socket
import numpy as np
import time
from struct import pack
from io import BytesIO
from time import sleep

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

    metadata = pack(">BH", code, id)

    return metadata + data

def send(packet, address):
    server_socket.sendto(packet, address)

def terminate(address):
    print("Terminating...")
    send(pack(">BH", Code.CONNECTION_END.value, 0), address)

print("Waiting for camera to intialize")
camera = picamera2.Picamera2()
camera.start()
time.sleep(1)#sleep statement to allow camera to fully wake up
print("Camera initialization complete")

msg,client_addr = server_socket.recvfrom(PACK_SIZE)
print('GOT connection from ',client_addr)
server_socket.settimeout(1)

while True:
    image = camera.capture_array()

    _, image_encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,80])
    
    image_data = BytesIO()
    np.save(image_data, image_encoded, allow_pickle=False)
    image_data.seek(0)

    image_data = image_data.read()

    packet_id = 0
    
    while len(image_data) > 0:

        starting = False
        ending = False

        if packet_id == 0:
            starting = True
        if len(image_data) < DATA_SIZE:
            ending = True


        data = packet(starting, ending, packet_id, image_data[:DATA_SIZE])

        send(data, client_addr)
        server_socket.recvfrom(PACK_SIZE)

        image_data = image_data[DATA_SIZE:]
        packet_id += 1

terminate(client_addr)
server_socket.close()