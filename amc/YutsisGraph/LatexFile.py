
class LatexFile:
    """Class for Latex output"""

    def __init__(self,_filename):
        """Constructor method"""

        # Content of the latex file
        self.latexstr = ''

        # Name of the latex file
        self.filename = _filename

        # Add preamble
        self.addPreamble()

    def addString(self,_str):
        """Add string to latexstr"""

        self.latexstr += _str

    def addPreamble(self):
        """Add LaTeX preamble"""

        # Document class and packages
        self.addDocumentClassAndPackages()

        # Macros
        self.addMacros()

        # Begin document
        self.beginDocument()

    def addDocumentClassAndPackages(self):
        """Add document class and packages"""

        self.addString('\\documentclass[11pt]{article}\n')
        self.addString('\\usepackage[left=1cm,right=1cm,top=1.5cm,bottom=1cm,includeheadfoot]{geometry}\n')
        self.addString('\\usepackage{amsmath}\n')
        self.addString('\\allowdisplaybreaks\n\n')

    def addMacros(self):
        """Add macros"""

        pass

    def beginDocument(self):
        """Beginning of LaTeX document"""

        self.addString('\\begin{document}\n\n')

    def endDocument(self):
        """Ending of LaTeX document"""

        self.addString('\\end{document}\n')

    def __str__(self):
        """Return Latex String"""

        return self.latexstr

    def writeLatexFile(self):
        """Write final latexstring to LaTeX output file"""

        # End document
        self.endDocument()

        # Open, write and close latex file
        fp = open(self.filename,"w+")
        fp.write(self.latexstr)
        fp.close()

