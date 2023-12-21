import cv2
import socket

from pistream import Consts, Protocol, Network


def connect():
    Protocol.start_connection(Network.client_socket, Network.server_address)


def init(ip: str, port: int = 9999):
    Network.server_address = (ip, port)

    Network.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Network.client_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_RCVBUF, Consts.PACK_SIZE * Consts.BUFFER_PACKETS
    )
    Network.client_socket.settimeout(2)

    connect()


def request_frame():
    Protocol.request_frame(Network.client_socket, Network.server_address)


def request_stream_start():
    Protocol.request_stream_start(Network.client_socket, Network.server_address)


def request_stream_stop():
    Protocol.request_stream_stop(Network.client_socket, Network.server_address)


def request_enable_timeout():
    Protocol.request_enable_timeout(Network.client_socket, Network.server_address)


def request_disable_timeout():
    Protocol.request_disable_timeout(Network.client_socket, Network.server_address)


def kill_server():
    Protocol.kill_server(Network.client_socket, Network.server_address)


def listen():
    try:
        packet = Network.client_socket.recvfrom(Consts.PACK_SIZE)[0]
    except TimeoutError:
        print("Timeout")
        connect()
        return None

    return Protocol.decode_packet(packet)


def close():
    Protocol.terminate(Network.client_socket, Network.server_address)
    Network.client_socket.close()


def process_packet(image_data, code, id, data):
    """
    Two return values
    boolean frame_complete - does imageData contain a full frame or does it still have missing packets?
    dict    image_data     - a dictionary indexed by packet ID of every packet in the current frame
    In UDP, packets can transmit in the wrong order, so their IDs are preserved so that they can be sorted later
    """

    if Protocol.connection_ending(code):
        print("Server connection terminated, killing client...")
        close()
        exit()
    elif Protocol.connection_timedout(code):
        connect()
        return False, image_data

    elif Protocol.frame_starting(code):
        image_data = {}
    elif len(image_data) == 0:
        return False, image_data

    image_data[id] = data

    if not Protocol.frame_ending(code):
        return False, image_data

    return True, image_data


def extract_image(image_data):
    try:
        image_data = sorted(image_data.items())
    except AttributeError:
        print("An unknown bug occurred receiving the current frame")
        return None

    if image_data[-1][0] + 1 > len(image_data):
        print("Lost packet, skipping frame")
        image_data = {}
        # NOTE: THIS IS WHERE RESENDING CODE WOULD GO
        # ASK FOR SPECIFIC PACKETS ENCODED SOMEHOW
        return None

    try:
        encoded_image = Protocol.unpack_data(image_data)
    except ValueError:
        print("Corrupted packet, skipping frame")
        return None

    return cv2.imdecode(encoded_image, 1)


def respond():
    Network.client_socket.sendto(
        Protocol.encode_simple_packet(Protocol.Code.NORMAL), Network.server_address
    )


def display(image):
    cv2.imshow("RECEIVING VIDEO", image)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        Protocol.terminate(Network.client_socket, Network.server_address)
        exit()
    elif key == ord("k"):
        kill_server()
        exit()


def get_image(show_image: bool = False):
    try:
        image_data = {}

        frame_complete = False

        while not frame_complete:
            packet = listen()

            if packet is None:
                continue

            frame_complete, image_data = process_packet(image_data, *packet)

        image = extract_image(image_data)

        if show_image and image is not None:
            display(image)

        respond()

        return image
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        close()
        exit()
