
from amc.MTensor import MTensor
from amc.YutsisGraph import ClebschGordan,Idx

class JTensor(MTensor):
    """JTensor class"""

    def __init__(self,_amp,tensorId,tensorId2,_external=None):
        """Constructor method"""

        # Get MScheme amplitude members
        self.indices = _amp.indices
        self.I,self.J = _amp.I,_amp.J
        self.symbol = _amp.symbol
        self.scalar = _amp.scalar
        self.after = _amp.after
        self.rank = _amp.rank
        self.sign = _amp.sign
        self.external = _external

        # Additional indices
        self.tensorIdx = None
        self.diagonalIdx = None
        self.diagonalIdx2 = None
        self.interIndices = []
        self.setAdditionalIndices(tensorId,tensorId2)

        # Add a tilde for cross-coupling
        if self.rank != 0:
            self.symbol = "\\tilde" + self.symbol

    def setAdditionalIndices(self,tensorId,tensorId2):
        """Set intermediate, diagonal and tensor indices"""

        # Set intermediate indices (A >= 3)
        for idx in range(0,self.rank//2-2):
            idxType = 'int' if idx % 2 == 0 else 'hint'
            self.interIndices.append(Idx(idxType,None,_jtex='J^{(%i)}_{%i%i}'%(tensorId,idx+1,idx+2),_mtex='M^{(%i)}_{%i%i}'%(tensorId,idx+1,idx+2),_external=self.external))
        for idx in range(0,self.rank//2-2):
            idxType = 'int' if idx % 2 == 0 else 'hint'
            self.interIndices.append(Idx(idxType,None,_jtex='J^{(%i)}_{%i%i}'%(tensorId,idx+self.rank//2+1,idx+self.rank//2+2),_mtex='M^{(%i)}_{%i%i}'%(tensorId,idx+self.rank//2+1,idx+self.rank//2+2),_external=self.external))

        # Set diagonal index (A >= 2)
        idxType = 'int' if self.rank % 4 == 0 else 'hint'
        if self.rank >= 4:
            self.diagonalIdx = Idx(idxType,None,_jtex='J^{(%i)}'%(tensorId),_mtex='M^{(%i)}'%(tensorId),_external=self.external)

        # Set tensorial index (if not scalar)
        if not self.scalar:
            self.tensorIdx = Idx('int',None,_jtex='\\lambda^{(%i)}'%(tensorId2),_mtex='\\mu^{(%i)}'%(tensorId2),_external=self.external)
            idxType = 'int' if self.rank % 4 == 0 else 'hint'
            if self.rank >= 4:
                self.diagonalIdx2 = Idx(idxType,None,_jtex='J^{(%i)\'}'%(tensorId),_mtex='M^{(%i)\'}'%(tensorId),_external=self.external)

    def getClebsches(self):
        """Get single-particle phases, jhat factors and Clebsch-Gordan coefficients
        related to the angular-momentum coupled-form of the operator"""

        # Create empty list of clebsches
        clebsches = []

        # If one-body operator
        if self.rank == 2:
            clebsches = self.getOneBodyClebsches()

        # If A-body operator (A>=2)
        if self.rank >= 4:
            clebsches = self.getABodyClebsches()

        # Get tensorial clebsch
        if self.rank >= 4 and not self.scalar:
            clebsches.append(self.getTensorialClebsch())

        # Return clebsches
        return clebsches

    def getTensorialClebsch(self):

        return ClebschGordan([self.diagonalIdx2,self.tensorIdx,self.diagonalIdx],[1,1,1])

    def getOneBodyClebsches(self):
        """Get single-particle phases, jhat factors and Clebsch-Gordan coefficients
        related to the angular-momentum coupled-form of a one-body operator"""

        # Notice that O^{20} and O^{02} have the same recoupling coefficient
        # (O^{20} = O^{02 \, \ast} if O is hermitian)

        # Get the two indices
        idx1 = self.indices[0]
        idx2 = self.indices[1]

        # Add jhat factor
        idx1.jhat += 1

        # Add single-particle phase
        if self.I == 1 and self.J == 1:
            idx1.jphase += 1
            idx1.mphase -= 1

        # Get clebsch signs
        signs = [1,1,1]
        if self.I == 1 and self.J == 1:
            signs = [1,-1,1]

        # Return list of clebsches
        return [ClebschGordan([idx1,idx2,None],signs)]

    def getABodyClebsches(self):
        """Get single-particle phases, jhat factors and Clebsch-Gordan coefficients
        related to the angular-momentum coupled-form of a A-body operator (A >= 2)"""

        # Create empty list of clebsches
        clebsches = []

        # Time-reversal phase
        self.timeReversalPhase()

        # /!\ Only place to be checked for A-body tensor (A>=4)

        # Get clebsches from the left state
        for idx in range(self.rank//2-1):
            # Indices
            if idx==0:
                idx1 = self.indices[idx]
            else:
                idx1 = self.interIndices[idx-1]
            idx2 = self.indices[idx+1]
            if idx==self.rank//2-2:
                idx3 = self.diagonalIdx
            else:
                idx3 = self.interIndices[idx]
            # Signs
            if self.I < self.J:
                if idx==0:
                    if self.I==0:
                        signs = [-1,-1,1]
                    elif self.I==1:
                        signs = [1,-1,1]
                    else:
                        signs = [1,1,1]
                else:
                    if self.I-idx < 2:
                        signs = [1,-1,1]
                    else:
                        signs = [1,1,1]
            else:
                signs = [1,1,1]
            clebsches.append(ClebschGordan([idx1,idx2,idx3],signs))

        # Get clebsches from the right state
        for idx in range(self.rank//2-1):
            # Indices
            if idx==0:
                idx1 = self.indices[idx+self.rank//2]
            else:
                idx1 = self.interIndices[idx+self.rank//2-3]
            idx2 = self.indices[idx+self.rank//2+1]
            if idx==self.rank//2-2:
                idx3 = self.diagonalIdx if self.scalar else self.diagonalIdx2
            else:
                idx3 = self.interIndices[idx+self.rank//2-2]
            # Signs
            if self.I > self.J:
                if idx==0:
                    if self.I==self.J:
                        signs = [1,1,1]
                    elif self.I-self.J ==2:
                        signs = [-1,1,1]
                    else:
                        signs = [-1,-1,1]
                else:
                    if self.I-self.rank//2-idx < 2:
                        signs = [1,1,1]
                    else:
                        signs = [1,-1,1]
            else:
                signs = [1,1,1]
            clebsches.append(ClebschGordan([idx1,idx2,idx3],signs))

        # Return list of clebsches
        return clebsches

    def __str__(self):
        """Return LaTeX string"""

        # LaTeX string
        texStr = ""

        # Diagonal index
        if self.rank == 2:
            texStr += "{}^{%s}"%(self.indices[0].jtex if self.indices[0].hasbeendelta == None else self.indices[0].hasbeendelta.jtex)
        elif self.rank >= 4:
            texStr += "{}^{%s}"%(self.diagonalIdx.jtex)

        # LaTeX symbol
        texStr += self.symbol

        # List of indices
        if len(self.indices) != 0:
            texStr += "_{"
            leftindices = self.indices[:self.rank//2]
            for k,idx in enumerate(leftindices):
                if self.rank == 2:
                    texStr += "n_{%s}"%(idx.tex)
                else:
                    if idx.hasbeendelta == None:
                        texStr += "\\tilde%s"%(idx.tex)
                    else:
                        if idx.hasbeendelta.tex != None:
                            texStr += "n_{%s}(ljt)_{%s}"%(idx.tex,idx.hasbeendelta.tex)
                        else:
                            texStr += "(nlt)_{%s}%s"%(idx.tex,idx.hasbeendelta.jtex)
                if k != 0 and k != len(leftindices)-1:
                    texStr += self.interIndices[k-1].jtex
            if self.rank >= 6:
                texStr += ";"
            rightindices = self.indices[self.rank//2:]
            for k,idx in enumerate(rightindices):
                if self.rank == 2:
                    texStr += "n_{%s}"%(idx.tex)
                else:
                    if idx.hasbeendelta == None:
                        texStr += "\\tilde%s"%(idx.tex)
                    else:
                        if idx.hasbeendelta.tex != None:
                            texStr += "n_{%s}(ljt)_{%s}"%(idx.tex,idx.hasbeendelta.tex)
                        else:
                            texStr += "(nlt)_{%s}%s"%(idx.tex,idx.hasbeendelta.jtex)
                if k != 0 and k != len(leftindices)-1:
                    texStr += self.interIndices[k-1+self.rank//2-2].jtex
            texStr += "}"

        # After
        if self.after != None:
            texStr += self.after

        return texStr

