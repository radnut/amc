
class Idx:
    """Angular-momentum index class"""

    def __init__(self,_type='hint',_tex=None,_jtex=None,_mtex=None,_zero=False,_external=False):
        """Constructor method"""

        # Properties
        self.type = _type
        self.zero = _zero
        self.external = _external

        # LaTeX output
        self.tex = _tex
        if self.tex != None:
            self.jtex = 'j_{%s}'%(self.tex)
            self.mtex = 'm_{%s}'%(self.tex)
        elif _jtex != None and _mtex != None:
            self.jtex = _jtex
            self.mtex = _mtex
        else:
            print("Error: Index creation LaTeX issue")

        # Sign, phase and jhat factors
        self.setDefault()

        # Tex != None for particle indices
        self.partIdx = _tex is not None

        # To treat deltas in equations
        self.hasbeendelta = None

    def simplify(self):
        """Simplify the phases"""

        # Zero
        if self.zero:
            self.setDefault()

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

    def setDefault(self):
        """Set default values"""

        self.jphase = 0
        self.mphase = 0
        self.sign = 1
        self.jhat = 0

    def __str__(self):
        """String"""

        stringTemplate = "%10s  %10s  sign=%2i  phase=(-1)^{%2ij + %2im}  jhat=%2i  type=%4s  zero=%5r  external=%5r"
        return stringTemplate%(self.jtex, self.mtex, self.sign, self.jphase, self.mphase, self.jhat, self.type, self.zero, self.external)
