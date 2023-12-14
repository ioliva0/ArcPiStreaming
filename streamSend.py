import picamera2

# This is server code to send video frames over UDP
import cv2, socket
import numpy as np
import time
import base64

BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)

server_socket.bind(('0.0.0.0', 9999))

camera = picamera2.Picamera2()
camera.start()
time.sleep(2)

while (cv2.waitKey(10) & 0xFF) != ord("q"):
    image = camera.capture_array()
    try:
        msg,client_addr = server_socket.recvfrom(1024)
    except Exception as e:
        server_socket.sendto(b'terminate',client_addr)
        server_socket.close()
        raise e
    print('GOT connection from ',client_addr)

    encoded,buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,80])
    message = base64.b64encode(buffer)

    packet_id = 0

    server_socket.sendto(b'START',client_addr)
    
    while len(message) > 0:
        message_packet = str(packet_id).encode() + b"|" + message[:1000]

        server_socket.sendto(message_packet, client_addr)

        print(message_packet)

        message = message[1000:]
        packet_id += 1
    
    server_socket.sendto(b'FIN',client_addr)

    cv2.imshow('TRANSMITTING VIDEO',image)