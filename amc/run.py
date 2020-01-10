"""Routines handling the run of AMC."""
from __future__ import (division, absolute_import, print_function)

import argparse


def parse_command_line():
    """Return run commands from the Command Line Interface.

    Returns:
        (Namespace): Appropriate commands to manage the program's run.

    """

    parser = argparse.ArgumentParser(
        description=
        "ANGULAR MOMENTUM COUPLING v0.1\n\n"
        "Perform angular-momentum coupling on the given equations"
        "and return the result as a LaTeX file.")

    parser.add_argument('source', help='input file')
    parser.add_argument('-o', '--output', nargs=1, help='output file')
    parser.add_argument('-p', '--permute', choices=['yes', 'no', 'smart'], default='smart',
                      help="Permute tensor indices to find simpler formulas. `smart' tries only the ones that are probable to succeed.")
    parser.add_argument('--collect-ninejs', action='store_true', help='Build 9j-coefficients from products of 6j-coefficients.')
    parser.add_argument('--print-threejs', action='store_true', help='Print 3j-coefficients.')
    parser.add_argument('--select-equation', default=None,
                      help='Select a specific equation (Use for debugging purpose).')
    parser.add_argument('--select-term', default=None,
                      help='Select a specific term of an equation (Use for debugging purpose).')
    parser.add_argument('--select-permutation', default=None,
                      help='Select a permutation of a term (Use for debugging purpose).')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-v', '--verbose', action='count', help='Increase verbosity', default=0)

    args = parser.parse_args()

    return args

