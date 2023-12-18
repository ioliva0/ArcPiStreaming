
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
    code, id = unpack(">BH", packet[:3])
    data = packet[3:]

    print(id)

    print("data recieved")

    if code == Code.CONNECTION_END:
        exit()

    client_socket.sendto(b'RECIEVED', server_address)    
    frame_complete = False

    if len(image_data) == 0 and code != Code.FRAME_START.value and code != Code.FRAME_SOLO.value:
        continue
    
    if code == Code.FRAME_START.value or code == Code.FRAME_SOLO.value:
        image_data = {}

    image_data[id] = data

    if code == Code.FRAME_END.value or code == Code.FRAME_SOLO.value:
        
        image_data = sorted(image_data.items())

        if image_data[-1][0] + 1 > len(image_data):
            print("Not enough data: must have lost a packet")
        else:
            print(len(image_data))
            print([packet_data[0] for packet_data in image_data])
            print("Sufficient packets to create image (?)")
        

        image_bytes = b''.join([payload[1] for payload in image_data])

        print("here")
        with open("./recieved.txt", 'w') as out:
            out.write(str(image_bytes))
            out.close()
        print("here 2")

        client_socket.sendto(b"done", server_address)


        image_bytes_obj = BytesIO(image_bytes)

        print(image_bytes)

        encoded_image = np.load(image_bytes_obj, allow_pickle=False)

        image = cv2.imdecode(encoded_image, 1)
        cv2.imshow("RECEIVING VIDEO", image)

        exit()
    
    key = cv2.waitKey(10) & 0xFF
    if key == ord('q'):
        client_socket.close()
        break
