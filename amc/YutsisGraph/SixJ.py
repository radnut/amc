
class SixJ:
    """6j-symbol class"""

    def __init__(self,idx1,idx2,idx3,idx4,idx5,idx6):
        """Constructor method"""

        # J indices
        # { idx1 idx2 idx3 }
        # { idx4 idx5 idx6 }
        self.indices = [idx1,idx2,idx3,idx4,idx5,idx6]

    def containsThreeJ(self,threej):
        """Check if the 6j-symbol already contains
        the corresponding triangular inequality"""

        # Get positions of indices of the 3j-symbol in the 6j-symbol
        positions = []
        for k,idx1 in enumerate(self.indices):
            for idx2 in threej.indices:
                if idx1 == idx2:
                    positions.append(k)

        # If three indices match look for a triangular inequality
        if len(positions) == 3:
            positions.sort()
            if positions in [[0,1,2],[0,4,5],[1,3,5],[2,3,4]]:
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
        nint = 0
        for idx in self.indices:
            if idx.type == 'int':
                nint += 1

        # According to the number of integer indices
        if nint not in [2,3,6]:
            print("Error: Not a valid SixJ symbol !")
        elif nint == 2:
            if self.indices[0].type == 'int':
                self.indices = [self.indices[1],self.indices[2],self.indices[0],self.indices[4],self.indices[5],self.indices[3]]
            if self.indices[1].type == 'int':
                self.indices = [self.indices[0],self.indices[2],self.indices[1],self.indices[3],self.indices[5],self.indices[4]]
        elif nint == 3:
            hintTab = []
            for k,idx in enumerate(self.indices[:3]):
                if idx.type == 'hint':
                    hintTab.append(k)
            if len(hintTab) not in [0,2]:
                print("Error: Not a valid 3-integers SixJ symbol !")
            elif len(hintTab) == 2:
                self.indices[hintTab[0]],self.indices[hintTab[0]+3] = self.indices[hintTab[0]+3],self.indices[hintTab[0]]
                self.indices[hintTab[1]],self.indices[hintTab[1]+3] = self.indices[hintTab[1]+3],self.indices[hintTab[1]]

        # In the two-integers case:
        # Put three-body index in the fifth position
        if nint == 2:
            for k,idx in enumerate(self.indices[0:2]+self.indices[3:5]):
                if idx.type != 'hint':
                    print("Error: Not a valid 2-integers 6j-symbol")
                if not idx.partIdx:
                    if k == 0:
                       self.indices[0],self.indices[1],self.indices[3],self.indices[4] = self.indices[4],self.indices[3],self.indices[1],self.indices[0]
                    elif k == 1:
                        self.indices[0],self.indices[1],self.indices[3],self.indices[4] = self.indices[3],self.indices[4],self.indices[0],self.indices[1]
                    elif k == 2:
                        self.indices[0],self.indices[1],self.indices[3],self.indices[4] = self.indices[1],self.indices[0],self.indices[4],self.indices[3]
                    break

    @classmethod
    def getPreamble(cls):
        """Get the newcommand line for Latex output"""

        return '\\newcommand{\\sixj}[6]{\\begingroup\\setlength{\\arraycolsep}{0.2em}\\begin{Bmatrix} #1 & #2 & #3 \\\\ #4 & #5 & #6 \\end{Bmatrix}_{\\text{6j}}\\endgroup}\n'

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        sixjTex = '\sixj'
        for idx in self.indices:
            sixjTex += '{%s}'%(idx.jtex)

        return sixjTex

