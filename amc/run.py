"""Routines handling the run of AMC."""

import argparse

def parse_command_line():
    """Return run commands from the Command Line Interface.

    Returns:
        (Namespace): Appropriate commands to manage the program's run.

    """

    parser = argparse.ArgumentParser(
        description="ANGULAR MOMENTUM COUPLING v0.1\n\n"
        + "Perform angular-momentum coupling on the given equations"
        + "and return the result as a LaTeX file.")

    parser.add_argument('source', help='input file')
    parser.add_argument('-b', '--binary', action='store_true', help='Input source file in binary format.')
    parser.add_argument('-o', '--output', nargs=1, help='output file')
    parser.add_argument('-p', '--permute', choices=['yes', 'no', 'smart'], default='smart',
                      help='Permute tensor indices to find simpler formulas. `smart\' tries only the ones that are probable to succeed.')
    parser.add_argument('--print_threej', action='store_true', help='Print 3j-coefficients.')
    parser.add_argument('--select_equation', default=None,
                      help='Select a specific equation (Use for debuging purpose).')
    parser.add_argument('--select_term', default=None,
                      help='Select a specific term of an equation (Use for debuging purpose).')
    parser.add_argument('--select_permutation', default=None,
                      help='Select a permutation of a term (Use for debuging purpose).')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-v', '--verbose', action='count', help='Increase verbosity', default=0)

    args = parser.parse_args()

    return args

