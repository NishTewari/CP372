"""
    ~~~~~~~~~
    CLIENT.PY
    ~~~~~~~~~

    UDP and TCP Networking
    CP 372 -> Assignment 1
    
    @author Kelvin Kellner (190668940) - https://github.com/kelvinkellner
    @author Nishant Tewari (190684430) - https://github.com/XSilviaX

    @see https://github.com/XSilviaX/CP372
    ---------------------------------------------------------------------
    Files:
        client.py
        server.py
    ---------------------------------------------------------------------
    Program runs through 4 phases:
        Phase A: sending a single packet using UDP
        Phase B: sending multiple packets using UDP
        Phase C: connecting to TCP server and receiving a packet
        Phase D: sending multiple packets using TCP
    ---------------------------------------------------------------------
"""

# Imports
import socket
import struct
import sys
import time

# Constants
SERVER_HOST = 'localhost' # 'localhost' or '34.69.60.253'
SERVER_PORT = 12000


class Client:
    byte_alignment = 4 # adds empty bytes to the end of the packet to make it a multiple of 4
    entity = 1 # client is always 1, server is always 2
    timeout = 0.5 # seconds

    def __init__(self, serverHost, serverPort, code = 0):
        self.serverHost = serverHost
        # Assign a port number
        self.serverPort = serverPort
        self.code = code
    
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
            data = data + '\0' * (4 - len(data) % 4)
        data_len = len(data)

        # generate packet
        header = struct.pack("!IHH", data_len, self.code, Client.entity)
        packet = header + data.encode('utf-8')

        # send packet
        self.clientSocket.sendto(packet, (self.serverHost, self.serverPort))
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)

        # unpack and return response from server
        data_len, code, entity = struct.unpack("!IHH", response_packet[:8])
        repeat, udp_port, lenA, codeA = struct.unpack("!IIHH", response_packet[8:20])
        print(f'Received packet from server: data_len: {data_len}  pcode: {code}  entity: {entity}  repeat: {repeat}  len: {lenA}  udp_port: {udp_port}  codeA: {codeA}')
        return repeat, udp_port, lenA, codeA

    # For Phase B - sends multiple packets to UDP server
    def send_repeat_udp_data(self, repeat, data):
        self.clientSocket.settimeout(Client.timeout)
        time.sleep(Client.timeout) # give server time to start listening
        # send packet repeat-many times
        for i in range(repeat):
            # maintain divisible by 4 rule
            if len(data) % 4 > 0:
                data = data + '\0' * (4 - len(data) % 4)
            data_len = 4 + len(data)

            # generate packet
            header = struct.pack("!IHHI", data_len, self.code, Client.entity, i)
            packet = header + data.encode('utf-8')

            # send packet until acknowledged
            acknowledged = False
            while not acknowledged:
                try:
                    self.clientSocket.sendto(packet, (self.serverHost, self.serverPort))
                    ack_packet, serverAddress = self.clientSocket.recvfrom(2048)
                    data_len, code, entity, ack_packet_id = struct.unpack("!IHHI", ack_packet[:12])
                    acknowledged = True # ack_packet_id == i
                    if acknowledged:
                        print(f'Received acknowledgement packet from server: data_len:  {data_len} pcode:  {code} entity:  {entity} acknumber:  {ack_packet_id}')
                    else:
                        print(f'Server acknowledged packet {ack_packet_id} instead of {i}')
                except socket.timeout:
                    print("CLIENT: Did not receive ack from server, sending packet {} again".format(i))
        # unpack server response
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)
        data_len, code, entity, tcp_port, codeB = struct.unpack("!IHHII", response_packet)
        print(f'Received final packet: data_len:  {data_len} pcode:  {code} entity: {entity}  tcp_port: {tcp_port}  codeB: {codeB}')
        return tcp_port, codeB

    # For Phase C - connect to TCP server and receive a packet
    def receive_tcp_data(self):
        # receive packet
        response_packet, serverAddress = self.clientSocket.recvfrom(2048)
        # unpack and return response from server
        data_len, code, entity = struct.unpack("!IHH", response_packet[:8])
        repeat, lenC, codeC, ord_char = struct.unpack("!IHHB", response_packet[8:17])
        char = chr(ord_char)
        print(f'Received packet from server: data_len: {data_len}  pcode: {code}   entity: {entity}   repeat2: {repeat}   len2: {lenC}   codeC: {codeC}   char:  {char}')
        return repeat, lenC, codeC, char

    # For Phase D - send repeat messages to TCP server
    def send_repeat_tcp_data(self, repeat, char, lenC):
        # maintain divisible by 4 rule
        data = char * (lenC + (4 - lenC % 4))
        data_len = len(data)
        # generate packet
        header = struct.pack("!IHH", data_len, self.code, Client.entity)
        packet = header + data.encode('utf-8')
        print(f'Sending {data} to server {repeat} times')
        # send packet repeat-many times
        for _ in range(repeat):
            self.clientSocket.sendall(packet)
        response_packet = self.clientSocket.recv(1024)
        data_len, code, entity, codeD = struct.unpack("!IHHI", response_packet[:12])
        print(f'Received from server: data_len: {data_len}  pcode: {code}  entity: {entity}  codeD: {codeD}')
        return codeD



def main():

    # Phase A - Send message via UDP Server
    print('\n------------ Starting Phase A ------------\n')

    client = Client(SERVER_HOST, SERVER_PORT)

    client.connect_udp_client()

    message = "Hello World!!!"
    repeat, udp_port, lenA, codeA = client.send_udp_data(message)

    print('\n------------  End of Phase A  ------------\n')


    # Phase B - Send repeat messages to new UDP Port
    print('\n------------ Starting Phase B ------------\n')

    client.set_code(codeA)
    client.set_port(udp_port)
    client.connect_udp_client()
    print(f'CLIENT: Client ready on the new UDP port: {udp_port}')

    time.sleep(Client.timeout) # give server time to switch ports

    tcp_port, codeB = client.send_repeat_udp_data(repeat, '0' * lenA)

    print('\n------------  End of Phase B  ------------\n')


    # Phase C - Connect to TCP Server and receive message
    print('\n------------ Starting Phase C ------------\n')

    client.set_code(codeB)
    client.set_port(tcp_port)
    client.connect_tcp_client()
    print(f'CLIENT: Client ready on the TCP port: {tcp_port}')

    time.sleep(Client.timeout) # give server time to start listening

    repeat, lenC, codeC, char = client.receive_tcp_data()

    print('\n------------  End of Phase C  ------------\n')


    # Phase D - Send repeat messages to TCP Port
    print('\n------------ Starting Phase D ------------\n')

    client.set_code(codeC)

    codeD = client.send_repeat_tcp_data(repeat, char, lenC)

    print('\n------------  End of Phase D  ------------\n')


    # Teardown

    client.close_client()
    sys.exit()  # Terminate the program when finished

# Run program if the file is being run directly
if __name__ == "__main__":
    main()