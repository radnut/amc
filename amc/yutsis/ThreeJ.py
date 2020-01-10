from __future__ import (division, absolute_import, print_function)


class ThreeJ:
    """3j-symbol class"""

    def __init__(self, idx1, idx2, idx3):
        """Constructor method"""

        # J indices
        # { idx1 idx2 idx3 }
        self.indices = (idx1, idx2, idx3)

    @classmethod
    def getPreamble(cls):
        """Get the newcommand line for Latex output"""

        return '\\newcommand{\\threej}[3]{\{#1,#2,#3\}}\n'

    def __str__(self):
        """Generate the corresponding LaTeX code"""

        threejTex = r"\threej"
        for idx in self.indices:
            threejTex += "{%s}" % (idx.name)

        return threejTex
