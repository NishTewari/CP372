"""
    ~~~~~~~~~
    sender.py
    ~~~~~~~~~

    CP 372 -> Assignment 2
    Reliable one-way messaging protocol (RDT) for an unreliable network.
    
    @author Kelvin Kellner (190668940) - https://github.com/kelvinkellner
    @author Nishant Tewari (190684430) - https://github.com/XSilviaX
    @see https://github.com/XSilviaX/CP372
    
    ---------------------------------------------------------------------
"""

from common import *

class sender:
    RTT = 20
    
    def isCorrupted (self, packet):
        '''Checks if a received packet (acknowledgement) has been corrupted
        during transmission.
        Return true if computed checksum is different than packet checksum.
        '''
        corrupted = packet.checksum != checksumCalc(packet.payload + str(packet.seqNum) + str(packet.ackNum))
        return corrupted

    def isDuplicate(self, packet):
        '''checks if an acknowledgement packet is duplicate or not
        similar to the corresponding function in receiver side
        '''
        duplicate = packet.seqNum != self.sequenceNumber
        return duplicate
 
    def getNextSeqNum(self):
        '''generate the next sequence number to be used.
        '''
        return (self.sequenceNumber + 1) % 2

    def __init__(self, entityName, ns):
        self.entity = entityName
        self.networkSimulator = ns
        print("Initializing sender: A: "+str(self.entity))

    def init(self):
        '''initialize the sequence number and the packet in transit.
        Initially there is no packet is transit and it should be set to None
        '''
        self.sequenceNumber = 0
        self.packetInTransit = None
        return

    def timerInterrupt(self):
        '''This function implements what the sender does in case of timer
        interrupt event.
        This function sends the packet again, restarts the time, and sets
        the timeout to be twice the RTT.
        You never call this function. It is called by the simulator.
        '''
        self.networkSimulator.startTimer(self.entity, 2*self.RTT)
        self.networkSimulator.udtSend(self.entity, self.packetInTransit)
        return


    def output(self, message):
        '''prepare a packet and send the packet through the network layer
        by calling calling utdSend.
        It also start the timer.
        It must ignore the message if there is one packet in transit
        '''
        if self.packetInTransit is None:
            data = message.data
            checksum = checksumCalc(data + str(self.sequenceNumber) + str(self.sequenceNumber))
            packet = Packet(self.sequenceNumber, self.sequenceNumber, checksum, data)
            self.packetInTransit = packet
            self.networkSimulator.startTimer(self.entity, self.RTT)
            self.networkSimulator.udtSend(self.entity, packet)
        else:
            # print('> output: Packet in transit, cannot send another packet.')
            pass
        return
 
    
    def input(self, packet):

        '''If the acknowlegement packet isn't corrupted or duplicate, 
        transmission is complete. Therefore, indicate there is no packet
        in transition.
        The timer should be stopped, and sequence number  should be updated.

        In the case of duplicate or corrupt acknowlegement packet, it does 
        not do anything and the packet will be sent again since the
        timer will be expired and timerInterrupt will be called by the simulator.
        '''
        if self.isCorrupted(packet) or self.isDuplicate(packet):
            # print('> input: Packet received is corrupted or duplicate. Packet dropped.')
            pass
        else:
            self.networkSimulator.stopTimer(self.entity)
            self.sequenceNumber = self.getNextSeqNum()
            self.packetInTransit = None
            # print('> input: Received correct ack. Moving to next sequence number.')
        return 
