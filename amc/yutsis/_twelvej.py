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

class TwelveJFirst:
    """12j(I)-symbol class"""

    def __init__(self,idx1,idx2,idx3,idx4,idx5,idx6,idx7,idx8,idx9,idx10,idx11,idx12):
        """Constructor method"""

        # J indices
        # { idx1  idx2   idx3   idx4    }
        # {    idx5   idx6   idx7   idx8}
        # { idx9  idx10  idx11  idx12   }
        self.indices = [idx1,idx2,idx3,idx4,idx5,idx6,idx7,idx8,idx9,idx10,idx11,idx12]

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        ninejTex = '\\twelvejfirst{'
        for k,idx in enumerate(self.indices):
            ninejTex += '%s'%(idx.jtex)
            if k != 11:
                ninejTex += ','
        ninejTex += '}'

        return ninejTex

