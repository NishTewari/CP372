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
        self.serverHost = serverHost
        # Assign a port number
        self.serverPort = serverPort
        self.code = 0

    def set_port(self, serverPort):
        self.serverPort = serverPort

    def set_code(self, code):
        self.code = code

    def bind_udp_server(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to server address and server port
        self.serverSocket.bind((self.serverHost, self.serverPort))

    def bind_tcp_server(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to server address and server port
        self.serverSocket.bind((self.serverHost, self.serverPort))

    def close_server(self):
        self.serverSocket.close()

    def check_protocol_deviation(self, attr_name, true_value, expected_value):
        if expected_value != true_value:
            print("\nProtocol deviation detected:\n'{}': received {}, expected {}".format(attr_name, expected_value, true_value))
            print("\nQuitting program...")
            self.close_server()
            sys.exit()

    def check_default_deviations(self, data_len, data, code, entity):
        # check for protocol deviations
        self.check_protocol_deviation("data_len divisible by 4", data_len % 4 == 0, True)
        self.check_protocol_deviation("len(data) is true to data_len", len(data), data_len)
        self.check_protocol_deviation("correct code", code, self.code)
        self.check_protocol_deviation("correct entity", entity, 1)

    def unpack_client_packet(self):
        # unpack data from the client
        packet, clientAddress = self.serverSocket.recvfrom(1024)
        data_len, code, entity = struct.unpack("IHH", packet[:8])
        data = packet[8:8+data_len].decode()
        print('From client {} : {}'.format(clientAddress[1], data))
        return data_len, code, entity, data, clientAddress

    def unpack_client_ordered_packet(self):
        # unpack data from client
        packet, clientAddress = self.serverSocket.recvfrom(1024)
        data_len, code, entity = struct.unpack("IHH", packet[:8])
        packet_id = struct.unpack("I", packet[8:12])[0]
        data = packet[12:12+data_len-4].decode()
        print('From client {} : {}'.format(clientAddress[1], data))
        return data_len, code, entity, data, clientAddress, packet_id

    def send_ack_packet(self, data_len, code, clientAddress, packet_id):
        # generate ack packet
        ack_packet = struct.pack("IHHI", data_len, code, Server.entity, packet_id)
        self.serverSocket.sendto(ack_packet, clientAddress)
        return

    # For Phase A - Receive single client packet using UDP
    def receive_udp_data(self):
        repeat = None
        udp_port = None
        codeA = None
        active = True
        self.serverSocket.settimeout(Server.timeout)
        while active:
            try:
                data_len, code, entity, data, clientAddress = self.unpack_client_packet()
                # check for protocol deviations
                self.check_default_deviations(data_len, data, code, entity)
                # generate response packet
                data_len = 4+4+2+2
                repeat = randint(5, 20)
                udp_port = randint(20000, 30000)
                lenA = randint(50, 100)
                codeA = randint(100, 400)
                response_packet = struct.pack("IHHIIHH", data_len, self.code, Server.entity, repeat, udp_port, lenA, codeA)
                # send response packet
                self.serverSocket.sendto(response_packet, clientAddress)
                active = False
            except socket.timeout as ex:
                print(ex, ': no connections after 3 seconds')
                self.close_server()
                active = False
        return repeat, udp_port, codeA

    # For Phase B - Receive repeat client packets using UDP and send ack packet each time
    def listen_udp_data(self, repeat):
        self.serverSocket.settimeout(Server.timeout)
        i = 0
        while i < repeat:
            data_len, code, entity, data, clientAddress, packet_id = self.unpack_client_ordered_packet()
            # check for protocol deviations
            self.check_default_deviations(data_len-4, data, code, entity)
            self.send_ack_packet(data_len, self.code, clientAddress, packet_id)
            i = packet_id+1
        print('All packets received and acknowledged')
        # generate response packet
        data_len = 4+2
        tcp_port = randint(20000, 30000)
        codeB = randint(100, 400)
        response_packet = struct.pack("IHHIH", data_len, self.code, Server.entity, tcp_port, codeB)
        # send response packet
        self.serverSocket.sendto(response_packet, clientAddress)
        return tcp_port, codeB

    # For Phase C - Send single packet to client using TCP
    def send_tcp_data(self):
        self.serverSocket.listen(20)
        # TODO: multi-threaded clients - simply send the packet on a new thread and return there instead of here
        # await a client connection
        active = True
        while active:
            connection, clientAddress = self.serverSocket.accept()
            print('Connected to client {}'.format(clientAddress[1]))
            # send data to client
            data_len = 4+2+2+1
            repeat = randint(5, 20)
            lenC = randint(50, 100)
            codeC = randint(100, 400)
            char = 'A'
            packet = struct.pack("IHHIHHB", data_len, self.code, Server.entity, repeat, lenC, codeC, ord(char))
            connection.sendall(packet)
            return connection, clientAddress, repeat, lenC * char, codeC

    # For Phase D - Receive repeat client packets using TCP
    def listen_tcp_data(self, connection, clientAddress, repeat, expected_data):
        # receive data from client
        i = 0
        while i < repeat:
            data = connection.recv(1024)
            data_len, code, entity = struct.unpack("IHH", data[:8])
            data = data[8:8+data_len].decode()
            # check for protocol deviations
            self.check_default_deviations(data_len, data, code, entity)
            print('From client {} : {}'.format(clientAddress[1], data))
            i += 1
        print('All packets received')
        # generate response packet
        data_len = 2+2
        codeD = randint(100, 400)
        response_packet = struct.pack("IHHI", data_len, self.code, Server.entity, codeD)
        # send response packet
        connection.sendall(response_packet)
        return codeD



def main():

    # Phase A - Receive client message via UDP Server

    server = Server('localhost', 12000)
    server.bind_udp_server()

    repeat, udp_port, codeA = server.receive_udp_data()
    # udp_port is None if server timed out
    if udp_port is None:
        print("Quitting program...")
        sys.exit()

    # Phase B - Receive repeat messages from client on new UDP Port

    server.set_port(udp_port)
    server.set_code(codeA)
    server.bind_udp_server()

    tcp_port, codeB = server.listen_udp_data(repeat)

    # Phase C - Send client a message via TCP Server

    server.set_port(tcp_port)
    server.set_code(codeB)
    server.bind_tcp_server()

    connection, clientAddress, repeat, data, codeC = server.send_tcp_data()

    # Phase D - Receive repeat messages from client via TCP Server

    server.set_code(codeC)
    codeD = server.listen_tcp_data(connection, clientAddress, repeat, data)

    # Teardown

    server.close_server()

    sys.exit()  # Terminate the program when finished

# Run program if the file is being run directly
if __name__ == "__main__":
    main()