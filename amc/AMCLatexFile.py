from __future__ import (division, absolute_import, print_function)

from sympy import Rational
from amc.YutsisGraph import ClbLatexFile

class AMCLatexFile(ClbLatexFile):
    """Class for Latex output"""

    def __init__(self,_filename):
        """Constructor method"""

        # Constructor of LatexFile class
        ClbLatexFile.__init__(self,_filename)

    def generateLHS(self,prefactor,sums,amplitudes):
        """Generate a LaTeX output"""

        # Overall sign and Prefactor
        overallSign = 1
        for amp in amplitudes:
            overallSign *= amp.sign
        if overallSign == -1:
            prefactor = Rational(-prefactor)
        if prefactor == 1:
            pass
        elif prefactor == -1:
            self.addString('-')
        else:
            self.addString(str(prefactor))

        # Summation
        if len(sums) != 0:
            self.addString("\\sum_{")
            for idx in sums:
                self.addString(idx.tex)
            self.addString("}")

        # Amplitudes
        for amp in amplitudes:
            self.addString(str(amp))

        # Alignment symbol and rightarrow
        self.addString('&\\rightarrow ')

        # Temporary
        self.addString('\\notag \\\\')

    def generateRHS(self,Y,prefactor,sums,indices,interindices,jschAmplitudes,noThreeJ=False):
        """Generate a LaTeX output"""

        # Simplifies indices
        for idx in indices:
            idx.simplify()

        # Alignment symbol
        #self.addString('&')

        # Overall sign and Prefactor
        overallSign = 1
        overallSign *= Y.sign
        for idx in indices:
            overallSign *= idx.sign
        for amp in jschAmplitudes:
            overallSign *= amp.sign
        if overallSign == -1:
            prefactor = Rational(-prefactor)
        if prefactor == 1:
            pass
        elif prefactor == -1:
            self.addString('-')
        else:
            self.addString(str(prefactor))

        # Summation
        if len(sums) != 0 or len([idx for idx in interindices if idx.constrained_to == None]) != 0:
            self.addString("\\sum_{")
            for idx in sums:
                if idx.constrained_to == None:
                    self.addString("\\tilde%s"%(idx.tex))
                else:
                    if idx.constrained_to.tex != None:
                        self.addString("n_{%s}"%(idx.tex))
                    else:
                        self.addString("(nlt)_{%s}"%(idx.tex))
            for idx in interindices:
                if idx.constrained_to == None:
                    self.addString(idx.jtex)
            self.addString("}")

        # Deltas
        self.addRHSDeltas(Y.deltas)

        # Single-particle phases
        self.addRHSPhases(indices)

        # Jhat
        self.addRHSJhats(indices)

        # Return and Alignment symbol
        self.addString('& \\notag \\\\')

        # Spherical amplitudes
        for amp in jschAmplitudes:
            self.addString(str(amp))

        # Return and Alignment symbol
        self.addString('& \\notag \\\\')

        # 3j-Symbols
        if not noThreeJ:
            self.addRHSThreeJs(Y.threejs)

        # 6j-Symbols
        self.addRHSSixJs(Y.sixjs)

        # 9j-Symbols
        self.addRHSNineJs(Y.ninejs)

        # 12j(I)-Symbols
        self.addRHSTwelveJFirsts(Y.twelvejfirsts)

        # Temporary
        #self.addString('&')

