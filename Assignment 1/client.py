# Imports
import socket
import struct
import sys
import time


class Client:
    byte_alignment = 4 # adds empty bytes to the end of the packet to make it a multiple of 4
    entity = 1 # client is always 1, server is always 2
    timeout = 0.5 # seconds

    def __init__(self, serverHost, serverPort, clientCode):
        self.serverHost = serverHost
        # Assign a port number
        self.serverPort = serverPort
        self.code = clientCode
    
    def set_port(self, serverPort):
        self.serverPort = serverPort

    def set_code(self, code):
        self.code = code

    def connect_udp_client(self):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect the socket to server address and server port
        self.clientSocket.connect((self.serverHost, self.serverPort))

    def connect_tcp_client(self):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to server address and server port
        self.clientSocket.connect((self.serverHost, self.serverPort))

    def close_client(self):
        self.clientSocket.close()

    # For Phase A - sends a single packet to UDP server
    def send_udp_data(self, data):
        # maintain divisible by 4 rule
        if len(data) % 4 > 0:
            data = data + '0' * (4 - len(data) % 4)
        data_len = len(data)

        # generate packet
        header = struct.pack("IHH", data_len, self.code, Client.entity)
        packet = header + data.encode('utf-8')

        # send packet
        self.clientSocket.sendto(packet, (self.serverHost, self.serverPort))
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)

        # unpack and return response from server
        header = struct.unpack("IHH", response_packet[:8])
        repeat, udp_port, lenA, codeA = struct.unpack("IIHH", response_packet[8:20])
        return repeat, udp_port, lenA, codeA

    # For Phase B - sends multiple packets to UDP server
    def send_repeat_udp_data(self, repeat, data):
        self.clientSocket.settimeout(Client.timeout)
        # maintain divisible by 4 rule
        if len(data) % 4 > 0:
            data = data + '0' * (4 - len(data) % 4)
        data_len = 4 + len(data)
        # send packet repeat-many times
        for i in range(repeat):

            # generate packet
            header = struct.pack("IHHI", data_len, self.code, Client.entity, i)
            packet = header + data.encode('utf-8')

            # send packet until acknowledged
            acknowledged = False
            while not acknowledged:
                try:
                    self.clientSocket.sendto(packet, (self.serverHost, self.serverPort))
                    ack_packet, serverAddress = self.clientSocket.recvfrom(2048)
                    ack_header = struct.unpack("IHH", ack_packet[:8])
                    ack_data = struct.unpack("I", ack_packet[8:12])
                    ack_packet_id = ack_data[0]
                    acknowledged = ack_packet_id == i
                    if not acknowledged:
                        print('Server acknowledged packet {} instead of {}'.format(ack_packet_id, i))
                except socket.timeout as ex:
                    print("{} : Did not receive ack from server, sending packet {} again".format(ex, i))
                    pass
        print('All packets sent and acknowledged')
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)
        tcp_port, codeB = struct.unpack("IH", response_packet[8:14])
        return tcp_port, codeB

    # For Phase C - connect to TCP server and receive a packet
    def receive_tcp_data(self):
        # receive packet
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)
        # unpack and return response from server
        header = struct.unpack("IHH", response_packet[:8])
        repeat, lenC, codeC, ord_char = struct.unpack("IHHB", response_packet[8:17])
        char = chr(ord_char)
        return repeat, lenC, codeC, char

    # For Phase D - send repeat messages to TCP server
    def send_repeat_tcp_data(self, repeat, data):
        # TODO: CONFIRM THIS IS REQUIRED HERE
        # maintain divisible by 4 rule
        if len(data) % 4 > 0:
            data = data + '0' * (4 - len(data) % 4)
        data_len = len(data)
        # generate packet
        header = struct.pack("IHH", data_len, self.code, Client.entity)
        packet = header + data.encode('utf-8')
        # send packet repeat-many times
        for i in range(repeat):
            # TODO: Confirm acknowledgement is NOT required here
            # send packet until acknowledged
            self.clientSocket.sendall(packet)
            time.sleep(0.05) # TODO: Does this make more sense than ack?
        print('All packets sent')
        response_packet = self.clientSocket.recv(2048)
        header = struct.unpack("H", response_packet[8:10])
        codeD = header[0]
        return codeD



def main():

    # Phase A - Send message via UDP Server

    client = Client('localhost', 12000, 0)

    client.connect_udp_client()

    message = "Hello World!!!"
    repeat, udp_port, lenA, codeA = client.send_udp_data(message)
    print('From server: ', repeat, udp_port, lenA, codeA)

    # Phase B - Send repeat messages to new UDP Port

    client.set_code(codeA)
    client.set_port(udp_port)
    client.connect_udp_client()

    tcp_port, codeB = client.send_repeat_udp_data(repeat, '0' * lenA)
    print('From server: ', tcp_port, codeB)

    # Phase C - Connect to TCP Server and receive message

    client.set_code(codeB)
    client.set_port(tcp_port)
    client.connect_tcp_client()

    time.sleep(2) # give server time to start listening

    repeat, lenC, codeC, char = client.receive_tcp_data()

    # Phase D - Send repeat messages to TCP Port

    client.set_code(codeC)

    codeD = client.send_repeat_tcp_data(repeat, char * lenC)
    print('From server: ', codeD)

    # Teardown

    client.close_client()

    sys.exit()  # Terminate the program when finished

# Run program if the file is being run directly
if __name__ == "__main__":
    main()