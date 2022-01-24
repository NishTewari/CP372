# Imports
from random import randint
import socket
import struct
import sys


class Server:
    byte_alignment = 4 # adds empty bytes to the end of the packet to make it a multiple of 4
    entity = 2 # client is always 1, server is always 2
    timeout = 3 # seconds

    def __init__(self, serverHost, serverPort):
        # Assign a port number
        self.serverHost = serverHost
        self.serverPort = serverPort

    def set_port(self, serverPort):
        self.serverPort = serverPort

    def bind_udp_server(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to server address and server port
        self.serverSocket.bind((self.serverHost, self.serverPort))

    def close_server(self):
        self.serverSocket.close()

    def unpack_client_packet(self):
        # unpack data from the client
        packet, clientAddress = self.serverSocket.recvfrom(1024)
        len_data, code = struct.unpack("IHH", packet[:8])
        data = packet[8:8+len_data].decode()
        print('From client {} : {}'.format(clientAddress[1], data))
        return len_data, code, data, clientAddress

    def unpack_client_ordered_packet(self):
        # unpack data from client
        packet, clientAddress = self.serverSocket.recvfrom(1024)
        len_data, code = struct.unpack("IHH", packet[:8])
        packet_id = struct.unpack("I", packet[8:12])[0]
        data = packet[12:12+len_data-4].decode()
        print('From client {} : {}'.format(clientAddress[1], data))
        return len_data, code, data, clientAddress, packet_id

    def send_ack_packet(self, len_data, code, clientAddress, packet_id):
        # generate ack packet
        ack_packet = struct.pack("IHHI", len_data, code, Server.entity, packet_id)
        self.serverSocket.sendto(ack_packet, clientAddress)
        return

    # For Phase A - Recieve single client packet
    def recieve_udp_data(self):
        repeat = None
        udp_port = None
        active = True
        self.serverSocket.settimeout(Server.timeout)
        while active:
            try:
                len_data, code, data, clientAddress = self.unpack_client_packet()
                # generate response packet
                repeat = randint(5, 20)
                udp_port = randint(20000, 30000)
                lenA = randint(50, 100)
                codeA = randint(100, 400)
                len_data = 4+4+2+2
                response_packet = struct.pack("IHHIIHH", len_data, code, Server.entity, repeat, udp_port, lenA, codeA)
                # send response packet
                self.serverSocket.sendto(response_packet, clientAddress)
                active = False
            except socket.timeout as ex:
                print(ex, ': no connections after 3 seconds')
                self.close_server()
                active = False
        return repeat, udp_port

    # For Phase B - Recieve repeat client packets and send ack packet each time
    def listen_udp_data(self, repeat):
        active = True
        self.serverSocket.settimeout(Server.timeout)
        i = 0
        while i < repeat:
            len_data, code, data, clientAddress, packet_id = self.unpack_client_ordered_packet()
            self.send_ack_packet(len_data, code, clientAddress, packet_id)
            i += 1
        print('All packets recieved and acknowledged')
        # generate response packet
        tcp_port = randint(20000, 30000)
        cobeB = randint(100, 400)
        len_data = 4+2
        response_packet = struct.pack("IHHIH", len_data, code, Server.entity, tcp_port, cobeB)
        # send response packet
        self.serverSocket.sendto(response_packet, clientAddress)
        return tcp_port



# Phase A - Receive client message via UDP Server

server = Server('localhost', 12000)
server.bind_udp_server()

repeat, udp_port = server.recieve_udp_data()
# udp_port is None if server timed out
if udp_port is None:
    sys.exit()

# Phase B - Send receive repeat messages from client on new UDP Port

server.set_port(udp_port)
server.bind_udp_server()

tcp_port = server.listen_udp_data(repeat)

# Teardown

server.close_server()

sys.exit()  # Terminate the program when finished
