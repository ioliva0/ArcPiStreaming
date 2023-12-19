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
config = camera.create_video_configuration(main={"size": Consts.RESOLUTION, "format": "RGB888"}, buffer_count=6)
camera.configure(config)
camera.set_controls({"ExposureTime" : Consts.EXPOSURE})
camera.start()
time.sleep(1)#sleep statement to allow camera to fully wake up
print("Camera initialization complete")

listening = True

while listening:
    connected = False
    server_socket.settimeout(10)

    while not connected:
        print("waiting for connection...")
        try:
            packet,client_addr = server_socket.recvfrom(Consts.PACK_SIZE)
        except TimeoutError:
            continue

        if Protocol.connection_starting(Protocol.decode_simple_packet(packet)):
            connected = True
        else:
            print("Connection recieved, non-initiating")

    print('GOT connection from ' + str(client_addr))
    server_socket.settimeout(1)
    timeouts = 0

    try:
        while connected:
            

            image = camera.capture_array()

            start_time = time.time()
            _, image_encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,Consts.JPEG_QUALITY])
            print("Encoding image: " + str(int((time.time() - start_time) * 1000)))
            start_time = time.time()

            packets = Protocol.package_image(image_encoded)

            for packet in packets:
                server_socket.sendto(packet, client_addr)
            
            try:
                code = Protocol.decode_simple_packet(server_socket.recvfrom(Protocol.CODE_SIZE)[0])
                timeouts = 0
                if Protocol.server_kill_triggered(code):
                    listening = False
                    connected = False
                    Protocol.terminate(server_socket, client_addr)
                elif Protocol.connection_ending(code):
                    connected = False
                    Protocol.terminate(server_socket, client_addr)
            except TimeoutError:
                connected = False
                Protocol.timeout(server_socket, client_addr)

    except KeyboardInterrupt:
        pass

    
            
server_socket.close()