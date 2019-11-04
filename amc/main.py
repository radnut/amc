#!/usr/bin/env python3

"""Main routine of the Angular Momentum Coupling."""

import os.path
import pickle
import datetime
import run
import frontend
import AMCReduction

def main():
    """Launch the AMC program."""

    print(
        "#############################\n"
        + "# Angular Momentum Coupling #\n"
        + "#           v0.1            #\n"
        + "#                           #\n"
        + "#      by AMC Dev Team      #\n"
        + "#############################\n"
    )

    # Parse command line
    run_arguments = run.parse_command_line()

    # Input file
    if run_arguments.binary:
        # Binary
        with open(run_arguments.source,"rb") as fp:
            equations = pickle.load(fp)
    else:
        # Text
        parser = frontend.Parser(optimize=0)
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
                print('Drudged')
                print(eqn_expanded.to_drudge())
                print()
                print()
        equations = [ eqn.to_drudge() for eqn in parser.equations ]

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

    # Permutation option
    if run_arguments.permute == 'smart':
        permute = True
        permute_smart = True
    elif run_arguments.permute == 'yes':
        permute = True
        permute_smart = False
    else:
        permute = False
        permute_smart = False

    # Select options
    select_equation    = run_arguments.select_equation
    select_term        = run_arguments.select_term
    select_permutation = run_arguments.select_permutation
    if select_equation is not None:
        select_equation = int(select_equation)
    if select_term is not None:
        select_term = int(select_term)
    if select_permutation is not None:
        select_permutation = int(select_permutation)

    # Verbose option
    verbose = run_arguments.verbose > 0

    # Start computing
    print("Running...")
    start_time = datetime.datetime.now()

    # Angular-momentum reduction
    AMCReduction.AMCReduction(equations, output_file, doPermutations=permute, doSmartPermutations=permute_smart, verbose=verbose, keqnMaster=select_equation, ktermMaster=select_term, kpermMaster=select_permutation)

    print("Time elapsed: %s.\n" % (datetime.datetime.now() - start_time))

    print("AMC ended successfully!")

if __name__ == "__main__":
    main()

