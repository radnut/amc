
class TwelveJSecond:
    """12j(II)-symbol class"""

    def __init__(self,idx1,idx2,idx3,idx4,idx5,idx6,idx7,idx8,idx9,idx10,idx11,idx12):
        """Constructor method"""

        # J indices
        # {   -   idx1  idx2  idx3 }
        # { idx4    -   idx5  idx6 }
        # { idx7  idx8    -   idx9 }
        # { idx10 idx11 idx12   -  }
        self.indices = [idx1,idx2,idx3,idx4,idx5,idx6,idx7,idx8,idx9,idx10,idx11,idx12]

    @classmethod
    def getPreamble(cls):
        """Get the newcommand line for Latex output"""

        # /!\ package version - condition for preamble ???

        return '\\usepackage{listofitems}\n'+'\\newcommand{\\twelvejsecond}[1]{\\setsepchar{,}\\readlist\\args{#1}\\begingroup\\setlength{\\arraycolsep}{0.2em}\\begin{Bmatrix} - & \\args[1] & \\args[2] & \\args[3] \\\\ \\args[4] & - & \\args[5] & \\args[6] \\\\ \\args[7] & \\args[8] & - & \\args[9] \\\\ \\args[10] & \\args[11] & \\args[12] & - \\end{Bmatrix}_{\\text{12j(II)}}\\endgroup}\n'

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        ninejTex = '\\twelvejsecond{'
        for k,idx in enumerate(self.indices):
            ninejTex += '%s'%(idx.jtex)
            if k != 11:
                ninejTex += ','
        ninejTex += '}'

        return ninejTex

