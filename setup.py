"""Installation script for the Angular Momentum Coupling program.

You can install the program either by running
    pip install <folder>
or
    python setup.py install
"""

from setuptools import setup, find_packages
import amc

import distutils.command.build_py

with open("README.rst", "r") as fh:
    long_description = fh.read()

    # PyPI complains that it cannot find a Pygments lexer for "none"... seriously?
    long_description = long_description.replace(
        '.. code-block:: none',
        '.. code-block::'
        )

    # PyPI rejects the README because of a MathJax warning... seriously?
    long_description = long_description.replace(
        '.. math::',
        '.. code-block:: latex'
        )

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
        url="https://github.com/radnut/amc",
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
