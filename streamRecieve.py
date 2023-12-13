
# This is client code to receive video frames over UDP
import cv2, imutils, socket
import numpy as np
import time
import base64

BUFF_SIZE = 65536
client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)

host_ip = "192.168.10.255"
print(host_ip)

port = 9999
message = b'Hello'

client_socket.sendto(message,(host_ip,port))

while True:
    packet,_ = client_socket.recvfrom(BUFF_SIZE)

    data = base64.b64decode(packet,' /')

    if data == "terminate":
        exit()

    npdata = np.fromstring(data,dtype=np.uint8)
    frame = cv2.imdecode(npdata,1)
    cv2.imshow("RECEIVING VIDEO",frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        client_socket.close()
        break
