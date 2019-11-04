
from .Delta import *
from .ThreeJ import *
from .SixJ import *
from .Idx import *
from .YutsisNode import *
from .YutsisEdge import *

class YutsisGraph:
    """Yutsis graph class"""

    def __init__(self,threejms,deltas,_zeroIdx):
        """Constructor method"""

        # n number of the Yutsis graph
        self.n = len(threejms)//2

        # Create list of nodes
        self.nodes = [YutsisNode() for _ in range(2*self.n)]

        # Create list of edges
        self.edges = [YutsisEdge() for _ in range(3*self.n)]

        # Create list of deltas
        self.deltas = []
        self.deltas.extend(deltas)

        # Create list of 3j-Symbols
        self.threejs = []

        # Create list of 6j-Symbols
        self.sixjs = []

        # Create list of additional indices
        self.additionalIndices = []

        # Associate a zero index
        self.zeroIdx = _zeroIdx

        # Specify nodes and edges
        for k,threejm in enumerate(threejms):

            for l,idx in enumerate(threejm.indices):

                # Look for index of the corresponding edge
                kedge = -1
                for m,edge in enumerate(self.edges):
                    if edge.idx == idx or edge.idx == None:
                        kedge = m
                        break

                # Add corresponding index to edge
                self.edges[kedge].idx = idx

                # Add the corresponding node to edge
                if threejm.getSign(l) == 1:
                    self.edges[kedge].setOutgoing(self.nodes[k])
                elif threejm.getSign(l) == -1:
                    self.edges[kedge].setIncoming(self.nodes[k])
                else:
                    print("Error: 3JM-Symbol sign is neither 1 or -1")

                # Add the corresponding edge to node
                self.nodes[k].edges[l] = self.edges[kedge]

    def getNumberOfNodes(self):
        """Get the number of nodes"""

        return len(self.nodes)

    def mergeEdges(self,outgoingEdge,incomingEdge):
        """Merge the two exterior edges of a bubble"""

        # Change the outgoing node of outgoingEdge for the one of incomingEdge
        outgoingEdge.setOutgoing(incomingEdge.getOutgoing())

        # Set outgoingEdge as outgoing edge of the outgoing node of incomingEdge
        incomingEdge.getOutgoing().placeFirst(incomingEdge)
        incomingEdge.getOutgoing().edges[0] = outgoingEdge

        # Remove incomingEdge
        self.edges.remove(incomingEdge)

    def onecycleSearch(self,onecycleEdges):
        """Search for a 1-cycle in the graph"""

        # Search for a 1-cycle in the graph
        for node in self.nodes:
            edges = node.edges
            for edge in edges:
                if edges.count(edge) == 2:
                    onecycleEdges.append((edge))
                    break
            if onecycleEdges != []:
                break

        # Return onecycleEdges
        return onecycleEdges

    def bubbleSearch(self,bubbleEdges):
        """Search for a bubble in the graph"""

        # Search for a bubble in the graph
        for ka,nodeA in enumerate(self.nodes):
            for nodeB in self.nodes[ka+1:]:
                commonListAB = [edge for edge in nodeA.edges if edge in nodeB.edges]
                if len(commonListAB) == 2:
                    bubbleEdges.append((commonListAB[0],commonListAB[1]))
                    break
            if bubbleEdges != []:
                break

        # Return bubbleEdges
        return bubbleEdges

    def triangleSearch(self,triangleEdges):
        """Search for a triangle in the graph"""

        # Search for a triangle in the graph
        for ka,nodeA in enumerate(self.nodes):
            for kb,nodeB in enumerate(self.nodes[ka+1:]):
                commonListAB = [edge for edge in nodeA.edges if edge in nodeB.edges]
                if len(commonListAB) == 1:
                    for nodeC in self.nodes[ka+kb+2:]:
                        commonListBC = [edge for edge in nodeB.edges if edge in nodeC.edges]
                        commonListCA = [edge for edge in nodeC.edges if edge in nodeA.edges]
                        if len(commonListBC) == 1 and len(commonListCA) == 1:
                            triangleEdges.append((commonListAB[0],commonListBC[0],commonListCA[0]))
                            break
                if triangleEdges != []:
                    break
            if triangleEdges != []:
                break

        # Return triangleEdges
        return triangleEdges

    def squareSearch(self,squareEdges):
        """Search for a square in the graph"""

        # Search for a square in the graph
        for ka,nodeA in enumerate(self.nodes):
            for kb,nodeB in enumerate(self.nodes[ka+1:]):
                commonListAB = [edge for edge in nodeA.edges if edge in nodeB.edges]
                if len(commonListAB) == 1:
                    for kc,nodeC in enumerate(self.nodes[ka+1:]):
                        if nodeC == nodeB:
                            continue
                        commonListAC = [edge for edge in nodeA.edges if edge in nodeC.edges]
                        commonListBC = [edge for edge in nodeB.edges if edge in nodeC.edges]
                        if len(commonListAC) == 1 and len(commonListBC) == 0:
                            for nodeD in self.nodes[ka+1:]:
                                if nodeD == nodeB or nodeD == nodeC:
                                    continue
                                commonListBD = [edge for edge in nodeB.edges if edge in nodeD.edges]
                                commonListCD = [edge for edge in nodeC.edges if edge in nodeD.edges]
                                if len(commonListBD) == 1 and len(commonListCD) == 1:
                                    squareEdges.append((commonListAB[0],commonListBD[0],commonListCD[0],commonListAC[0]))
                                    break
                        if len(commonListAC) == 0 and len(commonListBC) == 1:
                            for nodeD in self.nodes[ka+1:]:
                                if nodeD == nodeB or nodeD == nodeC:
                                    continue
                                commonListCD = [edge for edge in nodeC.edges if edge in nodeD.edges]
                                commonListDA = [edge for edge in nodeD.edges if edge in nodeA.edges]
                                if len(commonListCD) == 1 and len(commonListDA) == 1:
                                    squareEdges.append((commonListAB[0],commonListBC[0],commonListCD[0],commonListDA[0]))
                                    break
                        if squareEdges != []:
                            break
                if squareEdges != []:
                    break
            if squareEdges != []:
                break

        # Return squareEdges
        return squareEdges

    def oneCycleReduction(self,edgeIncoming,edgeOutgoing):
        """Remove a 1-cycle from the graph"""

        # Get the internal node of the one-cycle
        nodeInt = edgeOutgoing.getOutgoing()
        if(nodeInt != edgeIncoming.getIncoming()):
            print("Error: Outgoing and incoming nodes of one-cycle edge should be the same")

        # Get the internal edge
        for edge in nodeInt.edges:
            if edge not in [edgeIncoming,edgeOutgoing]:
                edgeInt = edge
                break

        # Get the external node
        for node in edgeInt.nodes:
            if node != nodeInt:
                nodeExt = node
                break

        # Get the two external edges
        for edge in nodeExt.edges:
            if edge not in [edgeInt]:
                edgeExt1 = edge
                break
        for edge in nodeExt.edges:
            if edge not in [edgeInt,edgeExt1]:
                edgeExt2 = edge
                break

        # Make edgeExt1 as incoming and edgeExt2 as outgoing
        if edgeExt1.getOutgoing() == nodeExt:
            edgeExt1.changeDirection()
        if edgeExt2.getIncoming() == nodeExt:
            edgeExt2.changeDirection()

        # Set the appropriate node signs
        if edgeIncoming == nodeInt.firstOfTwo(edgeIncoming,edgeOutgoing):
            nodeInt.changeSign('direct')
        if edgeExt1 == nodeExt.firstOfTwo(edgeExt1,edgeExt2):
            nodeInt.changeSign('direct')

        # Add J hat factor
        edgeIncoming.idx.jhat += 1
        edgeExt1.idx.jhat -= 1

        # Create deltas
        self.deltas.append(Delta(edgeExt1.idx,edgeExt2.idx))
        self.deltas.append(Delta(self.zeroIdx,edgeInt.idx))

        # Remove the one-cycle from the graph
        self.n -= 1
        self.edges.remove(edgeInt)
        self.nodes.remove(nodeInt)
        self.nodes.remove(nodeExt)
        self.mergeEdges(edgeExt2,edgeExt1)

    def bubbleReduction(self,bubbleEdges):
        """Remove a bubble from the graph"""

        # Get the internal edges of the bubble
        edgeA, edgeB = bubbleEdges

        # Get the two nodes of the bubble
        node1 = edgeA.getOutgoing()
        node2 = edgeA.getIncoming()

        # Get the two external edges of the bubble
        for edge in node1.edges:
            if edge not in bubbleEdges:
                edgeExt1 = edge
                break
        for edge in node2.edges:
            if edge not in bubbleEdges:
                edgeExt2 = edge
                break

        # Set the appropriate edge orientations
        if edgeB.getOutgoing() != node1:
            if edgeB.getIncoming() != node1:
                print("Error: edgeB is neither incoming nor outgoing node1")
            edgeB.changeDirection()
        if edgeExt1.getOutgoing() != node1:
            if edgeExt1.getIncoming() != node1:
                print("Error: edgeExt1 is neither incoming nor outgoing node1")
            edgeExt1.changeDirection()
        if edgeExt2.getIncoming() != node2:
            if edgeExt2.getOutgoing() != node2:
                print("Error: edgeExt2 is neither incoming nor outgoing node2")
            edgeExt2.changeDirection()

        # Set the appropriate node signs
        if node1.firstOfTwo(edgeA,edgeB) == node2.firstOfTwo(edgeA,edgeB):
            node2.changeSign('indirect')
        if node1.sign == node2.sign:
            node2.changeSign('direct')

        # Add J hat factor
        edgeExt1.idx.jhat -= 2

        # Save edgeA and edgeB indices
        idxA = edgeA.idx
        idxB = edgeB.idx

        # Remove the bubble from the graph
        self.n -= 1
        self.nodes.remove(node1)
        self.nodes.remove(node2)
        self.edges.remove(edgeA)
        self.edges.remove(edgeB)

        # If lead to one-cycle then proceed to the one-cycle reduction
        # before merging the two edges (if not then there would be phase indetermination)
        if edgeExt1.getIncoming() == edgeExt2.getOutgoing():
            self.oneCycleReduction(edgeExt1,edgeExt2)

        # Create the delta
        self.deltas.append(Delta(edgeExt1.idx,edgeExt2.idx))

        # Set edgeExt1 index to the surviving one
        edgeExt1.idx = self.deltas[-1].indices[0]

        # Create the 3j-Symbol
        self.threejs.append(ThreeJ(edgeExt1.idx,idxA,idxB))

        # Merge external edges (or remove them if lead to one-cycle)
        if edgeExt1.getIncoming() == edgeExt2.getOutgoing():
            self.edges.remove(edgeExt1)
            self.edges.remove(edgeExt2)
        else:
            self.mergeEdges(edgeExt1,edgeExt2)

    def triangleReduction(self,triangleEdges):
        """Remove a triangle from the graph"""

        # Get the internal edges of the triangle
        edgeA, edgeB, edgeC = triangleEdges

        # Get the three nodes of the triangle
        for nodeA in edgeA.nodes:
            for nodeB in edgeB.nodes:
                if nodeA == nodeB:
                    nodeAB = nodeA
        for nodeB in edgeB.nodes:
            for nodeC in edgeC.nodes:
                if nodeB == nodeC:
                    nodeBC = nodeB
        for nodeC in edgeC.nodes:
            for nodeA in edgeA.nodes:
                if nodeC == nodeA:
                    nodeCA = nodeC

        # Get the three external edges of the triangle
        for edge in nodeAB.edges:
            if edge not in triangleEdges:
                edgeExtAB = edge
                break
        for edge in nodeBC.edges:
            if edge not in triangleEdges:
                edgeExtBC = edge
                break
        for edge in nodeCA.edges:
            if edge not in triangleEdges:
                edgeExtCA = edge
                break

        # Set the appropriate edge orientations
        if edgeA.getOutgoing() != nodeAB:
            if edgeA.getIncoming() != nodeAB:
                print("Error: edgeA is neither incoming nor outgoing nodeAB")
            edgeA.changeDirection()
        if edgeB.getOutgoing() != nodeBC:
            if edgeB.getIncoming() != nodeBC:
                print("Error: edgeB is neither incoming nor outgoing nodeBC")
            edgeB.changeDirection()
        if edgeC.getOutgoing() != nodeCA:
            if edgeC.getIncoming() != nodeCA:
                print("Error: edgeC is neither incoming nor outgoing nodeCA")
            edgeC.changeDirection()
        if edgeExtAB.getOutgoing() != nodeAB:
            if edgeExtAB.getIncoming() != nodeAB:
                print("Error: edgeExtAB is neither incoming nor outgoing nodeAB")
            edgeExtAB.changeDirection()
        if edgeExtBC.getOutgoing() != nodeBC:
            if edgeExtBC.getIncoming() != nodeBC:
                print("Error: edgeExtBC is neither incoming nor outgoing nodeBC")
            edgeExtBC.changeDirection()
        if edgeExtCA.getOutgoing() != nodeCA:
            if edgeExtCA.getIncoming() != nodeCA:
                print("Error: edgeExtCA is neither incoming nor outgoing nodeCA")
            edgeExtCA.changeDirection()

        # Set the appropriate node signs
        if nodeAB.firstOfTwo(edgeA,edgeB) != edgeA:
            nodeAB.changeSign('indirect')
        if nodeBC.firstOfTwo(edgeB,edgeC) != edgeB:
            nodeBC.changeSign('indirect')
        if nodeCA.firstOfTwo(edgeC,edgeA) != edgeC:
            nodeCA.changeSign('indirect')
        if nodeAB.sign != -1:
            nodeAB.changeSign('direct')
        if nodeBC.sign != -1:
            nodeBC.changeSign('direct')
        if nodeCA.sign != -1:
            nodeCA.changeSign('direct')

        # Create the 6j-Symbol
        # (1 2 3) -> (BC CA AB)
        # (4 5 6) -> (A  B  C )
        self.sixjs.append(SixJ(edgeExtBC.idx,edgeExtCA.idx,edgeExtAB.idx,edgeA.idx,edgeB.idx,edgeC.idx))

        # Remove the triangle from the graph
        self.n -= 1
        nodeAB.sign = +1
        nodeAB.placeFirst(edgeExtAB)
        nodeAB.edges[1] = edgeExtCA
        nodeAB.edges[2] = edgeExtBC
        edgeExtBC.setOutgoing(nodeAB)
        edgeExtCA.setOutgoing(nodeAB)
        self.nodes.remove(nodeBC)
        self.nodes.remove(nodeCA)
        self.edges.remove(edgeA)
        self.edges.remove(edgeB)
        self.edges.remove(edgeC)

    def squareReduction(self,squareEdges):
        """Remove a square from the graph"""

        # Get the internal edges of the square
        edgeA, edgeB, edgeC, edgeD = squareEdges

        # Get the four nodes of the square
        for nodeA in edgeA.nodes:
            for nodeB in edgeB.nodes:
                if nodeA == nodeB:
                    nodeAB = nodeA
        for nodeB in edgeB.nodes:
            for nodeC in edgeC.nodes:
                if nodeB == nodeC:
                    nodeBC = nodeB
        for nodeC in edgeC.nodes:
            for nodeD in edgeD.nodes:
                if nodeC == nodeD:
                    nodeCD = nodeC
        for nodeD in edgeD.nodes:
            for nodeA in edgeA.nodes:
                if nodeD == nodeA:
                    nodeDA = nodeD

        # Get the four external edges of the square
        for edge in nodeAB.edges:
            if edge not in squareEdges:
                edgeExtAB = edge
                break
        for edge in nodeBC.edges:
            if edge not in squareEdges:
                edgeExtBC = edge
                break
        for edge in nodeCD.edges:
            if edge not in squareEdges:
                edgeExtCD = edge
                break
        for edge in nodeDA.edges:
            if edge not in squareEdges:
                edgeExtDA = edge
                break

        # Set the appropriate edge orientations
        if edgeA.getOutgoing() != nodeAB:
            if edgeA.getIncoming() != nodeAB:
                print("Error: edgeA is neither incoming nor outgoing nodeAB")
            edgeA.changeDirection()
        if edgeB.getOutgoing() != nodeBC:
            if edgeB.getIncoming() != nodeBC:
                print("Error: edgeB is neither incoming nor outgoing nodeBC")
            edgeB.changeDirection()
        if edgeC.getOutgoing() != nodeCD:
            if edgeC.getIncoming() != nodeCD:
                print("Error: edgeC is neither incoming nor outgoing nodeCD")
            edgeC.changeDirection()
        if edgeD.getOutgoing() != nodeDA:
            if edgeD.getIncoming() != nodeDA:
                print("Error: edgeD is neither incoming nor outgoing nodeDA")
            edgeD.changeDirection()
        if edgeExtAB.getOutgoing() != nodeAB:
            if edgeExtAB.getIncoming() != nodeAB:
                print("Error: edgeExtAB is neither incoming nor outgoing nodeAB")
            edgeExtAB.changeDirection()
        if edgeExtBC.getOutgoing() != nodeBC:
            if edgeExtBC.getIncoming() != nodeBC:
                print("Error: edgeExtBC is neither incoming nor outgoing nodeBC")
            edgeExtBC.changeDirection()
        if edgeExtCD.getOutgoing() != nodeCD:
            if edgeExtCD.getIncoming() != nodeCD:
                print("Error: edgeExtCD is neither incoming nor outgoing nodeCD")
            edgeExtCD.changeDirection()
        if edgeExtDA.getOutgoing() != nodeDA:
            if edgeExtDA.getIncoming() != nodeDA:
                print("Error: edgeExtDA is neither incoming nor outgoing nodeDA")
            edgeExtDA.changeDirection()

        # Set the appropriate node signs
        if nodeAB.firstOfTwo(edgeA,edgeB) != edgeA:
            nodeAB.changeSign('indirect')
        if nodeBC.firstOfTwo(edgeB,edgeC) != edgeB:
            nodeBC.changeSign('indirect')
        if nodeCD.firstOfTwo(edgeC,edgeD) != edgeC:
            nodeCD.changeSign('indirect')
        if nodeDA.firstOfTwo(edgeD,edgeA) != edgeD:
            nodeDA.changeSign('indirect')
        if nodeAB.sign != -1:
            nodeAB.changeSign('direct')
        if nodeBC.sign != -1:
            nodeBC.changeSign('direct')
        if nodeCD.sign != -1:
            nodeCD.changeSign('direct')
        if nodeDA.sign != -1:
            nodeDA.changeSign('direct')

        # Create an additional index and add it to self.additionalIndices
        addIdxId = len(self.additionalIndices) + 1
        numbHalfInt = 0
        numbHalfInt += 1 if edgeB.idx.type == 'hint' else 0
        numbHalfInt += 1 if edgeD.idx.type == 'hint' else 0
        addIdxType = 'int' if numbHalfInt % 2 == 0 else 'hint'
        addIdx = Idx(addIdxType,None,'K_{%s}'%(addIdxId),'shouldNeverAppear')
        self.additionalIndices.append(addIdx)

        # Create the edge associated the additional index and add it to self.edges
        addEdge = YutsisEdge(addIdx)
        self.edges.append(addEdge)

        # Add phases
        addIdx.jphase += 1
        edgeB.idx.jphase += 1
        edgeD.idx.jphase -= 1

        # Add jhat factor
        addIdx.jhat += 2

        # Create the first 6j-Symbol
        # (1 2 3) -> (AB DA add)
        # (4 5 6) -> (D  B  A  )
        self.sixjs.append(SixJ(edgeExtAB.idx,edgeExtDA.idx,addIdx,edgeD.idx,edgeB.idx,edgeA.idx))

        # Create the second 6j-Symbol
        # (1 2 3) -> (BC CD add)
        # (4 5 6) -> (D  B  C  )
        self.sixjs.append(SixJ(edgeExtBC.idx,edgeExtCD.idx,addIdx,edgeD.idx,edgeB.idx,edgeC.idx))

        # Remove the square from the graph
        self.n -= 1
        nodeAB.sign = +1
        nodeAB.placeFirst(edgeExtAB)
        nodeAB.edges[1] = edgeExtDA
        nodeAB.edges[2] = addEdge
        nodeBC.sign = +1
        nodeBC.placeFirst(edgeExtBC)
        nodeBC.edges[1] = addEdge
        nodeBC.edges[2] = edgeExtCD
        edgeExtDA.setOutgoing(nodeAB)
        edgeExtCD.setOutgoing(nodeBC)
        addEdge.setOutgoing(nodeAB)
        addEdge.setIncoming(nodeBC)
        self.nodes.remove(nodeCD)
        self.nodes.remove(nodeDA)
        self.edges.remove(edgeA)
        self.edges.remove(edgeB)
        self.edges.remove(edgeC)
        self.edges.remove(edgeD)

    def finalThreeJSymbol(self):
        """Create the final 3J-symbol"""

        if self.getNumberOfNodes() > 2:
            print("Error: The reduction has not been fully accomplished")
        else:
            # Set the appropriate edge orientations
            for k,edge in enumerate(self.edges):
                if edge.getIncoming() != self.nodes[0]:
                    if edge.getOutgoing() != self.nodes[0]:
                        print("Error: edge %i is neither incoming nor outgoing node0"%(k))
                        exit(-1)
                    edge.changeDirection()

            # Set the appropriate node signs
            for node in self.nodes:
                node.placeFirst(self.edges[0])
            if self.nodes[0].firstOfTwo(self.edges[1],self.edges[2]) == self.nodes[1].firstOfTwo(self.edges[1],self.edges[2]):
                self.nodes[1].changeSign('indirect')
            if self.nodes[0].sign == self.nodes[1].sign:
                self.nodes[1].changeSign('direct')

            # Create the 3j-Symbol
            self.threejs.append(ThreeJ(self.edges[0].idx,self.edges[1].idx,self.edges[2].idx))

            # Remove the last 3j-Symbol from the graph
            self.n -= 1
            self.nodes.remove(self.nodes[1])
            self.nodes.remove(self.nodes[0])
            self.edges.remove(self.edges[2])
            self.edges.remove(self.edges[1])
            self.edges.remove(self.edges[0])

    def removeRedondantThreeJ(self):
        """Remove 3j-Symbols that are already part of a 6j-Symbol"""

        for sixj in self.sixjs:
            for threej in self.threejs:
                if sixj.containsThreeJ(threej):
                    self.threejs.remove(threej)

    def printResults(self):
        """Print resulting objects"""

        # Introduction
        print("Show the graph content (n=%2i):" % (self.n))

        # Show deltas
        for delta in self.deltas:
            print(delta)

        # Show 3j-Symbols
        for threej in self.threejs:
            print(threej)

        # Show 6j-Symbols
        for sixj in self.sixjs:
            print(sixj)

