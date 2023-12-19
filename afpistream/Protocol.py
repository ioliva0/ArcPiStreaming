from struct import pack, unpack
from enum import Enum
from numpy import save, load, ndarray
from io import BytesIO

from afpistream import Consts

CODE_SIZE = 1
METADATA_SIZE = 3
DATA_SIZE = Consts.PACK_SIZE - METADATA_SIZE


class Code(Enum):
    # universal
    NORMAL = 0
    CONNECTION_END = 1
    CONNECTION_TIMEOUT = 2

    # serverside
    FRAME_START = 3
    FRAME_END = 4
    FRAME_SOLO = 5

    # general client commands
    CONNECTION_START = 6
    SERVER_KILL = 7

    # client requests
    REQUEST_FRAME = 8
    REQUEST_STREAM_START = 9
    REQUEST_STREAM_STOP = 10


def encode_packet(starting: bool, ending: bool, id: int, data: bytes):
    code = 0
    if starting:
        code += Code.FRAME_START.value
    if ending:
        code += Code.FRAME_END.value

    metadata = pack(">BH", code, id)

    return metadata + data


def decode_packet(packet: bytes):
    if packet[:1] == packet:
        code = decode_simple_packet(packet)
        return code, None, None

    code, id = unpack(">BH", packet[:3])
    data = packet[3:]
    return code, id, data


def encode_simple_packet(code: Code):
    return pack(">B", code.value)


def decode_simple_packet(packet: bytes):
    return unpack(">B", packet)[0]


def terminate(sock, address):
    print("Terminating...")
    sock.sendto(encode_simple_packet(Code.CONNECTION_END), address)


def initiate(sock, address):
    print("Initiating...")
    sock.sendto(encode_simple_packet(Code.CONNECTION_START), address)


def timeout(sock, address):
    print("Timeout...")
    sock.sendto(encode_simple_packet(Code.CONNECTION_TIMEOUT), address)


def kill_server(sock, address):
    print("Killing server...")
    sock.sendto(encode_simple_packet(Code.SERVER_KILL), address)


def request_frame(sock, address):
    print("Requesting frame...")
    sock.sendto(encode_simple_packet(Code.REQUEST_FRAME), address)


def request_stream_start(sock, address):
    print("Requesting stream start...")
    sock.sendto(encode_simple_packet(Code.REQUEST_STREAM_START), address)


def request_stream_start(sock, address):
    print("Requesting stream stop...")
    sock.sendto(encode_simple_packet(Code.REQUEST_STREAM_STOP), address)


def frame_starting(code: int):
    return code == Code.FRAME_START.value or code == Code.FRAME_SOLO.value


def frame_ending(code: int):
    return code == Code.FRAME_END.value or code == Code.FRAME_SOLO.value


def connection_starting(code: int):
    return code == Code.CONNECTION_START.value


def connection_ending(code: int):
    return code == Code.CONNECTION_END.value


def connection_timedout(code: int):
    return code == Code.CONNECTION_TIMEOUT.value


def server_kill_triggered(code: int):
    return code == Code.SERVER_KILL.value


def frame_requested(code: int):
    return code == Code.REQUEST_FRAME


def stream_start_requested(code: int):
    return code == Code.REQUEST_STREAM_START


def stream_stop_requested(code: int):
    return code == Code.REQUEST_STREAM_STOP


def package_data(data: bytes):
    packets = []
    id = 0

    while len(data) > 0:
        curr_packet = encode_packet(
            id == 0, len(data) <= DATA_SIZE, id, data[:DATA_SIZE]
        )
        packets.append(curr_packet)

        data = data[DATA_SIZE:]
        id += 1

    return packets


def package_image(image: ndarray):
    image_data = BytesIO()
    save(image_data, image, allow_pickle=True)

    image_data.seek(0)
    image_data = image_data.read()
    return package_data(image_data)


def unpack_data(packets: dict):
    image_bytes = b"".join([packet[1] for packet in packets])
    image_bytes_obj = BytesIO(image_bytes)
    image = load(image_bytes_obj, allow_pickle=True)
    return image
