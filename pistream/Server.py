import socket
import picamera2
import cv2
import time

from pistream import Consts, Protocol, Network


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


def enable_timeout(seconds: int = 10):
    Network.server_socket.settimeout(seconds)


def disable_timeout():
    Network.server_socket.settimeout(None)


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


def handle_command(code):
    """
    Return value: connected
    if connected is false, the client has disconnected from the server and the server should start looking for a new client
    """

    if Protocol.is_normal(code) or Protocol.connection_starting(code):
        return True

    if Protocol.server_kill_triggered(code):
        Protocol.terminate(Network.server_socket, Network.client_address)
        close()
        exit()

    if Protocol.connection_ending(code):
        Protocol.terminate(Network.server_socket, Network.client_address)
        return False

    if Protocol.timeout_enable_requested(code):
        enable_timeout()
        return True
    if Protocol.timeout_disable_requested(code):
        disable_timeout()
        return True

    if Protocol.frame_requested(code):
        Network.frame_requested = True
        return True
    if Protocol.stream_start_requested(code):
        Network.stream_requested = True
        return True
    if Protocol.stream_stop_requested(code):
        Network.stream_requested = False
        return True

    print("Invalid command sent to server")
    return False


def listen():
    """
    Return value: connected
    if connected is false, the client has disconnected from the server and the server should start looking for a new client
    """

    try:
        packet = Network.server_socket.recvfrom(Protocol.CODE_SIZE)[0]
        code = Protocol.decode_simple_packet(packet)
        return handle_command(code)

    except TimeoutError:
        Protocol.timeout(Network.server_socket, Network.client_address)
    except Exception:
        print("Error getting client response, this should never happen")
    return True


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


def serve():
    try:
        if not listen():
            return False

        if Network.frame_requested:
            Network.frame_requested = False
            return send_image()

        elif Network.stream_requested:
            return send_image()

        return True

    except KeyboardInterrupt:
        killKey()
