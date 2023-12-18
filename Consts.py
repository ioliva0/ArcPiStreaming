from enum import Enum

class Code(Enum):
    NORMAL = 0
    FRAME_START = 1
    FRAME_END = 2
    FRAME_SOLO = 3
    CONNECTION_END = 4 

DATA_SIZE = 1000
PACK_SIZE = DATA_SIZE + 3