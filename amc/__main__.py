"""Main routine of the Angular Momentum Coupling."""

from __future__ import (division, absolute_import, print_function)

import argparse
import os.path
import datetime

import amc.output
import amc.parser
import amc.reduction


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
    parser.add_argument('--collect-ninejs', action='store_true', help='Build 9j-coefficients from products of 6j-coefficients.')
    parser.add_argument('--keep-trideltas', action='store_true', help='Print triangular deltas.')
    parser.add_argument('--wet-convention', choices=['wigner', 'sakurai'], default='wigner',
                        help='Convention used for Wigner-Eckart reduced matrix elements.')
    parser.add_argument('--wet-scalar', action='store_true',
                        help='Reduce scalar matrix elements. Default is to use the unreduced form for scalar tensors.')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-v', '--verbose', action='count', help='Increase verbosity', default=0)

    args = parser.parse_args()

    return args


def main():
    """Launch the AMC program."""

    print(
        "#############################\n"
        "# Angular Momentum Coupling #\n"
        "#           v0.1            #\n"
        "#                           #\n"
        "#      by AMC Dev Team      #\n"
        "#############################\n"
    )

    # Parse command line
    run_arguments = parse_command_line()

    # Text
    parser = amc.parser.Parser(optimize=True)
    with open(run_arguments.source) as f:
        parser.parse(f.read(), debug=0)
    if run_arguments.verbose > 0:
        print('# Known Tensors #')
        for tensor in parser.tensors.values():
            print(tensor)
        print()
        print('# Equations #')
        for eqn in parser.equations:
            print('Original')
            print(eqn)
            print()
            eqn_permuted = eqn.expand_permutations()
            print('Permuted')
            print(eqn_permuted)
            print()
            eqn_expanded = eqn_permuted.expand()
            print('Expanded')
            print(eqn_expanded)
            print()
    equations = parser.equations

    # Output file
    if run_arguments.output is None:
        dirname, basename = os.path.split(run_arguments.source)
        if '.' in basename:
            basename = basename.rsplit('.', 1)[0] + '.tex'
        else:
            basename = basename + '.tex'
        output_file = os.path.join(dirname, basename)
    else:
        output_file = run_arguments.output[0]

    # Start computing
    print("Running...")
    start_time = datetime.datetime.now()

    results = []

    # Angular-momentum reduction
    for i, equation in enumerate(equations):
        print("Equation {0:3d}/{1:3d}...".format(i + 1, len(equations)), flush=True)
        res = amc.reduction.reduce_equation(
            equation,
            collect_ninejs=run_arguments.collect_ninejs,
            convention=run_arguments.wet_convention,
            wet_scalar=run_arguments.wet_scalar)
        results.append(res)

    output = amc.output.latex.equations_to_document(results, print_triangulardeltas=run_arguments.keep_trideltas)

    with open(output_file, 'wt') as f:
        f.write(output)

    print("Time elapsed: %s.\n" % (datetime.datetime.now() - start_time))

    print("AMC ended successfully!")


if __name__ == "__main__":
    main()

