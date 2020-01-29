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

