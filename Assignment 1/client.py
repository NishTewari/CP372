# Import socket module
import socket
import struct
import sys  # In order to terminate the program


class Client:
    byte_alignment = 4
    entity = 1
    timeout = 0.5 # seconds

    def __init__(self, serverHost, serverPort):
        self.serverHost = serverHost
        # Assign a port number
        self.serverPort = serverPort
        self.code = 0
    
    def set_port(self, serverPort):
        self.serverPort = serverPort

    def set_code(self, code):
        self.code = code

    def connect_udp_client(self):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect the socket to server address and server port
        self.clientSocket.connect((self.serverHost, self.serverPort))

    def close_client(self):
        self.clientSocket.close()

    def send_data(self, data):
        # generate packet
        header = struct.pack("IHH", len(data), self.code, Client.entity)
        packet = header + data.encode('utf-8')

        # maintain divisible by 4 rule
        while len(packet) % 4 > 0:
            packet = packet + '0'.encode('utf-8')

        # send packet
        self.clientSocket.sendto(packet, (self.serverHost, self.serverPort))
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)

        # unpack and return response from server
        header = struct.unpack("IHH", response_packet[:8])
        data = struct.unpack("IIHH", response_packet[8:20])
        repeat = data[0]
        udp_port = data[1]
        lenA = data[2]
        codeA = data[3]
        return repeat, udp_port, lenA, codeA

    def send_repeat_data(self, repeat, data):
        # send packet repeat-many times
        for i in range(repeat):
            # generate packet
            header = struct.pack("IHHI", len(message) + 4, self.code, Client.entity, i)
            packet = header + data.encode('utf-8')

            # maintain divisible by 4 rule
            while len(packet) % 4 > 0:
                packet = packet + '0'.encode('utf-8')

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
        data = struct.unpack("IH", response_packet[8:14])
        tcp_port = data[0]
        cobeB = data[1]
        return tcp_port, cobeB



# Phase A - Send message via UDP Server

client = Client('localhost', 12000)

client.connect_udp_client()

message = "Hello World!!!"
repeat, udp_port, lenA, codeA = client.send_data(message)
print('From server: ', repeat, udp_port, lenA, codeA)

# Phase B - Send repeat messages to new UDP Port

client.set_code(codeA)
client.set_port(udp_port)
client.connect_udp_client()

tcp_port, codeB = client.send_repeat_data(repeat, '0000')
print('From server: ', tcp_port, codeB)

# Teardown

client.close_client()

sys.exit()  # Terminate the program when finished
