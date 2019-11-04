
class YutsisEdge:
    """YutsisEdge class"""

    def __init__(self,_idx=None):
        """Constructor method"""

        # Index
        self.idx = _idx

        # Both nodes
        # Outgoing node -> self.nodes[0]
        # Incoming node -> self.nodes[1]
        self.nodes = [None for _ in range(2)]

    def getOutgoing(self):
        """Get outgoing node"""

        return self.nodes[0]

    def getIncoming(self):
        """Get incoming node"""

        return self.nodes[1]

    def setOutgoing(self,_outgoing):
        """Set outgoing node"""

        self.nodes[0] = _outgoing

    def setIncoming(self,_incoming):
        """Set incoming node"""

        self.nodes[1] = _incoming

    def changeDirection(self):
        """Change the edge direction"""

        # Phase factor
        self.idx.jphase += 2

        # Interchange the two nodes
        self.nodes[0], self.nodes[1] = self.nodes[1], self.nodes[0]

    def __str__(self):
        """String"""

        stringTemplate = "YutsisEdge %8s: From (%s) to (%s)"

        return stringTemplate % (self.idx.jtex,self.nodes[0],self.nodes[1])

