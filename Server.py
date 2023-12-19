import socket
import picamera2
import cv2
import time

import Consts
import Protocol

def init():
    print("initializing socket")
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,Consts.PACK_SIZE)

    server_socket.bind(('0.0.0.0', Consts.SERVER_PORT))
    print("socket initialization complete")

    print("Waiting for camera to intialize")
    camera = picamera2.Picamera2()
    config = camera.create_video_configuration(main={"size": Consts.RESOLUTION, "format": "RGB888"}, buffer_count=6)
    camera.configure(config)
    camera.set_controls({"ExposureTime" : Consts.EXPOSURE})
    camera.start()
    time.sleep(1)#sleep statement to allow camera to fully wake up
    print("Camera initialization complete")

    return server_socket, camera

def wait_for_connection(server_socket):
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
    return client_addr

def send_image(camera, server_socket, client_addr):
    image = camera.capture_array()

    _, image_encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY,Consts.JPEG_QUALITY])

    packets = Protocol.package_image(image_encoded)

    for packet in packets:
        server_socket.sendto(packet, client_addr)

def listen(server_socket, client_addr):
    """
    Return values: listening, connected
    if listening is false, the server has been sent a command to stop listening for input
    if connected is false, the client has disconnected from the server and the server should start looking for a new client
    """

    listening = True
    connected = True

    try:
        code = Protocol.decode_simple_packet(server_socket.recvfrom(Protocol.CODE_SIZE)[0])
        if Protocol.server_kill_triggered(code):
            Protocol.terminate(server_socket, client_addr)
            listening = False
            connected = False
        elif Protocol.connection_ending(code):
            Protocol.terminate(server_socket, client_addr)
            connected = False
    except TimeoutError:
        Protocol.timeout(server_socket, client_addr)
        connected = False

    return listening, connected