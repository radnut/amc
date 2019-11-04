
class MTensor:
    """MTensor class"""

    def __init__(self,_indices,_I,_J,_symbol,_scalar=True,_after=None):
        """Constructor method"""

        # Amplitude indices
        self.indices = _indices
        for idx in self.indices:
            if not idx.partIdx:
                print("Error: MScheme amplitude contains non-particle indices")

        # Amplitude I,J
        self.I = _I
        self.J = _J

        # Amplitude LaTeX symbol
        self.symbol = _symbol

        # Scalar character
        self.scalar = _scalar

        # After
        self.after = _after

        # Amplitude rank
        self.rank = self.I + self.J

        # Amplitude sign (when using the permutation algorithm)
        self.sign = +1

    def timeReversalPhase(self):
        """Add coupled-form time-reversal phase"""

        I = self.I
        rank = self.rank
        indices = self.indices
        if I < rank//2:
            for idx in indices[I:rank//2]:
                idx.jphase += 1
                idx.mphase -= 1
        else:
            for idx in indices[rank//2:I]:
                idx.jphase += 1
                idx.mphase += 1

    def __str__(self):
        """Return LaTeX string"""

        texStr = self.symbol
        if len(self.indices) != 0:
            texStr += "_{"
            for idx in self.indices:
                texStr += idx.tex
            texStr += "}"
        if self.after != None:
            texStr += self.after

        return texStr

