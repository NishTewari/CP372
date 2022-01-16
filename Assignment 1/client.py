# Import socket module
import socket
import sys # In order to terminate the program

class Client:
    def __init__(self, serverHost, serverPort):
        self.serverHost = serverHost
        # Assign a port number
        self.serverPort = serverPort

    def connect_udp_client(self):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect the socket to server address and server port
        self.clientSocket.connect((self.serverHost, self.serverPort))

    def close_client(self):
        self.clientSocket.close()
        

    def send_message(self, message):
        self.clientSocket.sendto(message.encode(), (self.serverHost, self.serverPort))
        modifiedSentence, serverAddress = self.clientSocket.recvfrom(2048)

        print('From server: ', modifiedSentence.decode())




# Phase A - connect with UDP Server

client = Client('localhost', 12000)

client.connect_udp_client()

message = input('Input lower case sentence: ')
client.send_message(message)

client.close_client()

sys.exit() #Terminate the program after sending the corresponding data




