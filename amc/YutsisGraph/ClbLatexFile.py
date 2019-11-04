
from .Idx import *
from .ClebschGordan import *
from .SixJ import *
from .YutsisGraph import *
from .LatexFile import *

# /!\ Some stuff missing for proper outputs
# /!\ Prepare some examples

class ClbLatexFile(LatexFile):
    """Class for Latex output"""

    def __init__(self,_filename):
        """Constructor method"""

        # Constructor of LatexFile class
        LatexFile.__init__(self,_filename)

    def addMacros(self):
        """Add macros for angular-momentum coupling coefficients"""

        self.addString(ClebschGordan.getPreamble())
        self.addString(SixJ.getPreamble())
        self.addString(ThreeJ.getPreamble())
        self.addString('\n')

    def generateLHS(self,indices,clebsches):
        """Generate a LaTeX output"""

        # Alignment symbol
        self.addString('&')

        #Add M dependent quantities
        self.addLHSMdependent(indices,clebsches)

    def addLHSMdependent(self,indices,clebsches):
        """Add M dependent quantities"""

        # Ms summation symbol
        self.addLHSSummations(indices)

        # Return and Alignment symbol
        self.addString(' \\notag \\\\ &')

        # Single-particle phases
        self.addLHSPhases(indices)

        # Return and Alignment symbol
        self.addString(' \\notag \\\\ &')

        # Clebsch-Gordan coefficients
        self.addLHSClebsches(clebsches)

        # Return and Alignment symbol
        self.addString(' \\notag \\\\ &')

    def addLHSSummations(self,indices):
        """Add summations"""

        # If there is no summation indices then return
        if len(indices) == 0: return

        self.addString('\\sum_{')
        for idx in indices:
            if not idx.zero:
                self.addString(idx.mtex + ' ')
        self.addString('}')

    def addLHSPhases(self,indices):
        """Add phases"""

        for idx in indices:
            if idx.jphase != 0 or idx.mphase != 0:
                self.addString('(-1)^{')
                if idx.jphase != 0:
                    self.addString('' if idx.jphase > 0 else '-')
                    self.addString('%i'%(abs(idx.jphase)) if abs(idx.jphase) > 1 else '')
                    self.addString(idx.jtex + ' ')
                if idx.mphase != 0:
                    self.addString('+' if idx.mphase > 0 else '-')
                    self.addString('%i'%(abs(idx.mphase)) if abs(idx.mphase) > 1 else '')
                    self.addString(idx.mtex)
                self.addString('}')

    def addLHSClebsches(self,clebsches):
        """Add clebches"""

        for kclb,clebsch in enumerate(clebsches):
            self.addString('\\clebsch')
            for k,idx in enumerate(clebsch.indices):
                self.addString('{'+idx.jtex+'}'+'{')
                if clebsch.signs[k] == -1:
                    self.addString('-')
                self.addString(idx.mtex+'}')
            if (kclb+1) % 4 == 0 and kclb+1 != len(clebsches):
                self.addString(' \\notag \\\\ &')

    def generateRHS(self,Y,indices,noThreeJ=False):
        """Generate a LaTeX output"""

        # Simplifies indices
        for idx in indices:
            idx.simplify()

        # Alignment symbol
        self.addString('&')

        # Overall Sign
        self.addRHSSign(indices)

        # Deltas
        self.addRHSDeltas(Y.deltas)

        # Single-particle phases
        self.addRHSPhases(indices)

        # Jhat
        self.addRHSJhats(indices)

        # 3j-Symbols
        if not noThreeJ:
            self.addRHSThreeJs(Y.threejs)

        # 6j-Symbols
        self.addRHSSixJs(Y.sixjs)


    def addRHSSign(self,indices):
        """Add overall sign"""

        overallSign = 1
        for idx in indices:
            overallSign *= idx.sign
        if overallSign == -1:
            self.addString('-')

    def addRHSDeltas(self,deltas):
        """Add deltas"""

        for delta in deltas:
            self.addString(str(delta))

    def addRHSPhases(self,indices):
        """Add phases"""

        firstIdx = True
        for idx in indices:
            if idx.mphase != 0:
                if not idx.zero:
                    print("Error: There should not be M projection left for summed indices")
            if idx.jphase != 0:
                if firstIdx:
                    self.addString('(-1)^{')
                if not firstIdx:
                    self.addString('+' if idx.jphase > 0 else '-')
                if abs(idx.jphase) > 1:
                    self.addString('%i'%(abs(idx.jphase)))
                self.addString(idx.jtex + ' ')
                firstIdx = False

        if not firstIdx:
            self.addString('}')

    def addRHSJhats(self,indices):
        """Add phases"""

        for idx in indices:
            if idx.jhat == 0: continue
            self.addString('\hat{%s}'%(idx.jtex))
            if idx.jhat != 1: self.addString('^{%i}'%(idx.jhat))

    def addRHSThreeJs(self,threejs):
        """Add ThreeJs"""

        for threej in threejs:
            self.addString(str(threej))

    def addRHSSixJs(self,sixjs):
        """Add SixJs"""

        for sixj in sixjs:
            self.addString(str(sixj))

