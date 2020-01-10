from __future__ import (division, absolute_import, print_function)

from .ThreeJMSymbol import ThreeJM


class ClebschGordan:
    """Clebsch-Gordan coefficient class"""

    def __init__(self, indices, signs):
        """Constructor method"""

        # J indices
        self.indices = indices

        # Signs of M indices
        self.signs = signs

    def get_threejm(self):
        """Get the corresponding 3JM-Symbol object"""

        return ThreeJM(self.indices, self.signs)

    @classmethod
    def getPreamble(cls):
        """Get the newcommand line for Latex output"""

        return '\\newcommand{\\clebsch}[6]{C_{#1 #2,#3 #4}^{#5 #6}}\n'
        # return '\\newcommand{\\clebsch}[6]{\\begingroup\\setlength{\\arraycolsep}{0.1em}\\left(\\hskip -\\arraycolsep\\begin{array}{cc|c} #1 & #3 & #5 \\\\ #2 & #4 & #6 \\end{array}\\hskip -    \\arraycolsep\\right)\\endgroup}\n'

    def __str__(self):
        """String"""

        stringTemplate = "ClebscbGordan: %8s(%1s) %8s(%1s) %8s(%1s)"

        return stringTemplate % (self.indices[0].name, '+' if self.signs[0] == 1 else '-',
                               self.indices[1].name, '+' if self.signs[1] == 1 else '-',
                               self.indices[2].name, '+' if self.signs[2] == 1 else '-')

