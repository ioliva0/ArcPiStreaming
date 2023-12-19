import cv2

import Consts
import Protocol

import socket

def init():
    client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, Consts.PACK_SIZE * Consts.BUFFER_PACKETS)
    client_socket.settimeout(2)

    server_address = (Consts.SERVER_IP, Consts.SERVER_PORT)

    connection = (client_socket, server_address)

    Protocol.initiate(*connection)

    return connection



def listen(client_socket, server_address):
    try:
        packet = client_socket.recvfrom(Consts.PACK_SIZE)[0]
    except TimeoutError:
        print("Timeout")
        Protocol.initiate(client_socket, server_address)
        return True

    return (Protocol.decode_packet(packet))


def process_packet(image_data, code, id, data, client_socket, server_address):

    """
    Two return values
    boolean frame_complete - does imageData contain a full frame or does it still have missing packets?
    dict    image_data     - a dictionary indexed by packet ID of every packet in the current frame
    In UDP, packets can transmit in the wrong order, so their IDs are preserved so that they can be sorted later
    """

    if Protocol.connection_ending(code):
        print("Server connection terminated, killing client...")
        exit()
    elif Protocol.connection_timedout(code):
        Protocol.initiate(client_socket, server_address)
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
        #NOTE: THIS IS WHERE RESENDING CODE WOULD GO
        #ASK FOR SPECIFIC PACKETS ENCODED SOMEHOW
        return None

    encoded_image = Protocol.unpack_data(image_data)
    return cv2.imdecode(encoded_image, 1)

def respond(client_socket, server_address):
    client_socket.sendto(Protocol.encode_simple_packet(Protocol.Code.NORMAL), server_address)

def display(image, connection):
    cv2.imshow("RECEIVING VIDEO", image)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        exit()
    elif key == ord('k'):
        Protocol.kill_server(*connection)
        exit()

def close(client_socket, server_address):
    Protocol.terminate(client_socket, server_address)
    client_socket.close()