
# This is client code to receive video frames over UDP
import cv2, socket
import numpy as np
from struct import unpack

from Consts import *

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, PACK_SIZE)

host_ip = "172.17.17.120"
print(host_ip)

port = 9999

client_socket.sendto(b'Hello',(host_ip,port))

while True:


    code, id, data = unpack("BHs", client_socket.recvfrom(PACK_SIZE)[0])

    data = {}
    
    frame_complete = False

    if len(data) == 0 and code != Code.FRAME_START and code != Code.FRAME_SOLO:
        continue
    
    data[id] = data

    if code == Code.FRAME_END or code == Code.FRAME_SOLO:
        npdata = np.fromstring(data,dtype=np.uint8)
        frame = cv2.imdecode(npdata,1)
        cv2.imshow("RECEIVING VIDEO",frame)
    
    key = cv2.waitKey(10) & 0xFF
    if key == ord('q'):
        client_socket.close()
        break
