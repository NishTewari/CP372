"""
    ~~~~~~~~~
    SERVER.PY
    ~~~~~~~~~

    Multi-process server, waits for a client to connect on Port 12000.
    When client connects and finishes Phase A, the client and server
    switch ports and begin Phase B on a new Thread. A new server is
    created back on Port 12000 and waits for a client to connect.

    ---------------------------------------------------------------------
    
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
from random import randint
import socket
import struct
import sys
import threading
import time

# Constants
SERVER_HOST = 'localhost' # 'localhost'
SERVER_PORT = 12000


class Server:
    byte_alignment = 4 # adds empty bytes to the end of the packet to make it a multiple of 4
    entity = 2 # client is always 1, server is always 2
    timeout = 3 # seconds
    multiprocess_timeout = 30 # seconds

    def __init__(self, serverHost, serverPort, code = 0):
        self.serverHost = serverHost
        # Assign a port number
        self.serverPort = serverPort
        self.code = code

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
        # Allow reuse of the socket address without TIME_WAIT
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to server address and server port
        self.serverSocket.bind((self.serverHost, self.serverPort))

    def close_server(self):
        self.serverSocket.close()

    def check_protocol_deviation(self, attr_name, true_value, expected_value):
        if expected_value != true_value:
            print("\nProtocol deviation detected:\n'{}': received {}, expected {}".format(attr_name, true_value, expected_value))
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
        data_len, code, entity = struct.unpack("!IHH", packet[:8])
        data = packet[8:8+data_len].decode()
        # Lame spot for this print line, but it's the only way I can get the result I expect!
        print('\n------------ Starting Phase A ------------\n')
        print(f'Receiving from the client: data_length: {data_len}  code: {code}  entity: {entity} data: {data}')
        return data_len, code, entity, data, clientAddress

    def unpack_client_ordered_packet(self):
        # unpack data from client
        packet, clientAddress = self.serverSocket.recvfrom(1024)
        data_len, code, entity = struct.unpack("!IHH", packet[:8])
        packet_id = struct.unpack("!I", packet[8:12])[0]
        data = packet[12:12+data_len-4].decode()
        print(f'received_packet_id =  {packet_id} data_len =  {data_len}  pcode: {code}')
        return data_len, code, entity, data, clientAddress, packet_id

    def send_ack_packet(self, clientAddress, packet_id):
        # generate ack packet
        data_len = 4
        ack_packet = struct.pack("!IHHI", data_len, self.code, Server.entity, packet_id)
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
                response_packet = struct.pack("!IHHIIHH", data_len, self.code, Server.entity, repeat, udp_port, lenA, codeA)
                # send response packet
                print(f'\nSending to the client: data_length: {data_len}  code: {self.code}  entity: {Server.entity}  repeat: {repeat}  udp_port: {udp_port}  len: {lenA}  codeA: {codeA}')
                self.serverSocket.sendto(response_packet, clientAddress)
                active = False
            except socket.timeout as ex:
                # print('\nSERVER:', ex, ': no connections after 3 seconds')
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
            self.send_ack_packet(clientAddress, packet_id)
            i = packet_id+1
        # generate response packet
        data_len = 4+4
        tcp_port = randint(20000, 30000)
        codeB = randint(100, 400)
        response_packet = struct.pack("!IHHII", data_len, self.code, Server.entity, tcp_port, codeB)
        print(f' ------------- B2: sending tcp_port {tcp_port} codeB {codeB}')
        # send response packet
        self.serverSocket.sendto(response_packet, clientAddress)
        return tcp_port, codeB

    # For Phase C - Send single packet to client using TCP
    def send_tcp_data(self):
        self.serverSocket.listen(Server.timeout)
        # TODO: multi-threaded clients - simply send the packet on a new thread and return there instead of here
        # await a client connection
        active = True
        while active:
            connection, clientAddress = self.serverSocket.accept()
            print(f'SERVER: Connected to client {clientAddress[1]}')
            # send data to client
            data_len = 4+2+2+1
            repeat = randint(5, 20)
            lenC = randint(50, 100)
            codeC = randint(100, 400)
            char = chr(randint(65, 90)) # A - 65, Z - 90
            packet = struct.pack("!IHHIII", data_len, self.code, Server.entity, repeat, lenC, codeC)
            packet += char.encode('utf-8')
            print(f'Sending to the client: data_length: {data_len}  code: {self.code}  entity: {Server.entity}  repeat2: {repeat}  len2: {lenC}  char: {char}  codeC: {codeC}')
            connection.sendall(packet)
            return connection, clientAddress, repeat, char, codeC, lenC

    # For Phase D - Receive repeat client packets using TCP
    def listen_tcp_data(self, connection, clientAddress, repeat, lenC):
        self.serverSocket.settimeout(Server.timeout)
        print('SERVER: Starting to receive packets from client')
        active = True
        i = 0
        # receive data from client
        try:
            while active and i < repeat:
                # unpack packets
                packet = connection.recv(8 + lenC + (4 - lenC % 4 if lenC % 4 > 0 else 0))
                data_len, code, entity = struct.unpack("!IHH", packet[:8])
                data = packet[8:8+data_len].decode()
                # check for protocol deviations
                self.check_default_deviations(data_len, data, code, entity)
                print(f'i =  {i} data_len:  {data_len}  pcode: {code} entity: {entity} data:  {data}')
                i += 1
        except socket.timeout as ex:
            print(ex, ': no connections after 3 seconds')
        # generate response packet
        data_len = 2+2
        codeD = randint(100, 400)
        response_packet = struct.pack("!IHHI", data_len, self.code, Server.entity, codeD)
        # send response packet
        connection.sendall(response_packet)
        return codeD



def start():

    threads = []

    print(f'\n----------\nSERVER: Multi-process server started.\n----------')

    attempt = 0
    try:
        while attempt < (Server.multiprocess_timeout / Server.timeout):
            

            # Phase A - Receive client message via UDP Server

            server = Server(SERVER_HOST, SERVER_PORT)
            server.bind_udp_server()

            repeat, udp_port, codeA = server.receive_udp_data() # "Starting Phase A" printing happens at start of this call
            # udp_port is None if server timed out
            if udp_port is None:
                if attempt == 0:
                    print(f"\n----------\nWaiting up to {Server.multiprocess_timeout} seconds for a new client to connect...")
                    print("\tPress Ctrl+C (or Cmd+. on Mac) to quit program.\n----------")
                attempt += 1
                server.close_server()
                # print(f"Giving another chance for a new client to connect (attempt {attempt}/10)...")
            else:
                attempt = 0 # reset attempt counter


                # Phase B - Receive repeat messages from client on new UDP Port
                print('\n------------ Starting Phase B ------------\n')

                server.set_port(udp_port)
                server.set_code(codeA)
                server.bind_udp_server()
                print(f'SERVER: Server ready on the new UDP port: {udp_port}')
                
                # Create a new thread now that we have moved to a new port,
                # allowing an additional client to join on Port 12000.
                thread = threading.Thread(target=next, args=(server, repeat))
                threads.append(thread)
                print("\n----------\nSERVER: Client successfully connected. Moving to next section on new thread.")
                print("\tFeel free to connect another client to test multi-processing if you wish.\n----------\n")
                # Start the thread and finish Phase B
                thread.start()
        
        # If while loop is exceeded
        print("\nSERVER: Maximum new-client timeout reached. No new threads will be created.\n\tThe program will stop if/when all clients are finished.\n")

    # Allow Ctrl+C (or Ctrl+. on Mac) to exit the program without error
    except KeyboardInterrupt:
        pass

    finally:
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        # Kill the program
        sys.exit()

def next(server, repeat):

    tcp_port, codeB = server.listen_udp_data(repeat)


    # Phase C - Send client a message via TCP Server
    print('\n------------ Starting Phase C ------------\n')

    server.set_port(tcp_port)
    server.set_code(codeB)
    server.bind_tcp_server()
    print(f'SERVER: Server ready on the TCP port: {tcp_port}')

    connection, clientAddress, repeat, char, codeC, lenC = server.send_tcp_data()


    # Phase D - Receive repeat messages from client via TCP Server
    print('\n------------ Starting Phase D ------------\n')

    server.set_code(codeC)
    codeD = server.listen_tcp_data(connection, clientAddress, repeat, lenC)


    # Teardown

    server.close_server()
    sys.exit()  # Terminate the program when finished

# Run program if the file is being run directly
if __name__ == "__main__":
    start()