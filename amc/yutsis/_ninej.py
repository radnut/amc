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


class NineJ:
    """9j-symbol class"""

    def __init__(self, idx1, idx2, idx3, idx4, idx5, idx6, idx7, idx8, idx9):
        """Constructor method"""

        # J indices
        # { idx1 idx2 idx3 }
        # { idx4 idx5 idx6 }
        # { idx7 idx8 idx9 }
        self.indices = [idx1, idx2, idx3, idx4, idx5, idx6, idx7, idx8, idx9]

        # Canonicalize
        self.canonicalize()

    def canonicalize(self):
        """In some cases put the 9j-symbol in a more convenient form"""

        # Only canonicalize 9j-coefficients with three integers
        intIndices = []
        for idx in self.indices:
            if idx.type == "int":
                intIndices.append(idx)
        if len(intIndices) != 3:
            return

        # { j1 j3 J3 }
        # { j2 J2 j6 }
        # { J1 j4 j5 }

        # Place integer indices
        self.place_index_in_position(intIndices[0], 6)
        self.place_index_in_position(intIndices[1], 4)
        self.place_index_in_position(intIndices[2], 2)

    def place_index_in_position(self, idx, pos):
        """Place an index at a particular position"""

        # Get index position
        idxPos = self.indices.index(idx)

        # Permute column if necessary
        idxCol = idxPos % 3
        col = pos % 3
        if idxCol != col:
            self.permute_columns(idxCol, col)

        # Permute line if necessary
        idxLine = idxPos // 3
        line = pos // 3
        if idxLine != line:
            self.permute_lines(idxLine, line)

    def permute_indices(self, id1, id2):
        """Permute two indices characterize by their ids in self.indices"""

        self.indices[id1], self.indices[id2] = self.indices[id2], self.indices[id1]

    def add_permutation_phase(self):
        """Add the phase factor corresponding to an odd permutation of rows or columns"""

        for idx in self.indices:
            idx.jphase += 1

    def permute_columns(self, col1, col2):
        """Permute two columns of the 9j-symbol"""

        # Check arguments
        if col1 not in range(3) or col2 not in range(3):
            print("Error: Invalid 9j-symbol column permutation")

        # Permute the two columns
        self.permute_indices(col1  , col2)
        self.permute_indices(col1 + 3, col2 + 3)
        self.permute_indices(col1 + 6, col2 + 6)

        # Add the phase factor
        self.add_permutation_phase()

    def permute_lines(self, line1, line2):
        """Permute two lines of the 9j-symbols"""

        # Check arguments
        if line1 not in range(3) or line2 not in range(3):
            print("Error: Invalid 9j-symbol line permutation")

        # Permute the two lines
        self.permute_indices(3 * line1  , 3 * line2)
        self.permute_indices(3 * line1 + 1, 3 * line2 + 1)
        self.permute_indices(3 * line1 + 2, 3 * line2 + 2)

        # Add the phase factor
        self.add_permutation_phase()

    def reflection_first_diagonal(self):
        """Perform reflection over the first diagonal"""

        # { j1 j2 j3 }   { j1 j4 j7 }
        # { j4 j5 j6 } = { j2 j5 j8 }
        # { j7 j8 j9 }   { j3 j6 j9 }

        # Permutes indices
        self.permute_indices(1, 3)
        self.permute_indices(2, 6)
        self.permute_indices(5, 7)

    def reflection_second_diagonal(self):
        """Perform reflection over the second diagonal"""

        # { j1 j2 j3 }   { j9 j6 j3 }
        # { j4 j5 j6 } = { j8 j5 j2 }
        # { j7 j8 j9 }   { j7 j4 j1 }

        # Permutes indices
        self.permute_indices(0, 8)
        self.permute_indices(1, 5)
        self.permute_indices(3, 7)

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        ninejTex = '\\ninej'
        for idx in self.indices:
            ninejTex += '{%s}' % (idx.name)

        return ninejTex

