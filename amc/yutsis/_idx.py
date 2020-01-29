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


class Idx:
    """Angular-momentum index class"""

    default_name_index = {'hint': 0, 'int': 0}

    def __init__(self, type, name=None, *, is_particle, zero=False, external=False, rank=False):
        """Constructor method"""

        if type not in ('int', 'hint'):
            raise ValueError("Index type must be 'int' or 'hint'")

        # Properties
        self.type = type
        self.zero = zero
        self.external = external
        self.rank = rank

        self.name = name or Idx.make_name(type)

        # Sign, phase and jhat factors
        self.set_default()

        # Tex != None for particle indices
        self.is_particle = is_particle

        # To treat deltas in equations
        self.constrained_to = None

    def simplify(self):
        """Simplify the phases"""

        # Zero
        if self.zero:
            self.set_default()

        # Integer case
        if self.type == 'int':
            self.jphase %= 2
            self.mphase %= 2

        # Half-integer case
        if self.type == 'hint':
            self.jphase %= 4
            if self.jphase // 2 == 1:
                self.jphase -= 2
                self.sign *= -1
            self.mphase %= 4
            if self.mphase // 2 == 1:
                self.mphase -= 2
                self.sign *= -1

    def set_constraint(self, other):
        if self.type != other.type:
            raise ValueError('indices must have same type')

        self.constrained_to = other

        other.sign *= self.sign
        other.jphase += self.jphase
        other.mphase += self.mphase
        other.jhat += self.jhat

        self.set_default()

    def set_default(self):
        """Set default values"""

        self.jphase = 0
        self.mphase = 0
        self.sign = 1
        self.jhat = 0

    def __str__(self):
        """String"""

        stringTemplate = "index %s sign=%2i  phase=(-1)^{%2ij + %2im}  jhat=%2i  type=%4s  zero=%5r  external=%5r"
        return stringTemplate % (self.name, self.sign, self.jphase, self.mphase, self.jhat, self.type, self.zero, self.external)

    @staticmethod
    def coupled_type(idx1, idx2):
        if (idx1.type == 'hint' and idx2.type == 'hint') or (idx1.type == 'int' and idx2.type == 'int'):
            return 'int'
        else:
            return 'hint'

    @classmethod
    def make_name(cls, type):
        idx = cls.default_name_index[type]
        cls.default_name_index[type] += 1

        return ('j{}' if type == 'hint' else 'J{}').format(idx)
