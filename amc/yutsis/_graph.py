# Copyright (C) 2020  Julien Ripoche, Alexander Tichai, Roland Wirth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import (division, absolute_import, print_function)

from ._delta import Delta
from ._tridelta import TriangularDelta
from ._sixj import SixJ
from ._ninej import NineJ
from ._twelvej import TwelveJFirst
from ._idx import Idx
from ._node import YutsisNode
from ._edge import YutsisEdge


class YutsisGraph:
    """Yutsis graph class"""

    def __init__(self, threejms, deltas, _zeroIdx):
        """Constructor method"""

        # n number of the Yutsis graph
        self.n = len(threejms) // 2

        # Sign
        self.sign = +1

        # Create list of nodes
        self.nodes = [YutsisNode() for _ in range(2 * self.n)]

        # Create list of edges
        self.edges = [YutsisEdge() for _ in range(3 * self.n)]

        # Create list of deltas
        self.deltas = []
        self.deltas.extend(deltas)

        # Create list of triangular inequalities
        self.triangulardeltas = []

        # Create list of 6j-Symbols
        self.sixjs = []

        # Create list of 9j-Symbols
        self.ninejs = []

        # Create list of 12j(I)-Symbols
        self.twelvejfirsts = []

        # Create list of additional indices
        self.additionalIndices = []

        # Associate a zero index
        self.zeroIdx = _zeroIdx

        # Specify nodes and edges
        for k, threejm in enumerate(threejms):

            for l, idx in enumerate(threejm.indices):

                # Look for index of the corresponding edge
                kedge = -1
                for m, edge in enumerate(self.edges):
                    if edge.idx == idx or edge.idx == None:
                        kedge = m
                        break

                # Add corresponding index to edge
                self.edges[kedge].idx = idx

                # Add the corresponding node to edge
                if threejm.get_sign(l) == 1:
                    self.edges[kedge].setOutgoing(self.nodes[k])
                elif threejm.get_sign(l) == -1:
                    self.edges[kedge].setIncoming(self.nodes[k])
                else:
                    print("Error: 3JM-Symbol sign is neither 1 or -1")

                # Add the corresponding edge to node
                self.nodes[k].edges[l] = self.edges[kedge]

    def get_disconnected_graphs(self):
        """Return a list of disconnected graphs"""

        # Yutsis graph list
        yutsisGraphs = [self]

        # If empty graph return this empty graph
        if self.n == 0:
            return yutsisGraphs

        # Look for disconnected parts
        ygLength = self.n + 1
        while ygLength > self.n:
            ygLength = self.n
            nodes = [self.nodes[0]]
            edges = []
            for node in nodes:
                for edge in node.edges:
                    if edge not in edges:
                        edges.append(edge)
                        for edgeNode in edge.nodes:
                            if edgeNode not in nodes:
                                nodes.append(edgeNode)

            if len(nodes) > len(self.nodes):
                print("Error: The length of nodes should be lower than the one of self.nodes")
            elif len(nodes) == len(self.nodes):
                return yutsisGraphs
            else:
                # Create disconnected Yutsis graph
                YG = YutsisGraph([], [], self.zeroIdx)
                YG.n = len(nodes) // 2
                YG.nodes = nodes
                YG.edges = edges
                yutsisGraphs.append(YG)
                # Remove it from principal Yutsis graph
                self.n -= YG.n
                for node in YG.nodes:
                    self.nodes.remove(node)
                for edge in YG.edges:
                    self.edges.remove(edge)

        print("Error: Return should occur inside the loop")

    def separate_graph(self):
        """Return single internal line separated graph"""

        # Look for single internal lines
        ygLength = self.n + 1
        while ygLength > self.n:
            ygLength = self.n
            for internalLine in self.edges:
                nodes = [internalLine.nodes[0]]
                edges = []
                for node in nodes:
                    for edge in node.edges:
                        if edge not in edges and edge != internalLine:
                            edges.append(edge)
                            for edgeNode in edge.nodes:
                                if edgeNode not in nodes:
                                    nodes.append(edgeNode)

                # If the number of nodes is odd it means that the internal line
                # is a single internal line and one can perform separation
                if len(nodes) % 2 != 0:
                    self.singleInternalLineSeparation(internalLine)
                    break

    def singleInternalLineSeparation(self, edgeInt):
        """Separate graphs linked by a single internal line"""

        # Get internal nodes
        nodeInt1 = edgeInt.nodes[0]
        nodeInt2 = edgeInt.nodes[1]

        # Get external edges
        edgeExt1 = []
        edgeExt2 = []
        for edge in nodeInt1.edges:
            if edge != edgeInt:
                edgeExt1.append(edge)
        for edge in nodeInt2.edges:
            if edge != edgeInt:
                edgeExt2.append(edge)

        # Make edgeExt1[0] as incoming and edgeExt1[1] as outgoing
        if edgeExt1[0].getOutgoing() == nodeInt1:
            edgeExt1[0].changeDirection()
        if edgeExt1[1].getIncoming() == nodeInt1:
            edgeExt1[1].changeDirection()

        # Make edgeExt2[0] as incoming and edgeExt2[1] as outgoing
        if edgeExt2[0].getOutgoing() == nodeInt2:
            edgeExt2[0].changeDirection()
        if edgeExt2[1].getIncoming() == nodeInt2:
            edgeExt2[1].changeDirection()

        # Set the appropriate node signs
        if edgeExt1[0] == nodeInt1.firstOfTwo(edgeExt1[0], edgeExt1[1]):
            nodeInt1.changeSign('direct')
        if edgeExt2[0] == nodeInt2.firstOfTwo(edgeExt2[0], edgeExt2[1]):
            nodeInt2.changeSign('direct')

        # Add J hat factor
        edgeExt1[0].idx.jhat -= 1
        edgeExt2[0].idx.jhat -= 1

        # Create deltas
        self.deltas.append(Delta(edgeExt1[0].idx, edgeExt1[1].idx))
        self.deltas.append(Delta(edgeExt2[0].idx, edgeExt2[1].idx))
        self.deltas.append(Delta(self.zeroIdx, edgeInt.idx))

        # Remove the single internal line
        self.n -= 1
        self.edges.remove(edgeInt)
        self.nodes.remove(nodeInt1)
        self.nodes.remove(nodeInt2)
        self.mergeEdges(edgeExt1[1], edgeExt1[0])
        self.mergeEdges(edgeExt2[1], edgeExt2[0])

    def merge(self, Y):
        """Merge Y into self"""

        # Check
        if self.n != 0 or Y.n != 0:
            print("Error: merge method should be used whenever graphs are fully reduced")

        # Merge Y into self
        self.sign *= Y.sign
        self.deltas.extend(Y.deltas)
        self.triangulardeltas.extend(Y.triangulardeltas)
        self.sixjs.extend(Y.sixjs)
        self.ninejs.extend(Y.ninejs)
        self.additionalIndices.extend(Y.additionalIndices)

    def get_number_of_nodes(self):
        """Get the number of nodes"""

        return len(self.nodes)

    def mergeEdges(self, outgoingEdge, incomingEdge):
        """Merge the two exterior edges of a bubble"""

        # Change the outgoing node of outgoingEdge for the one of incomingEdge
        outgoingEdge.setOutgoing(incomingEdge.getOutgoing())

        # Set outgoingEdge as outgoing edge of the outgoing node of incomingEdge
        incomingEdge.getOutgoing().placeFirst(incomingEdge)
        incomingEdge.getOutgoing().edges[0] = outgoingEdge

        # Remove incomingEdge
        self.edges.remove(incomingEdge)

    def onecycleSearch(self, onecycleEdges):
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

    def bubbleSearch(self, bubbleEdges):
        """Search for a bubble in the graph"""

        # Search for a bubble in the graph
        for ka, nodeA in enumerate(self.nodes):
            for nodeB in self.nodes[ka + 1:]:
                commonListAB = [edge for edge in nodeA.edges if edge in nodeB.edges]
                if len(commonListAB) == 2:
                    bubbleEdges.append((commonListAB[0], commonListAB[1]))
                    break
            if bubbleEdges != []:
                break

        # Return bubbleEdges
        return bubbleEdges

    def triangleSearch(self, triangleEdges):
        """Search for a triangle in the graph"""

        # Search for a triangle in the graph
        for ka, nodeA in enumerate(self.nodes):
            for kb, nodeB in enumerate(self.nodes[ka + 1:]):
                commonListAB = [edge for edge in nodeA.edges if edge in nodeB.edges]
                if len(commonListAB) == 1:
                    for nodeC in self.nodes[ka + kb + 2:]:
                        commonListBC = [edge for edge in nodeB.edges if edge in nodeC.edges]
                        commonListCA = [edge for edge in nodeC.edges if edge in nodeA.edges]
                        if len(commonListBC) == 1 and len(commonListCA) == 1:
                            triangleEdges.append((commonListAB[0], commonListBC[0], commonListCA[0]))
                            break
                if triangleEdges != []:
                    break
            if triangleEdges != []:
                break

        # Return triangleEdges
        return triangleEdges

    def squareSearch(self, squareEdges):
        """Search for a square in the graph"""

        # Search for a square in the graph
        for ka, nodeA in enumerate(self.nodes):
            for kb, nodeB in enumerate(self.nodes[ka + 1:]):
                commonListAB = [edge for edge in nodeA.edges if edge in nodeB.edges]
                if len(commonListAB) == 1:
                    for kc, nodeC in enumerate(self.nodes[ka + 1:]):
                        if nodeC == nodeB:
                            continue
                        commonListAC = [edge for edge in nodeA.edges if edge in nodeC.edges]
                        commonListBC = [edge for edge in nodeB.edges if edge in nodeC.edges]
                        if len(commonListAC) == 1 and len(commonListBC) == 0:
                            for nodeD in self.nodes[ka + 1:]:
                                if nodeD == nodeB or nodeD == nodeC:
                                    continue
                                commonListBD = [edge for edge in nodeB.edges if edge in nodeD.edges]
                                commonListCD = [edge for edge in nodeC.edges if edge in nodeD.edges]
                                if len(commonListBD) == 1 and len(commonListCD) == 1:
                                    squareEdges.append((commonListAB[0], commonListBD[0], commonListCD[0], commonListAC[0]))
                                    break
                        if len(commonListAC) == 0 and len(commonListBC) == 1:
                            for nodeD in self.nodes[ka + 1:]:
                                if nodeD == nodeB or nodeD == nodeC:
                                    continue
                                commonListCD = [edge for edge in nodeC.edges if edge in nodeD.edges]
                                commonListDA = [edge for edge in nodeD.edges if edge in nodeA.edges]
                                if len(commonListCD) == 1 and len(commonListDA) == 1:
                                    squareEdges.append((commonListAB[0], commonListBC[0], commonListCD[0], commonListDA[0]))
                                    break
                        if squareEdges != []:
                            break
                if squareEdges != []:
                    break
            if squareEdges != []:
                break

        # Return squareEdges
        return squareEdges

    def bubbleReduction(self, bubbleEdges):
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
        if node1.firstOfTwo(edgeA, edgeB) == node2.firstOfTwo(edgeA, edgeB):
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

        # Create the delta
        self.deltas.append(Delta(edgeExt1.idx, edgeExt2.idx))

        # Set edgeExt1 index to the surviving one
        edgeExt1.idx = self.deltas[-1].indices[0]

        # Create the 3j-Symbol
        self.triangulardeltas.append(TriangularDelta(edgeExt1.idx, idxA, idxB))

        # Merge external edges (or remove them if lead to one-cycle)
        if edgeExt1.getIncoming() == edgeExt2.getOutgoing():
            self.edges.remove(edgeExt1)
            self.edges.remove(edgeExt2)
        else:
            self.mergeEdges(edgeExt1, edgeExt2)

    def triangleReduction(self, triangleEdges):
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
        if nodeAB.firstOfTwo(edgeA, edgeB) != edgeA:
            nodeAB.changeSign('indirect')
        if nodeBC.firstOfTwo(edgeB, edgeC) != edgeB:
            nodeBC.changeSign('indirect')
        if nodeCA.firstOfTwo(edgeC, edgeA) != edgeC:
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
        self.sixjs.append(SixJ(edgeExtBC.idx, edgeExtCA.idx, edgeExtAB.idx, edgeA.idx, edgeB.idx, edgeC.idx))

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

    def squareReduction(self, squareEdges, addIdxId):
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
        if nodeAB.firstOfTwo(edgeA, edgeB) != edgeA:
            nodeAB.changeSign('indirect')
        if nodeBC.firstOfTwo(edgeB, edgeC) != edgeB:
            nodeBC.changeSign('indirect')
        if nodeCD.firstOfTwo(edgeC, edgeD) != edgeC:
            nodeCD.changeSign('indirect')
        if nodeDA.firstOfTwo(edgeD, edgeA) != edgeD:
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
        numbHalfInt = 0
        numbHalfInt += 1 if edgeB.idx.type == 'hint' else 0
        numbHalfInt += 1 if edgeD.idx.type == 'hint' else 0
        addIdxType = 'int' if numbHalfInt % 2 == 0 else 'hint'
        addIdx = Idx(addIdxType, is_particle=False)
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
        self.sixjs.append(SixJ(edgeExtAB.idx, edgeExtDA.idx, addIdx, edgeD.idx, edgeB.idx, edgeA.idx))

        # Create the second 6j-Symbol
        # (1 2 3) -> (BC CD add)
        # (4 5 6) -> (D  B  C  )
        self.sixjs.append(SixJ(edgeExtBC.idx, edgeExtCD.idx, addIdx, edgeD.idx, edgeB.idx, edgeC.idx))

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

    def finalTriangularDelta(self):
        """Create the final triangular inequality."""

        if self.get_number_of_nodes() > 2:
            print("Error: The reduction has not been fully accomplished")
        else:
            # Set the appropriate edge orientations
            for k, edge in enumerate(self.edges):
                if edge.getIncoming() != self.nodes[0]:
                    if edge.getOutgoing() != self.nodes[0]:
                        print("Error: edge %i is neither incoming nor outgoing node0" % (k))
                        exit(-1)
                    edge.changeDirection()

            # Set the appropriate node signs
            for node in self.nodes:
                node.placeFirst(self.edges[0])
            if self.nodes[0].firstOfTwo(self.edges[1], self.edges[2]) == self.nodes[1].firstOfTwo(self.edges[1], self.edges[2]):
                self.nodes[1].changeSign('indirect')
            if self.nodes[0].sign == self.nodes[1].sign:
                self.nodes[1].changeSign('direct')

            # Create the 3j-Symbol
            self.triangulardeltas.append(TriangularDelta(self.edges[0].idx, self.edges[1].idx, self.edges[2].idx))

            # Remove the last 3j-Symbol from the graph
            self.n -= 1
            self.nodes.remove(self.nodes[1])
            self.nodes.remove(self.nodes[0])
            self.edges.remove(self.edges[2])
            self.edges.remove(self.edges[1])
            self.edges.remove(self.edges[0])

    def remove_redundant_triangulardeltas(self):
        """Remove 3j-Symbols that are already part of a 6j-Symbol"""

        for sixj in self.sixjs:
            for tridelta in self.triangulardeltas:
                if sixj.contains_triangulardelta(tridelta):
                    self.triangulardeltas.remove(tridelta)

    def printResults(self):
        """Print resulting objects"""

        # Introduction
        print("Show the graph content (n=%2i):" % (self.n))

        # Show deltas
        for delta in self.deltas:
            print(delta)

        # Show 3j-Symbols
        for tridelta in self.triangulardeltas:
            print(tridelta)

        # Show 6j-Symbols
        for sixj in self.sixjs:
            print(sixj)

    def collect_ninejs(self):
        """Factorize 9j-symbols from a given list of 6j-symbols"""

        # Loop over copy because list may be modified during iteration.
        for addIndex in self.additionalIndices[:]:
            self.collect_ninej(addIndex)

    def collect_ninej(self, additionalIndex):
        """Factorize 9j-symbols from a given list of 6j-symbols and an additional index"""

        # { idx1 idx2 idx3 }
        # { idx4 idx5 idx6 }                          { idx1 idx4 idx7 } { idx2 idx5 idx8 } { idx3 idx6 idx9 }
        # { idx7 idx8 idx9 } = sum_x (-1)^{2x} (2x+1) { idx8 idx9    x } { idx4    x idx6 } {    x idx1 idx2 }

        # Get 6j-symbols which contains this additional index
        sixjs = []
        for sixj in self.sixjs:
            if additionalIndex in sixj.indices:
                sixjs.append(sixj)

        # Additional index should appear in three 6j-symbols to make one 9j-symbol
        if len(sixjs) != 3:
            return

        # Check if this additional index phase is a multiple of 2
        if additionalIndex.jphase % 2 != 0:
            return

        # Check if this additional index has a (2j+1) factor
        if additionalIndex.jhat != 2:
            return

        # Put the additional index at a particular position
        for ksixj, sixj in enumerate(sixjs):
            position = sixj.indices.index(additionalIndex)
            col = position % 3
            line = position // 3
            if line != 1:
                sixj.permute_lines_for_columns(col, (col + 1) % 3)
            if col != 2 - ksixj:
                sixj.permute_columns(col, 2 - ksixj)

        # Put other indices in canonical position
        sixj1 = sixjs[0]
        sixj2 = sixjs[1]
        sixj3 = sixjs[2]

        # Already placed indices (j7,j5,j3)
        idx7 = sixj1.indices[2]
        idx5 = sixj2.indices[1]
        idx3 = sixj3.indices[0]

        # First sixj preparation
        try:
            position = sixj2.indices.index(sixj1.indices[0])
        except ValueError:
            pass
        else:
            sixj1.permute_lines_for_columns(0, 1)

        # Second sixj preparation
        # j8
        idx8 = sixj1.indices[3]
        try:
            position = sixj2.indices.index(idx8)
        except ValueError:
            print("Error: The index should appear in the two 6j-symbols (in Ninej factorization)")
        else:
            col = position % 3
            line = position // 3
            if line == 1:
                sixj2.permute_lines_for_columns(0, 2)
            if col == 0:
                sixj2.permute_columns(0, 2)

        # j4
        idx4 = sixj1.indices[1]
        try:
            position = sixj2.indices.index(idx4)
        except ValueError:
            print("Error: The index should appear in the two 6j-symbols (in Ninej factorization)")
        else:
            if position != 3:
                print("Error: ninej factorization failed")

        # Third sixj preparation
        # j1
        idx1 = sixj1.indices[0]
        try:
            position = sixj3.indices.index(idx1)
        except ValueError:
            print("Error: The index should appear in the two 6j-symbols (in Ninej factorization)")
        else:
            col = position % 3
            line = position // 3
            if line == 0:
                sixj3.permute_lines_for_columns(1, 2)
            if col == 2:
                sixj3.permute_columns(1, 2)

        # j9
        idx9 = sixj1.indices[4]
        try:
            position = sixj3.indices.index(idx9)
        except ValueError:
            print("Error: The index should appear in the two 6j-symbols (in Ninej factorization)")
        else:
            if position != 2:
                print("Error: ninej factorization failed")

        # j2
        idx2 = sixj2.indices[0]
        try:
            position = sixj3.indices.index(idx2)
        except ValueError:
            print("Error: The index should appear in the two 6j-symbols (in Ninej factorization)")
        else:
            if position != 5:
                print("Error: ninej factorization failed")

        # j6
        idx6 = sixj2.indices[5]
        try:
            position = sixj3.indices.index(idx6)
        except ValueError:
            print("Error: The index should appear in the two 6j-symbols (in Ninej factorization)")
        else:
            if position != 1:
                print("Error: ninej factorization failed")

        # Add a minus sign if additionalIndex is half-integer
        additionalIndex.simplify()
        if additionalIndex.type == 'hint':
            additionalIndex.sign *= -1
        self.sign *= additionalIndex.sign

        # Remove additional index
        self.additionalIndices.remove(additionalIndex)

        # Remove sixjs
        self.sixjs.remove(sixj1)
        self.sixjs.remove(sixj2)
        self.sixjs.remove(sixj3)

        # Create 9j-symbol
        self.ninejs.append(NineJ(idx1, idx2, idx3, idx4, idx5, idx6, idx7, idx8, idx9))

    def collect_twelvejfirsts(self):
        """Factorize 12j(I)-symbols from a given list of 6j-symbols and 9j-symbols"""

        # Loop over copy because list may be modified during iteration.
        for addIndex in self.additionalIndices[:]:
            self.collect_twelvejfirst(addIndex)

    def collect_twelvejfirst(self, additionalIndex):
        """Factorize 12j(I)-symbols from a given list of 6j-symbols and 9j-symbols and an additional index"""

        #                    {j1  j2   j3   j4   }
        #                    {  j5   j6   j7   j8}
        # (1)^{j1+j3-j9-j11} {j9  j10  j11  j12  }
        #
        #                { j1  j3  x   }
        #                { j8  j4  j9  } { j3  j1  x   } { j9  j11 x   }
        # = sum_x (2x+1) { j12 j7  j11 } { j5  j6  j2  } { j6  j5  j10 }

        # Get 6j-symbols which contains this additional index
        sixjs = []
        for sixj in self.sixjs:
            if additionalIndex in sixj.indices:
                sixjs.append(sixj)

        # Additional index should appear in two 6j-symbols
        if len(sixjs) != 2:
            return

        # Get 9j-symbols which contains this additional index
        ninejs = []
        for ninej in self.ninejs:
            if additionalIndex in ninej.indices:
                ninejs.append(ninej)

        # Additional index should appear in one 9j-symbol
        if len(ninejs) != 1:
            return
        ninej = ninejs[0]

        # Check if this additional index has a (2j+1) factor
        if additionalIndex.jhat != 2:
            return

        # Put the additional index at a particular position
        ninej.place_index_in_position(additionalIndex, 2)
        for sixj in sixjs:
            position = sixj.indices.index(additionalIndex)
            col = position % 3
            line = position // 3
            if line != 0:
                sixj.permute_lines_for_columns(col, (col + 1) % 3)
            if col != 2:
                sixj.permute_columns(col, 2)

        # Put other indices in canonical position
        sixj1 = sixjs[0]
        sixj2 = sixjs[1]

        # Already placed indices (j2,j10)
        idx2 = sixj1.indices[5]
        idx10 = sixj2.indices[5]
        if idx2 in sixj2.indices or idx2 in ninej.indices:
            print("Error: 12j(I) factorization impossible")
        if idx10 in sixj1.indices or idx10 in ninej.indices:
            print("Error: 12j(I) factorization impossible")

        # Prepare first sixj and two indices of the ninej
        if sixj1.indices[0] not in ninej.indices:
            sixj1.permute_lines_for_columns(0, 1)
        if sixj1.indices[0] not in ninej.indices[:2]:
            ninej.reflection_second_diagonal()
        if sixj1.indices[0] != ninej.indices[1]:
            ninej.permute_columns(0, 1)
        if sixj1.indices[0] != ninej.indices[1] or sixj1.indices[1] != ninej.indices[0]:
            print("Error: 12j(I) factorization impossible")
        idx3 = sixj1.indices[0]
        idx1 = sixj1.indices[1]
        idx5 = sixj1.indices[3]
        idx6 = sixj1.indices[4]

        # Check if this additional index phase is a multiple of 2
        # (Check done after possible reflection or permute columns because the phase might change)
        if additionalIndex.jphase % 2 != 0:
            return

        # Prepare second sixj and two indices of the ninej
        if sixj2.indices[0] not in ninej.indices:
            sixj2.permute_lines_for_columns(0, 1)
        if sixj2.indices[4] != sixj1.indices[3]:
            sixj2.permute_columns(0, 1)
        if sixj2.indices[0] != ninej.indices[5] or sixj2.indices[1] != ninej.indices[8]:
            print("Error: 12j(I) factorization impossible")
        idx9 = sixj2.indices[0]
        idx11 = sixj2.indices[1]
        if sixj2.indices[4] != idx5 or sixj2.indices[3] != idx6:
            print("Error: 12j(I) factorization impossible")

        # Indices from 9j-coefficient
        idx8 = ninej.indices[3]
        idx4 = ninej.indices[4]
        idx12 = ninej.indices[6]
        idx7 = ninej.indices[7]
        if idx8 in sixj1.indices or idx8 in sixj2.indices:
            print("Error: 12j(I) factorization impossible")
        if idx4 in sixj1.indices or idx8 in sixj2.indices:
            print("Error: 12j(I) factorization impossible")
        if idx12 in sixj1.indices or idx8 in sixj2.indices:
            print("Error: 12j(I) factorization impossible")
        if idx7 in sixj1.indices or idx8 in sixj2.indices:
            print("Error: 12j(I) factorization impossible")

        # Add a phase factor
        idx1.jphase += 1
        idx3.jphase += 1
        idx9.jphase -= 1
        idx11.jphase -= 1

        # Remove additional index
        additionalIndex.simplify()
        self.sign *= additionalIndex.sign
        self.additionalIndices.remove(additionalIndex)

        # Remove ninej
        self.ninejs.remove(ninej)

        # Remove sixjs
        self.sixjs.remove(sixj1)
        self.sixjs.remove(sixj2)

        # Create 12j(I)-symbol
        self.twelvejfirsts.append(TwelveJFirst(idx1, idx2, idx3, idx4, idx5, idx6, idx7, idx8, idx9, idx10, idx11, idx12))

