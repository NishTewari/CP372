# Import socket module
import socket 
import sys # In order to terminate the program
from time import time # For server deactivate conditions

class Server:
    def __init__(self, serverHost, serverPort):
        # Assign a port number
        self.serverHost = serverHost
        self.serverPort = serverPort
    
    def bind_udp_server(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to server address and server port
        self.serverSocket.bind((self.serverHost, self.serverPort))

    def close_server(self):
        self.serverSocket.close()

    def activate_udp_server(self):
        active = True
        self.serverSocket.settimeout(3)
        while active:
            try:
                message, clientAddress = self.serverSocket.recvfrom(1024)
                capitalizedMessage = message.decode().upper()
                self.serverSocket.sendto(capitalizedMessage.encode(), clientAddress)
                print('From client {} : {}'.format(clientAddress[1], message.encode()))
            except socket.timeout as ex:
                print(ex, ': no connections after 3 seconds')
                self.close_server()
                active = False


    

    # def await_client_connection(self):
    #     # Set server no-packet timeout to 3 seconds
    #     self.serverSocket.settimeout(60)
    #     # Wait 60 seconds to allow clients to connect
    #     self.serverSocket.listen(60)

    #     while 1:
    #         try:
    #             connection, clientAddress = self.serverSocket.accept()
    #             message = connection.recv(1024)
    #             capitalizedMessage = message.decode().upper()
    #             self.serverSocket.sendto(capitalizedMessage.encode(), clientAddress)
    #         except socket.timeout as e:
    #             print(e, ': no connections after 3 seconds')
    #             self.close_socket_connection()
    #             break
    #         print('Client connected: ' + clientAddress[0] + ':' + clientAddress[1])


    # def activate_client_to_server_connection(self):
    #     active = True
    #     condition = 'None provided'

    #     print('Server is now active. Awaiting messages from clients.')
    #     lastAction = time()
    #     while active:
    #         print(time(), lastAction, time() - lastAction)
    #         if time() - lastAction > 3:
    #             active = False
    #             condition = 'The server did not receive any packet from the client for 3 seconds'
    #         else:
    #             message, clientAddress = self.serverSocket.recvfrom(1024)
    #             capitalizedMessage = message.decode().upper()
    #             self.serverSocket.sendto(capitalizedMessage.encode(), clientAddress)
    #     print('Server has been deactived due to the following condition:\n{}'.format(condition))



server = Server('localhost', 12000)
server.bind_udp_server()

server.activate_udp_server()

server.close_server()

sys.exit() #Terminate the program after sending the corresponding data
