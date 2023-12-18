import picamera2

# This is server code to send video frames over UDP
import cv2, socket
import time

import Consts
import Protocol

print("initializing socket")
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,Consts.PACK_SIZE)

server_socket.bind(('0.0.0.0', 9999))
print("socket initialization complete")

print("Waiting for camera to intialize")
camera = picamera2.Picamera2()
camera.start()
time.sleep(1)#sleep statement to allow camera to fully wake up
print("Camera initialization complete")

msg,client_addr = server_socket.recvfrom(Consts.PACK_SIZE)
print('GOT connection from ',client_addr)
server_socket.settimeout(1)

connected = True

try:
    while connected:
        image = camera.capture_array()

        _, image_encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,80])

        packets = Protocol.package_image(image_encoded)

        for packet in packets:
            server_socket.sendto(packet, client_addr)

            try:
                if Protocol.connection_ending(Protocol.decode_simple_packet(server_socket.recvfrom(Protocol.CODE_SIZE)[0])):
                    connected = False
            except TimeoutError:
                Protocol.timeout(server_socket, client_addr)
except KeyboardInterrupt:
    pass
            
Protocol.terminate(server_socket, client_addr)
server_socket.close()