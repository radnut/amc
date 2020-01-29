"""Installation script for the Angular Momentum Coupling program.

You can install the program either by running
    pip install <folder>
or
    python setup.py install
"""

long_description = """
In quantum many-body theory, one often encounters problems with rotational
symmetry. While methods are most conveniently derived in schemes that do not
exploit the symmetry, a symmetry-adapted formulation can lead to orders of
magnitude savings in computation time. However, actually reducing the formulas
of a many-body method to symmetry-adapted form is tedious and error-prone.

The AMC package aims to help practitioners by automating the reduction
process. The unreduced (m-scheme) equations can be entered via an easy-to-use
language. The package then uses Yutsis graph techniques to reduce the
resulting network of angular-momentum variables to irreducible Wigner 6j and
9j symbols, and outputs the reduced equations as a LaTeX file. Moreover, the
package is based on abstract representations of the unreduced and reduced
equations in the form of syntax trees, which enable other uses such as
automatic generation of code that computes the reduced equations.
"""

from setuptools import setup, find_packages
import amc

import distutils.command.build_py

# Override build_py command.
class BuildPyCommand(distutils.command.build_py.build_py):
    def run(self):
        distutils.command.build_py.build_py.run(self)

        # Build lex and parser tabs.
        import amc.parser
        import os.path

        outputdir = os.path.join(self.build_lib, 'amc', 'parser')
        amc.parser.Parser(outputdir=outputdir)

        self.byte_compile((os.path.join(outputdir, '_parsetab.py'), os.path.join(outputdir, '_lextab.py')))

setup(
        name="amc",
        use_scm_version=True,
        packages=find_packages(),
        install_requires=[],
        setup_requires=['setuptools_scm'],
        python_requires='>=3',

        # Metadata
        author=amc.__author__,
        description="Automatic angular-momentum reduction",
        long_description=long_description,
        long_description_content_type="text/x-rst",
        keywords=[
            'angular momentum',
            'symbolic computation'
            ],
        url="",
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Scientific/Engineering :: Chemistry',
            'Topic :: Scientific/Engineering :: Physics',
            ],

        entry_points=dict(
            console_scripts=[
                "amc = amc.__main__:main"
            ]
        ),

        cmdclass={"build_py": BuildPyCommand},
)
