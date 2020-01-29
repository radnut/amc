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


class SixJ:
    """6j-symbol class"""

    def __init__(self, idx1, idx2, idx3, idx4, idx5, idx6):
        """Constructor method"""

        # J indices
        # { idx1 idx2 idx3 }
        # { idx4 idx5 idx6 }
        self.indices = [idx1, idx2, idx3, idx4, idx5, idx6]

        nint = 0
        for idx in self.indices:
            if idx.type == 'int':
                nint += 1

        if nint not in [2, 3, 6]:
            raise ValueError("Not a valid SixJ symbol")

        self.nint = nint

    def contains_triangulardelta(self, triangulardelta):
        """Check if the 6j-symbol already contains
        the corresponding triangular inequality"""

        # Get positions of indices of the 3j-symbol in the 6j-symbol
        positions = []
        for k, idx1 in enumerate(self.indices):
            for idx2 in triangulardelta.indices:
                if idx1 == idx2:
                    positions.append(k)

        # If three indices match look for a triangular inequality
        if len(positions) == 3:
            positions.sort()
            if positions in [[0, 1, 2], [0, 4, 5], [1, 3, 5], [2, 3, 4]]:
                return True
        elif len(positions) > 3:
            print("Error: 6j-symbol has some identical indices")

        return False

    def canonicalize(self):
        """Canonicalize 6j-symbol"""

        # All possibilities allowed by the four triangular inequalities:
        # ------- 2-integers case
        # |{hhi}| {hih} {ihh}
        # |{hhi}| {hih} {ihh}
        # ------- 3-integers case
        # |{iii}| {ihh} {hih} {hhi}
        # |{hhh}| {hii} {ihi} {iih}
        # ------- 6-integers case
        # |{iii}|
        # |{iii}|
        # -------
        # The three framed ones are choosen as canonicals.
        # One can get the other ones by applying symmetry properties of SixJ symbols.

        # Get the number of integer indices
        if self.nint == 2:
            if self.indices[0].type == 'int':
                self.indices = [self.indices[1], self.indices[2], self.indices[0], self.indices[4], self.indices[5], self.indices[3]]
            if self.indices[1].type == 'int':
                self.indices = [self.indices[0], self.indices[2], self.indices[1], self.indices[3], self.indices[5], self.indices[4]]
        elif self.nint == 3:
            hintTab = []
            for k, idx in enumerate(self.indices[:3]):
                if idx.type == 'hint':
                    hintTab.append(k)
            if len(hintTab) not in [0, 2]:
                print("Error: Not a valid 3-integers SixJ symbol !")
            elif len(hintTab) == 2:
                self.indices[hintTab[0]], self.indices[hintTab[0] + 3] = self.indices[hintTab[0] + 3], self.indices[hintTab[0]]
                self.indices[hintTab[1]], self.indices[hintTab[1] + 3] = self.indices[hintTab[1] + 3], self.indices[hintTab[1]]

        # In the two-integers case:
        # Put three-body index in the fifth position
        if self.nint == 2:
            for k, idx in enumerate(self.indices[0:2] + self.indices[3:5]):
                if not idx.is_particle:
                    if k == 0:
                        self.indices[0], self.indices[1], self.indices[3], self.indices[4] = self.indices[4], self.indices[3], self.indices[1], self.indices[0]
                    elif k == 1:
                        self.indices[0], self.indices[1], self.indices[3], self.indices[4] = self.indices[3], self.indices[4], self.indices[0], self.indices[1]
                    elif k == 2:
                        self.indices[0], self.indices[1], self.indices[3], self.indices[4] = self.indices[1], self.indices[0], self.indices[4], self.indices[3]
                    break

    def permute_indices(self, id1, id2):
        """Permute two indices characterize by their ids in self.indices"""

        self.indices[id1], self.indices[id2] = self.indices[id2], self.indices[id1]

    def permute_columns(self, col1, col2):
        """Permute two columns of the 6j-symbol"""

        # Check arguments
        if col1 not in range(3) or col2 not in range(3):
            raise ValueError("Invalid 6j-symbol column permutation")

        # Permute the two columns
        self.permute_indices(col1, col2)
        self.permute_indices(col1 + 3, col2 + 3)

    def permute_lines_for_columns(self, col1, col2):
        """Permute lines for two columns of the 6j-symbols"""

        # Check arguments
        if col1 not in range(3) or col2 not in range(3):
            raise ValueError("Invalid 6j-symbol column permutation")

        # Permute lines for the two columns
        self.permute_indices(col1, col1 + 3)
        self.permute_indices(col2, col2 + 3)

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        sixjTex = r'\sixj'
        for idx in self.indices:
            sixjTex += '{%s}' % (idx.name)

        return sixjTex

