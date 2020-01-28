User's Guide
============

This is a short user's guide explaining the construction of AMC files and the use of the ``amc`` command.

.. contents:: Contents
   :local:
   :backlinks: none

AMC Files
---------
AMC files describe the equations that should be angular-momentum reduced.
An AMC file is a mix of tensor declarations and equations.
Tensor declarations make a tensor known to the system and give its properties, like its coupling scheme, whether it is a scalar or not, or the symbol to use in LaTeX output.
The equations establish relations between tensor variables in unreduced form.

AMC files distinguish between a few data types: integers and fractions, booleans, tuples, and strings. Integers and fractions are written as numbers.
Fractions are denoted by a slash between numerator and denominator: ``3/4``.
Acceptable values for booleans are ``true`` and ``false``, where the first letter may be capitalized.
Tuples are comma-separated lists delimited by parentheses, ``(1,2,3)``, and may contain integers or nested tuples only.
Strings are delimited by double quotes: ``"string"``.
Embedded double quotes and newlines must be escaped by a backslash.
Backslashes before these characters, as well as before the backslash itself, are removed; all others are retained.
Comments are introduced by the pound sign, ``#``, and last to the end of the line.

Tensor Declarations
^^^^^^^^^^^^^^^^^^^
A tensor declaration has the following form:

.. code-block:: none

    declare T2 {
        mode = 4,
        scalar = true,
        diagonal = false,
        scheme = ((1,2),(3,4)),
        latex = "T",
    }

The ``declare`` keyword introduces the name (``T2`` in the example) of the tensor so it can be used in equations following the declaration.
Additionally, it provides the AMC system with the properties of the tensor. Currently, the following properties are known:

mode
    Required property.
    The mode of the tensor is the number of indices that the tensor needs.
    There are two ways to specify the mode: as an even integer or as a tuple ``(a,b)``.
    The latter declares the tensor to have ``a`` creator and ``b`` annihilator indices.
    The simple integer specification provides the total number of indices and assumes that half are creator indices and half are annihilator indices.
scalar
    Optional property (default ``true``).
    Boolean signalling that the tensor is a scalar (rank-0) tensor.
    Scalar tensors are treated slightly different from nonscalar tensors:
    The code exploits the aditional constraints on angular momenta of the creator and annihilator indices, and uses Wigner-Eckart unreduced matrix elements by default (this behavior can be changed by the ``reduce`` option).
reduce
    Optional property (default ``false`` for scalar tensors)
    Boolean signalling that reduced matrix elements should be used for this scalar operator.
    Ignored on nonscalar tensors, which always use reduced matrix elements.
diagonal
    Optional property (default ``false``).
    Boolean declaring a tensor as diagonal. Diagonal tensors have only half the indices their ``mode`` specifies and no coupling scheme.
    They behave as trivial scalars.
    An example for a diagonal tensor is an occupation number in a theory formulated in natural orbitals.
scheme
    Optional property.
    Describes the coupling scheme of the tensor.
    The tensor's scheme consists of nested two-element tuples.
    Each tuple describes the coupling of two angular momenta.

    If an element of a tuple is an integer, the angular momentum to be coupled is that of an index of the tensor (``1`` denotes the first index, ``2`` the second, etc.).
    The integer may be negated to signal that the time-reversed state should be coupled.
    The time-reversed state is obtained by reversing the projection, and multiplying by a phase :math:`(-1)^{j-m}`.

    If the element is itself a tuple, the angular momentum to be coupled is the angular momentum the elements of that tuple were coupled to.
    The top-level angular momenta are coupled with the rank of the tensor, according to the Wigner-Eckart theorem, constraining both to be the same if the tensor is scalar.

    If the scheme property is not present, a coupling scheme is assumed where the creator and annihilator indices are each coupled from left to right.

    Examples:

    - ``(((1,2),3),((4,5),6))`` is the default coupling scheme for a mode-6 tensor.
    - ``((1,-4),(3,-2))`` is the coupling scheme of a cross-coupled mode-4 tensor, similar to a Pandya transformation, where the first creator is coupled with the time-reversed second annihilator index, and the first annihilator is coupled with the time-reversed second creator index.
latex
    Optional property.
    Specifies the LaTeX code to use for this tensor.
    May only include sub- or superscripts if the tensor is mode-0, i.e., an ordinary number.


Equations
^^^^^^^^^
Equations are written in the usual way:

.. code-block:: none

    T2_abcd = - 1/2 * sum_ij(U2_abij * V2_ijcd);

Equations may span multiple lines and must be terminated by a semicolon ``;``.
The left-hand side of the equation must be a single tensor variable, and defines the properties of the result, like the desired coupling scheme, by naming the result tensor, as well as the external indices for the right-hand side.
The right-hand side is a general expression involving tensor variables, made up of additions, substractions, and multiplications (``+``, ``-``, ``*``).
Division is not supported, except in the form of fractions.

Aside from numbers, the building blocks for expressions are:

_`Subscripts`
    Subscripts appear on `sum operators`_ and `tensor variables`_.
    They may be specified simply as an underscore followed by a set of single-character indices, ``_abcd``, or as an underscore followed by a braced, space-separated list of multi-character indices, such as ``_{k1 k2 k3}``.
    Index names may consist of letters and digits.
    It is not recommended to have numbers as indices, because they will produce the same angular-momentum variables as those produced by indices generated during the reduction.
_`Tensor variables`
    Tensor variables are instances of a known tensor. They are constructed by attaching a subscript to the name of a known tensor, like ``T2_abcd``. The number of subscripts provided has to be the number of subscripts expected by the tensor.
_`Sum operators`
    Sum operators indicate a summation over a set of indices.
    They are introduced by the keyword ``sum`` followed by a subscript indicating the affected indices.
    The summed expression follows in parentheses:

    .. code-block:: none

        sum_abij(U_abij*U_ijab)

    The sum operator marks the affected indices as internal.
    The right-hand side of an equation must depend on all of the external indices that the left-hand side provides.
_`Permutation operators`
    Permutation operators are a tool to simplify the entering of equations into the program.
    Often, expressions must be explicitly antisymmetrized in order to make the result tensor antisymmetric.
    Permutation operators assist with this effort by generating the antisymmetrizing terms automatically.

    In its basic form, a permutation operator ``P(ij)`` transposes two indices in the part of the product to the right of it.
    With this form, one can build simple antisymmetrizers like ``(1-P(ij))*A_i*B_j``, generating ``A_i*B_j - A_j*B_i``.

    The advanced form of the operator accepts multiple sets of indices separated by forward slashes, ``P(ij/k)``.
    These expand to all distinct permutations of indices between the different sets:

    .. code-block:: none

        P(ij/k) = 1 - P(ik) - P(jk),
        P(i/j)  = 1 - P(ij).

    The operator ``P(i/j/k)`` expands to the six permutations of the set :math:`\{i,j,k\}`.
    Index sets can also be given as brace-delimited lists, as in ``P({k1}/{k2})``.

The ``amc`` Command
-------------------
The ``amc`` command is the command-line frontend of the package.
It parses the input file, performs the reduction, and writes the reduced equations to a LaTeX file.

Aside from the required input file, ``amc`` accepts the following optional arguments:

  -h, --help            Show a help message and exit.
  -o OUTPUT, --output OUTPUT
                        Output file
  --collect-ninejs      Build 9j-coefficients from products of 6j-coefficients.
  --print-threejs       Print 3j-coefficients.
  --wet-convention      ``{wigner,sakurai}``.
                        Convention used for Wigner-Eckart reduced matrix elements.
  -V, --version         show program's version number and exit
  -v, --verbose         Increase verbosity

By default, ``amc`` creates a ``.tex`` file with the same basename and in the same directory as the input file.

The ``collect-ninejs`` option activates a post-processing step during which products of three 6j symbols are coalesced into a 9j symbol.
This often makes the expressions shorter but can hinder the identification of intermediates, e.g., when one of the 6j symbols only depends on the quantum numbers of one tensor.

The ``print-threejs`` option activates the output of triangular inequality constraints (3j symbols) that were generated during the reduction.
Mostly, these constraints reproduce constraints that can be inferred from the tensors themselves, so the do not add information.
Redundant constraints that are implicit in 6j or 9j symbols are never printed.

The ``wet-convention`` switches between different definitions of the Wigner-Eckart reduced matrix element of a tensor, and thus between definitions of the Wigner-Eckart theorem.
Currently, ``amc`` supports two conventions:

wigner
    .. math::

        \langle j'm'|T^\lambda_\mu|jm\rangle = (-1)^{2\lambda} \langle jm,\lambda\mu|j'm'\rangle \frac{(j'\|T^\lambda\|j)}{\sqrt{2j'+1}}

    The wigner convention is also used, e.g., by Edmonds, Racah, and Varshalovich.
sakurai
    .. math::

        \langle j'm'|T^\lambda_\mu|jm\rangle = \langle jm,\lambda\mu|j'm'\rangle \frac{(j'\|T^\lambda\|j)}{\sqrt{2j+1}}

The ``wigner`` convention is chosen by default.
