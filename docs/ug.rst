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
-------------------
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
    The code exploits the aditional constraints on angular momenta of the creator and annihilator indices, and uses Wigner-Eckart unreduced matrix elements by default (this behavior can be changed by an option of the ``amc`` command).
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
    - ``((1,-4),(3,-2))`` is the coupling scheme of a cross-coupled mode-4 tensor, similar to a Pandya transformation, where the first creator is coupled to the time-reversed second annihilator, and the first annihilator is coupled to the second creator.
latex
    Optional property.
    Specifies the LaTeX code to use for this tensor.
    May only include sub- or superscripts if the tensor is mode-0, i.e., an ordinary number.


The ``amc`` Command
-------------------

