"""
    ~~~~~~~~~
    Node.py
    ~~~~~~~~~
    CP 372 -> Assignment 3
    Implement Networking Distance Vector Routing Algorithm
    
    @author Kelvin Kellner (190668940) - https://github.com/kelvinkellner
    @author Nishant Tewari (190684430) - https://github.com/XSilviaX
    @see https://github.com/XSilviaX/CP372
    
    ---------------------------------------------------------------------
"""
from common import *

class Node:
    def __init__(self, ID, networksimulator, costs):
        self.myID = ID
        self.ns = networksimulator
        num = self.ns.NUM_NODES        
        self.distanceTable = [[0 for _ in range(num)] for _ in range(num)]
        self.routes = [i if costs[i] != self.ns.INFINITY else self.ns.INFINITY for i in range(num)]
        self.connections = [i for i in range(num) if costs[i] != self.ns.INFINITY]

        # initialize distance table
        for i in range(num):
            for j in range(num):
                if i == j:
                    self.distanceTable[i][j] = 0
                elif i == self.myID:
                    self.distanceTable[i][j] = costs[j]
                else:
                    self.distanceTable[i][j] = self.ns.INFINITY
                
        # send the initial distance table to all neighbors
        for j in self.connections:
            if j != ID:
                pkt = RTPacket(ID, j, costs)
                self.ns.tolayer2(pkt)
        return

    def recvUpdate(self, pkt):
        # update estimated costs for sender node
        print(pkt.sourceid, '-->', self.myID, ':', pkt.mincosts)
        self.distanceTable[pkt.sourceid] = pkt.mincosts

        # calculate shortest path costs for all nodes using Bellman-Ford algorithm
        shortest_path_costs = self.bellman_ford_algorithm(self.myID)

        # if a change is made, update table and send new costs to neighbours
        arr_equal = lambda arr1, arr2: all(x == y for x, y in zip(arr1, arr2))
        if not arr_equal(self.distanceTable[self.myID], shortest_path_costs):
            self.distanceTable[self.myID] = shortest_path_costs
            for j in self.connections:
                if j != self.myID:
                    pkt = RTPacket(self.myID, j, shortest_path_costs)
                    self.ns.tolayer2(pkt)
        return 

    
    def printdt(self):
        print("   D"+str(self.myID)+" |  ", end="")
        for i in range(self.ns.NUM_NODES):
            print("{:3d}   ".format(i), end="")
        print()
        print("  ----|-", end="")
        for i in range(self.ns.NUM_NODES):            
            print("------", end="")
        print()    
        for i in range(self.ns.NUM_NODES):
            print("     {}|  ".format(i), end="" )
            
            for j in range(self.ns.NUM_NODES):
                print("{:3d}   ".format(self.distanceTable[i][j]), end="" )
            print()            
        print()

    def bellman_ford_algorithm(self, i):
        '''
        Computes the shortest costs for known paths from a
        single source node to all other nodes in the network
        '''
        # you implement the rest of it
        shortest_path_costs = []

        for j in range(self.ns.NUM_NODES):
            if i == j:
                shortest_path_costs.append(0)
            else:
                minimum_cost_path = self.distanceTable[i][j]
                for v in range(self.ns.NUM_NODES):
                    if self.distanceTable[i][v] != self.ns.INFINITY:
                        transitive_cost = self.distanceTable[i][v] + self.distanceTable[v][j]
                        if transitive_cost < minimum_cost_path:
                            minimum_cost_path = transitive_cost
                            self.routes[j] = v
                shortest_path_costs.append(minimum_cost_path)
        return shortest_path_costs

