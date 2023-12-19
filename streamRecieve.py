
# This is client code to receive video frames over UDP
import cv2, socket
from struct import unpack

import Consts
import Protocol

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, Consts.PACK_SIZE * Consts.BUFFER_PACKETS)
client_socket.settimeout(2)

host_ip = "172.17.17.120"
port = 9999
server_address = (host_ip, port)

Protocol.initiate(client_socket, server_address)

image_data = {}

connected = True
try:
    while connected:
        try:
            packet = client_socket.recvfrom(Consts.PACK_SIZE)[0]
        except TimeoutError:
            print("Timeout")
            Protocol.initiate(client_socket, server_address)
            continue

        #client_socket.sendto(Protocol.encode_simple_packet(Protocol.Code.NORMAL), server_address)


        code, id, data = Protocol.decode_packet(packet)

        if Protocol.connection_ending(code):
            print("Server connection terminated, killing client...")
            break
        elif Protocol.frame_starting(code):
            image_data = {}
        elif Protocol.connection_timedout(code):
            Protocol.initiate(client_socket, server_address)
            continue
        elif len(image_data) == 0:
            continue

        image_data[id] = data

        if not Protocol.frame_ending(code):
            continue
        
        try:
            image_data = sorted(image_data.items())
        except AttributeError:
            print("An unknown bug occurred receiving the current frame")
            continue

        if image_data[-1][0] + 1 > len(image_data):
            print("Lost packet, skipping frame")
            image_data = {}
            #NOTE: THIS IS WHERE RESENDING CODE WOULD GO
            #ASK FOR SPECIFIC PACKETS ENCODED SOMEHOW
            continue

        encoded_image = Protocol.unpack_data(image_data)
        image = cv2.imdecode(encoded_image, 1)
        cv2.imshow("RECEIVING VIDEO", image)
        

        #print(id)

        client_socket.sendto(Protocol.encode_simple_packet(Protocol.Code.NORMAL), server_address)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            connected = False
        elif key == ord('k'):
            Protocol.kill_server(client_socket, server_address)
            connected = False

except KeyboardInterrupt:
    pass

Protocol.terminate(client_socket, server_address)
client_socket.close()
