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

from copy import copy


class ThreeJM:
    """"3JM-symbol class"""

    def __init__(self, indices, signs):
        """Constructor method"""

        # Conversion of Clebsch-Gordan coefficient into 3JM-symbol
        # ( j1 j2 | j3 )                                       ( j1 j2  j3 )
        # ( m1 m2 | m3 ) = (-1)^{ j1 - j2 + m3 } sqrt{2j3 + 1} ( m1 m2 -m3 )

        # J indices
        self.indices = copy(indices)

        # Signs of M indices
        self.signs = copy(signs)

        # Phases
        self.indices[0].jphase += 1
        self.indices[1].jphase -= 1
        self.indices[2].mphase += self.signs[2]

        # jhat factor
        self.indices[2].jhat += 1

        # M sign
        self.signs[2] *= -1

        # Negative angular-momentum projection indices in a 3JM-symbol
        # are assumed to be accompanied with a (-1)^{j-m} phase:
        #                          ( j1 j2 j3 )
        #                          ( m1 m2 m3 )
        #                          ( j1 j2 j3 )
        #             (-1)^{j1-m1} (-m1 m2 m3 )
        #                          ( j1 j2 j3 )
        #       (-1)^{j1-m1+j2-m2} (-m1-m2 m3 )
        #                          ( j1 j2 j3 )
        # (-1)^{j1-m1+j2-m2+j3-m3} (-m1-m2-m3 )
        # Add a (-1)^{j-m} phase for each of the negative projection
        # to account for this property ((-1)^{2j-2m} = 1)
        for k in range(3):
            if self.signs[k] == -1:
                self.indices[k].jphase += 1
                self.indices[k].mphase -= 1

    def get_idx(self, k):
        """Get the corresponding index"""

        return self.indices[k]

    def set_idx(self, idx, k):
        """Set the corresponding index"""

        self.indices[k] = idx

    def exchange(self, k1, k2):
        """Exchange two couples (idx,sign) with the corresponding phase factor"""

        # ( j1 j2 j3 )                   ( j1 j3 j2 )
        # ( m1 m2 m3 ) = (-1)^{j1+j2+j3} ( m1 m3 m2 ) = ...

        # Necessary conditions
        if not (k1 in range(3) and k2 in range(3)):
            raise ValueError('invalid indices')

        if k1 == k2:
            return

        # Exchange index
        idx = self.indices[k1]
        self.indices[k1] = self.indices[k2]
        self.indices[k2] = idx

        # Exchange sign
        sign = self.signs[k1]
        self.signs[k1] = self.signs[k2]
        self.signs[k2] = sign

        # Phase factor
        for k in range(3):
            self.indices[k].jphase += 1

    def get_sign(self, k):
        """Get the corresponding sign"""

        return self.signs[k]

    def flip_signs(self):
        """Flip the sign of angular momentum projections"""

        # Flip the signs
        for k in range(3):
            self.signs[k] *= -1

        # Add phase factor if needed
        #              ( j1 j2 j3 )                                 ( j1 j2 j3 )
        # (-1)^{j1-m1} (-m1 m2 m3 ) = (-1)^{2j1} (-1)^{j2-m2+j3-m3} ( m1-m2-m3 )
        for k, idx in enumerate(self.indices):
            if self.signs[k] == +1:
                idx.jphase += 2

    def __str__(self):
        """String"""

        stringTemplate = "3JM-symbol: %8s(%1s) %8s(%1s) %8s(%1s)"

        return stringTemplate % (self.indices[0].jtex, '+' if self.signs[0] == 1 else '-',
                               self.indices[1].jtex, '+' if self.signs[1] == 1 else '-',
                               self.indices[2].jtex, '+' if self.signs[2] == 1 else '-')

