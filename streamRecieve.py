
# This is client code to receive video frames over UDP
import cv2, socket
import numpy as np
from struct import unpack
from io import BytesIO

import Consts
import Protocol

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, Consts.PACK_SIZE)
client_socket.settimeout(1)

host_ip = "172.17.17.120"
port = 9999
server_address = (host_ip, port)

client_socket.sendto(b'Hello',server_address)

image_data = {}

while True:

    packet = client_socket.recvfrom(Consts.PACK_SIZE)

    code, id, data = Protocol.decode_packet(packet)

    if Protocol.connection_ending(code):
        print("Server connection terminated, killing client...")
        break
    elif Protocol.frame_starting(code):
        image_data = {}
    elif len(image_data) == 0:
        continue

    image_data[id] = data

    if not Protocol.frame_ending(code):
        continue
    
    image_data = sorted(image_data.items())

    if image_data[-1][0] + 1 > len(image_data):
        print("Not enough data: must have lost a packet")

        #NOTE: THIS IS WHERE RESENDING CODE WOULD GO
        #ASK FOR SPECIFIC PACKETS ENCODED SOMEHOW

        continue
    
    image_bytes = b''.join([payload[1] for payload in image_data])
    image_bytes_obj = BytesIO(image_bytes)
    encoded_image = np.load(image_bytes_obj, allow_pickle=True)

    image = cv2.imdecode(encoded_image, 1)
    cv2.imshow("RECEIVING VIDEO", image)

    #print(id)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    

client_socket.close()
