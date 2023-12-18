from struct import pack, unpack
from Consts import *
from enum import Enum
from numpy import save, load, ndarray
from io import BytesIO

CODE_SIZE = 1
METADATA_SIZE = 3
DATA_SIZE = PACK_SIZE - METADATA_SIZE


class Code(Enum):
    #serverside
    FRAME_START = 1
    FRAME_END = 2
    FRAME_SOLO = 3
    
    #universal
    CONNECTION_END = 4 
    NORMAL = 0

    #clientside
    CONNECTION_START = 5

def encode_packet(starting : bool, ending : bool, id : int, data : bytes):
    code = 0
    if starting:
        code += Code.FRAME_START.value
    if ending:
        code += Code.FRAME_END.value

    metadata = pack(">BH", code, id)

    return metadata + data
def decode_packet(packet : bytes):

    if packet[:1] == packet:
        return decode_simple_packet(packet), None, None

    code, id = unpack(">BH", packet[:3])
    data = packet[3:]
    return code, id, data

def encode_simple_packet(code : Code):
    return pack(">B", code)
def decode_simple_packet(packet : bytes):
    return unpack(">B", packet)


def terminate(sock, address):
    print("Terminating...")
    sock.sendto(encode_simple_packet(Code.CONNECTION_END), address)
def initiate(sock, address):
    print("Initiating...")
    sock.sendto(encode_simple_packet(Code.CONNECTION_START), address)


def frame_starting(code : int):
    return code == Code.FRAME_START.value or code == Code.FRAME_SOLO.value
def frame_ending(code : int):
    return code == Code.FRAME_END.value or code == Code.FRAME_SOLO.value
def connection_starting(code : int):
    return code == Code.CONNECTION_START.value
def connection_ending(code : int):
    return code == Code.CONNECTION_END.value

def package_data(data : bytes):
    packets = []
    id = 0

    while len(data) > 0:
        curr_packet = encode_packet(id == 0, len(data) <= DATA_SIZE, id, data[:DATA_SIZE])
        packets.append(curr_packet)

        data = data[DATA_SIZE:]
        id += 1

    return packets

def package_image(image : ndarray):
    image_data = BytesIO()
    save(image_data, image, allow_pickle=True)

    image_data.seek(0)
    image_data = image_data.read()
    return package_data(image_data)