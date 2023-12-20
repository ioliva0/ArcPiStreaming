import socket
import picamera2
import cv2
import time

from afpistream import Consts, Protocol, Network


def init():
    print("initializing socket")
    Network.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Network.server_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_RCVBUF, Consts.PACK_SIZE
    )

    Network.server_socket.bind(("0.0.0.0", Network.server_address[1]))
    print("socket initialization complete")

    print("Waiting for camera to intialize")
    Network.camera = picamera2.Picamera2()
    config = Network.camera.create_video_configuration(
        main={"size": Consts.RESOLUTION, "format": "RGB888"}, buffer_count=6
    )
    Network.camera.configure(config)
    Network.camera.set_controls({"ExposureTime": Consts.EXPOSURE})
    Network.camera.start()
    time.sleep(1)  # sleep statement to allow camera to fully wake up
    print("camera initialization complete")


def close():
    Network.camera.stop()
    Network.server_socket.close()


def killKey():
    print("KeyboardInterrupt")
    close()
    exit()


def wait_for_connection():
    try:
        connected = False
        Network.server_socket.settimeout(10)

        while not connected:
            print("waiting for connection...")
            try:
                packet, Network.client_address = Network.server_socket.recvfrom(
                    Consts.PACK_SIZE
                )
            except TimeoutError:
                continue

            if Protocol.connection_starting(Protocol.decode_simple_packet(packet)):
                connected = True
            else:
                print("Connection recieved, non-initiating")

        print("GOT connection from " + str(Network.client_address))

    except KeyboardInterrupt:
        killKey()


def listen():
    """
    Return value: connected
    if connected is false, the client has disconnected from the server and the server should start looking for a new client
    """

    connected = True

    try:
        code = Protocol.decode_simple_packet(
            Network.server_socket.recvfrom(Protocol.CODE_SIZE)[0]
        )
        if Protocol.server_kill_triggered(code):
            Protocol.terminate(Network.server_socket, Network.client_address)
            close()
            exit()
        elif Protocol.connection_ending(code):
            Protocol.terminate(Network.server_socket, Network.client_address)
            connected = False
    except TimeoutError:
        Protocol.timeout(Network.server_socket, Network.client_address)
        connected = False

    return connected


def send_image():
    try:
        image = Network.camera.capture_array()

        _, image_encoded = cv2.imencode(
            ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, Consts.JPEG_QUALITY]
        )

        packets = Protocol.package_image(image_encoded)

        for packet in packets:
            Network.server_socket.sendto(packet, Network.client_address)

        return listen()
    except KeyboardInterrupt:
        killKey()
