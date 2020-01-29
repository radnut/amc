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

    @classmethod
    def getPreamble(cls):
        """Get the newcommand line for Latex output"""

        # /!\ package version - condition for preamble ???

        return '\\usepackage{listofitems}\n'+'\\newcommand{\\twelvejfirst}[1]{\\setsepchar{,}\\readlist\\args{#1}\\begingroup\\setlength{\\arraycolsep}{0.2em}\\begin{Bmatrix} \\args[1] & \\args[2] & \\args[3] & \\args[4] \\\\ \\args[5] & \\args[6] & \\args[7] & \\args[8] \\\\ \\args[9] & \\args[10] & \\args[11] & \\args[12] \\end{Bmatrix}_{\\text{12j(I)}}\\endgroup}\n'

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        ninejTex = '\\twelvejfirst{'
        for k,idx in enumerate(self.indices):
            ninejTex += '%s'%(idx.jtex)
            if k != 11:
                ninejTex += ','
        ninejTex += '}'

        return ninejTex

