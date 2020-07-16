# Copyright (C) 2020  Julien Ripoche, Alexander Tichai, Roland Wirth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Error classes for the AMC package."""

class Error(Exception):
    """Base class for all AMC exceptions."""
    pass

class ReductionError(Error):
    """Exception signaling an error during the angular-momentum reduction.

    Parameters
    ----------
    lhs : `amc.ast.Variable`
        Left-hand side of the corresponding equation.
    term : `amc.ast.AST`
        Term that caused the error.
    term_number : `int`
        Index the term inside its equation (0-based).
    """

    def __init__(self, term, lhs, term_number=None):
        self.term = term
        self.lhs = lhs
        self.term_number = term_number

    def __str__(self):
        if self.term_number is not None:
            return 'term {}: {!s} <- {!s}'.format(self.term_number, self.lhs, self.term)
        else:
            return 'term: {!s} <- {!s}'.format(self.lhs, self.term)


class GraphNotReducibleError(Error):
    """Exception signaling that the Yutsis graph could not be completely reduced."""
    pass


class GraphNotOrientableError(Error):
    """Exception signaling that the Yutsis graph is not orientable.

    Parameters
    ----------
    offending_pairs : `set` of `amc.yutsis.ThreeJM` pairs
        Set of pairs that could not be properly oriented. The second member of
        the pair could not be oriented to fulfill its constraints. The first
        member that provided the constraint that, if fulfilled, violates a constraint from another or the same 3jm symbol.
    """
    def __init__(self, offending_pairs):
        self.offending_pairs = offending_pairs

    def __str__(self):
        return 'offending pairs: {}'.format(', '.join(
            '{!s} <> {!s}'.format(a, b) for a, b in self.offending_pairs))

