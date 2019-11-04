
class ThreeJ:
    """3j-symbol class"""

    def __init__(self,idx1,idx2,idx3):
        """Constructor method"""

        # J indices
        # { idx1 idx2 idx3 }
        self.indices = (idx1,idx2,idx3)

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        return "\{%s,%s,%s\}"%(self.indices[0].jtex,self.indices[1].jtex,self.indices[2].jtex)

