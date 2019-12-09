# -*- coding: utf-8 -*-
"""Installation script for the Angular Momentum Coupling program.

You can install the program either by running
    pip2 install <folder>
or
    python2 setup.py install
"""

from setuptools import setup, find_packages
import amc

import distutils.command.build_py

# Override build_py command.
class BuildPyCommand(distutils.command.build_py.build_py):
    def run(self):
        distutils.command.build_py.build_py.run(self)

        # Build lex and parser tabs.
        import amc.frontend
        import os.path

        outputdir = os.path.join(self.build_lib, 'amc', 'frontend')
        amc.frontend.Parser(outputdir=outputdir)

        self.byte_compile((os.path.join(outputdir, '_parsetab.py'), os.path.join(outputdir, '_lextab.py')))

setup(
        name     = "amc",
        version  = "0.1",
        packages = find_packages(),
        install_requires = [],

        # Metadata
        author       = amc.__author__,
        author_email = amc.__email__,
        description  = "",
        keywords     = "",
        url          = "",
        classifiers  = [],

        entry_points=dict(
            console_scripts=[
                "amc = amc.__main__:main"
            ]
        ),

        cmdclass={"build_py": BuildPyCommand},
)

#import sys
#from setuptools import setup, find_packages
#import amc
#
#main_dependencies = [
#    "setuptools"
#]
#
#for dep in main_dependencies:
#    try:
#        __import__(dep)
#    except ImportError:
#        print(
#            "Error: You do not have %s installed, please\n"
#            "       install it. For example doing\n"
#            "\n"
#            "       pip2 install %s\n" % (dep, dep)
#        )
#        sys.exit(1)
#
#setup(
#        name="amc",
#        version="0.1",
#        packages=find_packages(),
#)

#setup(
#    name='amc',
#    version=amc.__version__,
#    maintainer='Julien Ripoche',
#    maintainer_email='julien.ripoche@protonmail.com',
#    author=amc.__author__,
#    author_email=amc.__email__,
#    license=amc.__license__,
#    url='https://github.com/amcproject/amc',
#    install_requires=[
#    #    "networkx>=2.0",
#    #    "numpy",
#    #    "scipy",
#    ],
#    python_requires='>=2.7.1',
#    extras_require=dict(
#        # List additional groups of dependencies here (e.g. development
#        # dependencies). You can install these using the following syntax:
#        # $ pip2 install -e .[develop]
#        develop=[
#        #    'pytest',
#        #    'pytest-cov',
#        #    'roman',
#        #    'sphinx',
#        #    'sphinx_rtd_theme',
#        ]
#    ),
#    classifiers=[
#        'Development Status :: 4 - Beta',
#        'Intended Audience :: Developers',
#        'Intended Audience :: End Users/Desktop',
#        'Intended Audience :: Science/Research',
#        'Natural Language :: English',
#        'Operating System :: MacOS',
#        'Operating System :: POSIX',
#        'Operating System :: Unix',
#        'Programming Language :: Python :: 2.7',
#        'Topic :: Scientific/Engineering',
#        'Topic :: Scientific/Engineering :: Chemistry',
#        'Topic :: Scientific/Engineering :: Physics',
#    ],
#    description="",
#    #'A powerful diagram generator and evaluator for many-body '
#    #            'formalisms in physics and chemistry',
#    long_description="",
#    #'AMC is a tool generating diagrams and producing their '
#    #                 'expressions for given many-body formalisms. Diagrammatic '
#    #                 'rules from the formalism are combined with graph theory '
#    #                 'objects to produce diagrams and expressions in a fast, '
#    #                 'simple and error-safe way.\n\n'
#    #                 'The only input consists in the theory and order of '
#    #                 'interest, and the N-body character of the operators of '
#    #                 'interest. The main output is a LaTeX file containing the '
#    #                 'diagrams, their associated expressions and additional '
#    #                 'informations that can be compiled by AMC if needed. '
#    #                 'Other computer-readable files may be produced as well.',
#    keywords=[
#        'physics',
#        'chemistry',
#        'theory',
#        'many-body',
#    #    'diagram',
#    #    'cli',
#    #    'batch'
#    ],
#    packages=[
#        "amc",
#    ],
#    data_files=[
#
#    #    ("share/doc/amc/", [
#    #        "README.md",
#    #    ]),
#
#    #    ("share/man/man1", [
#    #        "doc/build/man/amc.1",
#    #    ]),
#
#    ],
#    entry_points=dict(
#        console_scripts=[
#            'amc=amc.main:main'
#        ]
#    ),
#    platforms=['linux', 'osx'],
#)
