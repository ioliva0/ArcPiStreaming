
# This is client code to receive video frames over UDP
import cv2, socket
import numpy as np
from struct import unpack
from io import BytesIO

from Consts import *

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, PACK_SIZE)

host_ip = "172.17.17.120"
port = 9999
server_address = (host_ip, port)

client_socket.sendto(b'Hello',server_address)

image_data = {}


while True:

    print("receiving...")


    packet = client_socket.recvfrom(PACK_SIZE)[0]
    code, id = unpack(">BH", packet[:24])
    data = packet[24:]

    if code == Code.CONNECTION_END:
        exit()

    client_socket.sendto(b'RECIEVED', server_address)    
    frame_complete = False

    if len(image_data) == 0 and code != Code.FRAME_START.value and code != Code.FRAME_SOLO.value:
        continue
    
    if code == Code.FRAME_START.value or code == Code.FRAME_SOLO.value:
        image_data = {}

    image_data[id] = data

    print(image_data)

    if code == Code.FRAME_END.value or code == Code.FRAME_SOLO.value:
        
        print(image_data)

        image_bytes = b''.join([payload[1] for payload in sorted(image_data.items())])

        image_bytes_obj = BytesIO(image_bytes)

        encoded_image = np.load(image_bytes_obj, allow_pickle=True)

        image = cv2.imdecode(encoded_image, 1)
        cv2.imshow("RECEIVING VIDEO", image)
    
    key = cv2.waitKey(10) & 0xFF
    if key == ord('q'):
        client_socket.close()
        break
