
# This is client code to receive video frames over UDP
import Client

connection = Client.init()

image_data = {}

connected = True
try:
    while connected:

        packet = Client.listen(*connection)

        frame_complete, image_data = Client.process_packet(image_data, *packet, *connection)

        if not frame_complete:
            continue
        
        image = Client.extract_image(image_data)

        Client.display(image, connection)

        Client.respond(*connection)

except KeyboardInterrupt:
    pass

Client.close(*connection)