
class Delta:
    """Delta class"""

    def __init__(self,_idx1,_idx2):
        """Constructor method"""

        # Tuple of two indices
        self.indices = [_idx1,_idx2]

        # Sort according to tex of jtex
        self.sortAccordingToTex()

    def sortAccordingToTex(self):
        """Sort indices"""

        self.indices.sort(key = lambda idx: ((0 if idx.zero else 1),(0 if idx.external else 1),(0 if idx.partIdx else 1),len(idx.jtex),idx.jtex))

    def apply(self):
        """Apply the delta"""

        if self.indices[0].type != self.indices[1].type:
            print("Error: Delta is applied between indices of different types")
        self.indices[0].jphase += self.indices[1].jphase
        self.indices[0].mphase += self.indices[1].mphase
        self.indices[0].sign   *= self.indices[1].sign
        self.indices[0].jhat   += self.indices[1].jhat
        self.indices[1].setDefault()

    def __str__(self):
        """String"""

        stringTemplate = '\delta_{%s %s}'
        return stringTemplate%(self.indices[0].jtex, self.indices[1].jtex)

