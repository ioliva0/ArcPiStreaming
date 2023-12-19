import Server

server_socket, camera = Server.init()

listening = True

while listening:
    client_addr = Server.wait_for_connection(server_socket)
    connection = (server_socket, client_addr)
    connected = True
    
    try:
        while connected:
            Server.send_image(camera, *connection)
            listening, connected = Server.listen(*connection)
    except KeyboardInterrupt:
        pass

server_socket.close()