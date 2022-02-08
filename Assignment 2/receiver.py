"""
    ~~~~~~~~~
    receiver.py
    ~~~~~~~~~

    CP 372 -> Assignment 2
    Reliable one-way messaging protocol (RDT) for an unreliable network.
    
    @author Kelvin Kellner (190668940) - https://github.com/kelvinkellner
    @author Nishant Tewari (190684430) - https://github.com/XSilviaX
    @see https://github.com/XSilviaX/CP372
    
    ---------------------------------------------------------------------
"""

from common import *

class receiver:
    
    def isCorrupted(self, packet):
        ''' Checks if a received packet has been corrupted during transmission.
        Return true if computed checksum is different than packet checksum.'''
        corrupted = packet.checksum != checksumCalc(packet.payload + str(packet.seqNum) + str(packet.ackNum))
        return corrupted
   
    def isDuplicate(self, packet):
        '''checks if packet sequence number is the same as expected sequence number'''
        duplicate = packet.seqNum != self.expectedSequenceNumber
        return duplicate
    
    def getNextExpectedSeqNum(self):
        '''The expected sequence numbers are 0 or 1'''
        return (self.expectedSequenceNumber + 1) % 2
    
    
    def __init__(self, entityName, ns):
        self.entity = entityName
        self.networkSimulator = ns
        print("Initializing receiver: B: "+str(self.entity))


    def init(self):
        '''initialize expected sequence number'''
        self.expectedSequenceNumber = 0
        self.ack_duplicate = None
        return
         

    def input(self, packet):
        '''This method will be called whenever a packet sent 
        from the sender arrives at the receiver. If the received
        packet is corrupted or duplicate, it sends a packet where
        the ack number is the sequence number of the  last correctly
        received packet. Since there is only 0 and 1 sequence numbers,
        you can use the sequence number that is not expected.
        
        If packet is OK (not a duplicate or corrupted), deliver it to the
        application layer and send an acknowledgement to the sender
        '''
        if self.isCorrupted(packet) or self.isDuplicate(packet):
            # print("> input: Packet is corrupted or duplicate. Sending duplicate ack if one exists.")
            if self.ack_duplicate is not None:
                self.networkSimulator.udtSend(self.entity, self.ack_duplicate)
        else:
            # print("> input: Packet is OK. Passing to application layer and sending ack.")
            self.networkSimulator.deliverData(self.entity, packet.payload)
            self.networkSimulator.udtSend(self.entity, packet)
            self.ack_duplicate = packet
            self.expectedSequenceNumber = self.getNextExpectedSeqNum()
        return
