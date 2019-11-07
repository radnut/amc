
class NineJ:
    """9j-symbol class"""

    def __init__(self,idx1,idx2,idx3,idx4,idx5,idx6,idx7,idx8,idx9):
        """Constructor method"""

        # J indices
        # { idx1 idx2 idx3 }
        # { idx4 idx5 idx6 }
        # { idx7 idx8 idx9 }
        self.indices = [idx1,idx2,idx3,idx4,idx5,idx6,idx7,idx8,idx9]

    @classmethod
    def getPreamble(cls):
        """Get the newcommand line for Latex output"""

        return '\\newcommand{\\ninej}[9]{\\begingroup\\setlength{\\arraycolsep}{0.2em}\\begin{Bmatrix} #1 & #2 & #3 \\\\ #4 & #5 & #6 \\\\ #7 & #8 & #9 \\end{Bmatrix}_{\\text{9j}}\\endgroup}\n'

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        ninejTex = '\\ninej'
        for idx in self.indices:
            ninejTex += '{%s}'%(idx.jtex)

        return ninejTex

