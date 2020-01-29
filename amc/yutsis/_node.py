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


class YutsisNode:
    """YutsisNode class"""

    def __init__(self):
        """Constructor method"""

        # Assign plus sign by default
        self.sign = 1

        # List of edges
        self.edges = [None for _ in range(3)]

    def changeSign(self,_type):
        """Change the sign of the node with or without
        changing the order of the edges"""

        # Change the sign
        self.sign *= -1

        # Phase factor
        if _type == "direct":
            for edge in self.edges:
                edge.idx.jphase += 1

    def firstOfTwo(self,_edgeA,_edgeB):
        """Return the one edge that is followed by
        the other edge in the positive cyclic order"""

        if self.edges[0] in (_edgeA,_edgeB):
            if self.edges[1] in (_edgeA,_edgeB):
                return self.edges[0]
            else:
                return self.edges[2]
        else:
            return self.edges[1]

    def placeFirst(self,_edge):
        """Place _edge in the first place of the self.edges"""

        if self.edges[1] == _edge:
            self.edges[1] = self.edges[2]
            self.edges[2] = self.edges[0]
            self.edges[0] = _edge
        elif self.edges[2] == _edge:
            self.edges[2] = self.edges[1]
            self.edges[1] = self.edges[0]
            self.edges[0] = _edge

    def __str__(self):
        """String"""

        stringTemplate = "YutsisNode: %8s %8s %8s"

        return stringTemplate % (self.edges[0].idx.jtex, self.edges[1].idx.jtex, self.edges[2].idx.jtex)

