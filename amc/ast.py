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

"""Abstract Syntax Tree classes.

The ast module provides classes necessary to build abstract syntax trees for
reduced and unreduced equations.
"""

from __future__ import (absolute_import, print_function, division)

import fractions

from . import _util


class AST(object):
    """An Abstract Syntax Tree node.

    The AST node is the basic building block of the abstract syntax tree that
    represents unreduced and reduced equations. Access to a node's children is
    provided by subscripting:

    >>> node = AST('node')
    >>> node[:] = [AST('child')]
    >>> node[0].type
    'child'
    >>> len(node), len(node[0])
    (1, 0)

    Parameters
    ----------
    type : `str`
        The type of the node. Used for traversing the AST.

    Attributes
    ----------
    type : `str`
        The type of the node. Used for traversing the AST.
    """
    __slots__ = ('type', '_kids',)

    def __init__(self, type):
        self.type = type
        self._kids = None

    def __getitem__(self, i):
        if self._kids is None:
            raise IndexError
        return self._kids[i]

    def __len__(self):
        return len(self._kids) if self._kids is not None else 0

    def __setitem__(self, i, val):
        if self._kids is None:
            self._kids = []
        self._kids[i] = val


class ASTTraverser(object):
    """Base class for implementing AST traversers.

    This class provides the basic facilities for traversing an AST in pre- or
    post-order. It supports two modes of operation:

    The first mode is activated by invoking the static method `traverse` on
    the root of the tree and providing two functions ``preaction`` and
    ``postaction``. The ``preaction`` function is called for each node before
    its children, ``postaction`` is called after its children have been
    traversed.

    The second mode can be used by subclassing `ASTTraverser`: for each type
    of AST node (according to the `AST.type` attribute), the methods
    ``n_<type>`` and ``n_<type>_exit`` can be implemented. These methods will
    be called before and after visiting the children of a node of the given
    type. Additionally, methods named ``default`` and ``default_exit`` can be
    provided, which will be called when the node does not have a ``type``
    attribute or no type-specific method has been provided.

    In both modes, preactions may call the static `prune` method to signal
    that the node children should not be traversed. The postaction for this
    node will still be called.
    """

    class _PruneError(Exception):

        def __init__(self, params=None):
            self.params = params

    @staticmethod
    def traverse(root, preaction=(lambda n, **k: None),
                 postaction=(lambda n, r, **k: None)):
        """
        traverse(root, preaction=(lambda n, **k: None), postaction=(lambda n, r, **k: None))

        Traverse the AST represented by the given `root` node.

        Parameters
        ----------
        root : `AST`
            The root node of the AST to traverse.

        preaction : callable
            Function to be called before visiting the given node's children.

            **Parameters**

            - ``node`` :
                Current node.
            - ``**kwargs`` :
                Additional keyword arguments passed from the parent.

            Optionally, kwargs to the node's postaction and the children's
            preactions can be provided by returning a dict-like object. The
            root preaction is called without parameters.

        postaction : callable
            Function to be called after visiting the given node's children.

            **Parameters**

            - ``node``:
                Current node.
            - ``results``:
                List of return values of of all children's postactions, in
                order.
            - ``**kwargs``:
                Additional keyword arguments passed from the preaction.

            The return value of this function is appended to a list that is
            passed to the parent's postaction.

        Returns
        -------
        result
            The return value of the root node's postaction.

        See Also
        --------
        prune : To skip traversing a node's children.
        """
        stack = [ (root, 'pre', None) ]

        results = []

        while stack:

            node, state, params = stack.pop()

            if state == 'pre':
                prune = False

                try:
                    if params is not None:
                        params = preaction(node, **params)
                    else:
                        params = preaction(node)
                except ASTTraverser._PruneError as e:
                    prune = True
                    params = e.params

                stack.append((node, 'post', (params, results)))
                results = []

                if isinstance(node, AST) and not prune:
                    for child in reversed(node):
                        stack.append((child, 'pre', params))
            elif state == 'post':
                params, parent_results = params
                if params is not None:
                    result = postaction(node, results, **params)
                else:
                    result = postaction(node, results)

                results = parent_results
                results.append(result)

        return results[0]

    def start(self, root):
        """Start the AST traversal.

        Starts the AST traversal beginning with the ``root``. This method is
        intended for use with subclasses of `ASTTraverser`. For each node
        visited, it looks for the method ``n_<type>`` and ``n_<type>_exit``,
        respectively to use as pre- and postactions. If no appropriate methods
        are found or the node does not have a ``type`` attribute, ``default``
        or ``default_exit`` is called, both of which default to doing nothing.

        Parameters
        ----------
        root : `AST`
            The root node of the AST to traverse.

        Returns
        -------
        result
            The return value of the root's postaction.
        """
        default_pre = getattr(self, 'default', lambda n, **k: None)
        default_post = getattr(self, 'default_exit', lambda n, r, **k: None)

        def _pre(n, **k):
            if hasattr(n, 'type'):
                method = getattr(self, 'n_' + n.type, default_pre)
            else:
                method = default_pre
            return method(n, **k)

        def _post(n, r, **k):
            if hasattr(n, 'type'):
                method = getattr(self, 'n_' + n.type + '_exit', default_post)
            else:
                method = default_post
            return method(n, r, **k)

        return self.traverse(root, preaction=_pre, postaction=_post)

    @staticmethod
    def prune(params=None):
        """Stop processing the current node's children.

        .. warning :: Must be called from a preaction and does not return.

        Parameters
        ----------
        params : `dict`
            Dictionary of kwargs to pass to the postaction.
        """
        raise ASTTraverser._PruneError(params)


class TensorDeclaration(AST):
    """Tensor declaration node.

    A node that declares a tensor, enabling its use in variables.

    .. note:: `TensorDeclaration` nodes have type ``declare``.

    Parameters
    ----------
    name : `str`
        Name of the tensor.
    mode : `int` or 2-tuple of `int`
        Mode of the tensor, specifies the number and type of indices. If
        ``mode`` is an integer, it has to be even, and it is assumed that the
        tensor has ``mode // 2`` creator and ``mode // 2`` annihilator
        indices.

        If ``mode`` is a 2-tuple, the first and second members give the number
        of creator and annihilator indices, respectively.
    scalar : `bool`
        `True` if tensor has rank zero, `False` otherwise.
    reduce : `bool`
        If `True`, use reduced matrix elements even if the tensor is scalar.
        Has no effect on nonscalar tensors because these are always reduced.
    diagonal : `bool`
        Flag signaling that the tensor is diagonal. A diagonal tensor only has
        half as many indices as its mode suggests, and no coupling scheme.
    scheme : 2-tuple, optional
        Coupling scheme of the tensor. If omitted, a default scheme is
        generated by coupling indices left-to-right. If given, must be a tree
        of 2-tuples with integers as leaves.

        The coupling scheme is specified as follows: each index on the tensor
        is assigned a number, starting at ``1``. A tuple of integers indicates
        that the angular momenta of the respective indices should be coupled
        to some collective angular momentum. An integer may be negated to
        indicate coupling of the time-reversed state. A tuple containing a
        tuple indicates coupling of the collective angular momenta to a new
        angular momentum. The top-level angular momenta are coupled to the
        tensor rank.

        **Example**

            ``((1,2),3)`` couples 1 and 2 to J0, and J0 and 3 to J1.
            ``((1,-4),(3,-2))`` couples 1 and time-reversed 4 to J0, 3 and
            time-reversed 2 to J1, and J0 and J1 to J2 (the rank of the
            tensor).

    **kwargs
        Additional arguments, stored as a dict in the ``attrs`` attribute.
    """

    def __init__(self, name, mode, scalar=True, reduce=False, diagonal=False, scheme=None, **kwargs):
        super(TensorDeclaration, self).__init__('declare')

        try:
            if len(mode) != 2:
                raise ValueError('mode must be a nonnegative integer or a 2-tuple')
            else:
                mode = tuple(mode)
        except TypeError:
            try:
                if mode < 0:
                    raise ValueError('mode must be a nonnegative integer or a 2-tuple')
                else:
                    if mode % 2 == 0:
                        mode = (mode // 2,) * 2
            except TypeError:
                raise TypeError('mode must be a nonnegative integer or a 2-tuple')

        if scheme is not None:
            if len(scheme) != 2:
                raise ValueError('scheme must be a 2-tuple')

            scheme = self._check_scheme(scheme, 1, mode[0] + mode[1])
        else:
            if mode[0] and mode[1]:
                scheme = (self._create_scheme(1, mode[0]), self._create_scheme(mode[0] + 1, mode[1]))
            else:
                scheme = self._create_scheme(1, max(mode[0], mode[1]))

        self.name = name
        self.mode = mode
        self.totalmode = sum(mode)
        self.scalar = scalar
        self.reduce = reduce or not scalar
        self.diagonal = diagonal
        self.scheme = scheme
        self.attrs = kwargs

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Tensor {0.name} {{mode={0.mode}, scalar={0.scalar}, reduce={0.reduce} diagonal={0.diagonal}, scheme={0.scheme} }}'.format(self)

    @staticmethod
    def _check_scheme(scheme, start, num):
        idxs = set(range(start, start + num))

        def _rec(sub):
            try:
                if start <= abs(sub) < start + num:
                    if abs(sub) not in idxs:
                        raise ValueError('duplicate index {0} in scheme'.format(sub))
                    idxs.remove(abs(sub))
                    return sub
                else:
                    raise ValueError('unexpected index {0} in scheme, expected number between {1} and {2}, inclusive'.format(abs(sub), start, start + num - 1))
            except TypeError:
                pass

            if len(sub) != 2:
                raise ValueError('couplings have to be specified by 2-tuples. Offending part {0!s} of {1!s}'.format(sub, scheme))
            else:
                return (_rec(sub[0]), _rec(sub[1]))

        if num == 0:
            return ()

        return _rec(scheme)

    @staticmethod
    def _create_scheme(start, num):
        if num == 0:
            return ()
        elif num == 1:
            return start
        else:
            return (TensorDeclaration._create_scheme(start, num - 1), start + num - 1)


class Equation(AST):
    """Equation node.

    Represents a reduced or unreduced equation.

    .. note:: `Equation` nodes have type ``equation``.

    Parameters
    ----------
    lhs : `Variable` or `ReducedVariable`
        Left-hand side of the equation. Must be a variable.
    rhs : `AST`
        Right-hand side of the equation. Can be any expression.
        The left-hand side introduces a set of indices, which must be the only
        free indices on the right-hand side.

    Attributes
    ----------
    lhs : `Variable` or `ReducedVariable`
        Left-hand side of the equation.
    rhs : `AST`
        Right-hand side of the equation. Can be any expression.
    """

    def __init__(self, lhs, rhs):
        super(Equation, self).__init__('equation')
        if not isinstance(lhs, (Variable, ReducedVariable)):
            raise ValueError('left-hand side of equation must be a variable')

        if hasattr(rhs, 'depends_on') and lhs.depends_on < rhs.depends_on:
            raise ValueError('right-hand side of equation depends on more indices than left-hand side provides')

        self.lhs = lhs
        self.rhs = rhs
        self[:] = (lhs, rhs)

    def __str__(self):
        return '{0} = {1};'.format(self.lhs, self.rhs)

    def expand_permutations(self):
        """Expand permutation operators in expressions.

        Expands permutation operators, turning them into sums over products of
        permuted expressions.

        Returns
        -------
        new_eqn : `AST`
            New, expanded equation or ``self`` if expansion did not change the
            right-hand side.
        """
        if not self.rhs.contains_perm:
            return self

        new_rhs = self.rhs.expand_permutations()
        if id(new_rhs) == id(self.rhs):
            return self
        return Equation(self.lhs, new_rhs)

    def expand(self, keep_diagonal=True):
        """Expand the equation.

        Expands the right-hand side of the equation into a sum of products.

        Parameters
        ----------
        keep_diagonal : `bool`
            If set, keeps diagonal subterms, like sums of diagonal tensors,
            unexpanded.

        Returns
        -------
        new_eqn : `AST`
            New, expanded equation or ``self`` if expansion did not change the
            right-hand side.
        """
        new_rhs = self.rhs.expand(keep_diagonal)
        if id(new_rhs) == id(self.rhs):
            return self
        return Equation(self.lhs, new_rhs)


class Index(object):
    """Index object.

    Represents a tensor index.

    Parameters
    ----------
    name : str
        Name of the index.
    type : {'int', 'hint'}
        Type of the index. Must be 'int' for integer indices, or 'hint' for
        half-integers.
    class_ : {'am', 'part'}
        Index class. Must be 'am' for simple angular-momentum indices, or
        'part' for particle indices. 'part' indicates that the index ranges
        over the full single-particle basis instead of just an angular
        momentum.

    Attributes
    ----------
    name : str
        Name of the index.
    type : {'int', 'hint'}
        Type of the index. Must be 'int' for integer indices, or 'hint' for
        half-integers.
    class_ : {'am', 'part'}
        Index class. Must be 'am' for simple angular-momentum indices, or
        'part' for particle indices. 'part' indicates that the index ranges
        over the full single-particle basis instead of just an angular
        momentum.
    constrained_to : `Index` or `None`
        Index object that this index is constrained to via a delta constraint.
    """

    def __init__(self, name, type, class_):
        if type not in ('int', 'hint'):
            raise ValueError("Type must be 'int' or 'hint'")

        if class_ not in ('am', 'part'):
            raise ValueError("Type must be 'am' or 'part'")

        self.name = str(name)
        self.type = type
        self.class_ = class_
        self.constrained_to = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @staticmethod
    def coupled_type(i1, i2):
        """Get the coupled type for an index pair.

        Parameters
        ----------
        i1, i2 : `Index`
            The indices to couple.

        Returns
        -------
        cptype : `str`
            The index type resulting from coupling ``i1`` and ``i2`` together.
        """
        if (i1.type == 'hint' and i2.type == 'hint') or (i1.type == 'int' and i2.type == 'int'):
            return 'int'
        return 'hint'


class Variable(AST):
    """Unreduced tensor variable node.

    .. note:: `Variable` nodes have type ``variable``.

    Parameters
    ----------
    tensor : `TensorDeclaration`
        The tensor that this variable belongs to.
    subscripts : `tuple` of `Index`
        List of subscripts. Length must be compatible with ``tensor.mode``.

    Attributes
    ----------
    tensor : `TensorDeclaration`
        The tensor that this variable belongs to.
    subscripts : `tuple` of `Index`
        List of subscripts.
    depends_on : `set` of `Index`
        Set of the subscript indices.
    """

    def __init__(self, tensor, subscripts):
        super(Variable, self).__init__('variable')

        if (not tensor.diagonal and len(subscripts) != tensor.totalmode) or (tensor.diagonal and len(subscripts) != tensor.totalmode // 2):
            raise ValueError(
                'Expected {totalmode} subscripts on tensor "{name}", got {nsubscripts}'.format(
                    totalmode=(tensor.totalmode if not tensor.diagonal else tensor.totalmode // 2), name=tensor.name, nsubscripts=len(subscripts)))

        self.tensor = tensor
        self.subscripts = tuple(subscripts)
        self.depends_on = set(self.subscripts)

        if any(not isinstance(i, Index) for i in self.subscripts):
            raise ValueError('subscripts must be AST indices.')

    def __str__(self):
        return '{0}_{{{1}}}'.format(self.tensor.name, ' '.join(map(str, self.subscripts)))

    def apply_permutation(self, i, j):
        """Permute two indices.

        Parameters
        ----------
        i, j : `Index`
            Indices to permute.

        Returns
        -------
        new_var
            New variable with indices ``i`` and ``j`` exchanged, or ``self``
            if the Variable is independent of both.
        """
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        subst = {i: j, j: i}

        new_subscripts = tuple(subst.get(s, s) for s in self.subscripts)
        return Variable(self.tensor, new_subscripts)


class ReducedVariable(AST):
    """Reduced tensor variable node.

    .. note:: `ReducedVariable` nodes have type ``reducedvariable``.

    Parameters
    ----------
    tensor : `TensorDeclaration`
        The tensor that this variable belongs to.
    subscripts : `tuple` of `Index`
        List of subscripts. Length must be compatible with ``tensor.mode``.
    labels : `tuple` of `Index`
        List of additional angular-momentum labels. Must be compatible with
        ``tensor.scheme``.

    Attributes
    ----------
    tensor : `TensorDeclaration`
        The tensor that this variable belongs to.
    subscripts : `tuple` of `Index`
        List of subscripts.
    labels : `tuple` of `Index`
        List of additional angular-momentum labels.
    depends_on : `set` of `Index`
        Set of the subscript and label indices.
    """

    def __init__(self, tensor, subscripts, labels):
        super(ReducedVariable, self).__init__('reducedvariable')

        if (not tensor.diagonal and len(subscripts) != tensor.totalmode) or (tensor.diagonal and len(subscripts) != tensor.totalmode // 2):
            raise ValueError(
                'Expected {totalmode} subscripts on tensor "{name}", got {nsubscripts}'.format(
                    totalmode=(tensor.totalmode if not tensor.diagonal else tensor.totalmode // 2), name=tensor.name, nsubscripts=len(subscripts)))

        self.tensor = tensor
        self.subscripts = tuple(subscripts)
        self.labels = tuple(labels)
        self.depends_on = set(self.subscripts) | set(self.labels)

        if any(not isinstance(i, Index) for i in self.subscripts):
            raise ValueError('subscripts must be AST indices.')

        if any(not isinstance(l, Index) for l in self.labels):
            raise ValueError('labels must be AST indices.')

    def __str__(self):
        return '{0}_{{{1}}}^{{{2}}}'.format(self.tensor.name, ' '.join(map(str, self.subscripts)), ' '.join(map(str, self.labels)))

    def apply_permutation(self, i, j):
        """Permute two indices.

        Parameters
        ----------
        i, j : `Index`
            Indices to permute.

        Returns
        -------
        new_var
            New variable with indices ``i`` and ``j`` exchanged, or ``self``
            if the ReducedVariable is independent of both.
        """
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        subst = {i: j, j: i}

        new_subscripts = tuple(subst.get(s, s) for s in self.subscripts)
        new_labels = tuple(subst.get(s, s) for s in self.labels)
        return ReducedVariable(self.tensor, new_subscripts, new_labels)


class TriangularDelta(AST):
    """Triangular delta node.

    Represents a triangular inequality between three indices.

    .. note:: `TriangularDelta` nodes have type ``triangulardelta``.

    Parameters
    ----------
    indices : 3-tuple of `Index`
        Indices constrained by the 3j symbol.

    Attributes
    ----------
    depends_on : `set` of `Index`
        Set of the three indices.
    indices : 3-tuple of `Index`
        Indices constrained by the 3j symbol.
    """

    def __init__(self, indices):
        super(TriangularDelta, self).__init__('triangulardelta')

        self.indices = tuple(indices)

        if len(self.indices) != 3:
            raise ValueError('indices list must have three elements.')

        if any(not isinstance(i, Index) for i in self.indices):
            raise ValueError('elements of the indices list must be AST indices.')

        if sum(1 if i.type == 'int' else 0 for i in self.indices) not in (1, 3):
            raise ValueError('incompatible indices (must be of hhi or iii type).')

        self.depends_on = set(self.indices)

    def __str__(self):
        return 'TriangularDelta({})'.format(' '.join(map(str, self.indices)))


class SixJ(AST):
    """6j node.

    Represents a Wigner 6j symbol.

    .. note:: `SixJ` nodes have type ``sixj``.

    Parameters
    ----------
    indices : 6-tuple of `Index`
        Indices of the 6j symbol.

    Attributes
    ----------
    depends_on : `set` of `Index`
        Set of the indices.
    indices : 6-tuple of `Index`
        Indices of the 6j symbol.
    """

    def __init__(self, indices):
        super(SixJ, self).__init__('sixj')

        self.indices = tuple(indices)

        if len(self.indices) != 6:
            raise ValueError('indices list must have six elements.')

        if any(not isinstance(i, Index) for i in self.indices):
            raise ValueError('elements of the indices list must be AST indices.')

        if sum(1 if i.type == 'int' else 0 for i in self.indices) not in (2, 3, 6):
            raise ValueError('incompatible indices (must be of hhi,hhi; iii,hhh, or iii,iii type).')

        self.depends_on = set(self.indices)

    def __str__(self):
        return 'SixJ({})'.format(' '.join(map(str, self.indices)))


class NineJ(AST):
    """9j node.

    Represents a Wigner 9j symbol.

    .. note:: `NineJ` nodes have type ``ninej``.

    Parameters
    ----------
    indices : 9-tuple of `Index`
        Indices of the 9j symbol.

    Attributes
    ----------
    depends_on : `set` of `Index`
        Set of the indices.
    indices : 9-tuple of `Index`
        Indices of the 9j symbol.
    """

    def __init__(self, indices):
        super(NineJ, self).__init__('ninej')

        self.indices = tuple(indices)

        if len(self.indices) != 9:
            raise ValueError('indices list must have nine elements.')

        if any(not isinstance(i, Index) for i in self.indices):
            raise ValueError('elements of the indices list must be AST indices.')

        self.depends_on = set(self.indices)

    def __str__(self):
        return 'NineJ({})'.format(' '.join(map(str, self.indices)))


class DeltaJ(AST):
    """DeltaJ node.

    Represents a delta constraint on angular momenta.

    .. note:: `DeltaJ` nodes have type ``deltaj``.

    Parameters
    ----------
    a, b : `Index`
        Indices to be constrained.

    Attributes
    ----------
    a, b : `Index`
        Constrained indices.
    depends_on : `set` of `Index`
        Set of the two constrained indices.
    """

    def __init__(self, a, b):
        super(DeltaJ, self).__init__('deltaj')
        self.a = a
        self.b = b
        self.depends_on = {a, b}

    def __str__(self):
        return 'DeltaJ({0!s},{1!s})'.format(self.a, self.b)


class HatPhaseFactor(AST):
    """Combined node for hat and phase factors.

    Represents the terms :math:`(-1)^{xj+ym} (\\sqrt{2j+1})^z`.

    .. note:: `HatPhaseFactor` nodes have type ``hatphasefactor``.

    Parameters
    ----------
    index : `Index`
        Index associated with the hat-phase factor.
    hatpower : integer
        Power of the hat factor :math:`\\sqrt{2j+1}`.
    jphase : integer
        Multiplier of ``j`` in the phase factor.
    mphase : integer
        Multiplier of ``m`` in the phase factor.
    sign : {+1, -1}
        Overall sign.

    Notes
    -----
    The constructor might return an `int` or a `Mul`.

    Attributes
    ----------
    index : `Index`
        Index associated with the hat-phase factor.
    hatpower : integer
        Power of the hat factor :math:`\\sqrt{2j+1}`.
    jphase : integer
        Multiplier of ``j`` in the phase factor.
    mphase : integer
        Multiplier of ``m`` in the phase factor.
    """

    def __init__(self, index, hatpower=0, jphase=0, mphase=0, sign=1):
        pass

    def __new__(cls, index, hatpower=0, jphase=0, mphase=0, sign=1):
        if index.type == 'int':
            jphase %= 2
            mphase %= 2
        else:
            jphase %= 4
            mphase %= 4

            if jphase // 2 == 1:
                sign *= -1
                jphase -= 2

            if mphase // 2 == 1:
                sign *= -1
                mphase -= 2

        if jphase == 0 and mphase == 0 and hatpower == 0:
            return sign

        obj = super(HatPhaseFactor, cls).__new__(cls)
        super(HatPhaseFactor, obj).__init__('hatphasefactor')
        obj.index = index
        obj.depends_on = {index}
        obj.hatpower = hatpower
        obj.jphase = jphase
        obj.mphase = mphase

        if sign != 1:
            return Mul([sign, obj])
        else:
            return obj

    def __str__(self):
        return 'hat({0!s}, {1}, {2}j{3:+d}m)'.format(self.index, self.hatpower, self.jphase, self.mphase)


class Add(AST):
    """Add node.

    Represents an addition of terms.

    .. note:: `Add` nodes have type ``add``.

    Parameters
    ----------
    terms : iterable
        Terms to add.

    Notes
    -----
    The constructor simplifies the terms, removing zeros and splicing contents
    of `Add` objects. It may, therefore, not return an `Add` object at all,
    e.g., if there is only one term.

    Attributes
    ----------
    contains_perm : bool
        Flag to signal that at least one term contains a permutation operator.
    depends_on : `set` of `Index`
        Set of all indices the terms depend on.
    """

    def __init__(self, terms):
        pass

    def __new__(cls, terms):
        cleaned_terms = []
        depends_on = set()
        for t in terms:
            try:
                if t == 0:
                    continue
                if isinstance(t, Add) and len(t) == 1 and t[0] == 0:
                    continue
            except TypeError:
                pass

            if hasattr(t, 'depends_on'):
                depends_on |= t.depends_on

            if isinstance(t, Add):
                cleaned_terms += t[:]
            else:
                cleaned_terms.append(t)

        if len(cleaned_terms) == 0:
            return 0
        elif len(cleaned_terms) == 1:
            return cleaned_terms[0]

        obj = super(Add, cls).__new__(cls)
        super(Add, obj).__init__('add')
        obj[:] = cleaned_terms
        obj.depends_on = depends_on
        obj.contains_perm = any(hasattr(t, 'contains_perm') and t.contains_perm for t in cleaned_terms)
        return obj

    def __str__(self):
        return ' + '.join(str(k) for k in self)

    def is_diagonal(self):
        """Check if all variables contained in terms are diagonal.

        Returns
        -------
        True if all terms are diagonal.
        """

        def _rec(t):
            if isinstance(t, Variable):
                return t.tensor.diagonal
            elif not isinstance(t, AST):
                return True
            else:
                return all(_rec(tt) for tt in t)

        return _rec(self)

    def distribute(self, terms, side='right', keep_diagonal=True):
        """Apply the distributive law to turn a `Mul` of `Add` into an `Add`
        of `Mul`.

        Parameters
        ----------
        terms : `list` of `AST`
            Factors of the product to distribute.
        side : {'left', 'right'}
            Indicates whether the ``terms`` are on the left or right side of
            this `Add`.
        keep_diagonal : bool
            If True, keeps diagonal terms undistributed.

        Returns
        -------
        An `Add` or `Mul` instance containing the distributed terms.
        """
        if not terms:
            return self

        if keep_diagonal:
            if self.is_diagonal():
                if side == 'right':
                    return Mul([self] + terms)
                else:
                    return Mul(terms + [self])

        if side == 'right':
            new_terms = [ Mul([k] + terms) for k in self ]
        else:
            new_terms = [ Mul(terms + [k]) for k in self ]
        return Add(new_terms)

    def expand_permutations(self):
        """Expand permutation operators in terms.

        Expands permutation operators, turning them into sums over products of
        permuted expressions.

        Returns
        -------
        new_add : `Add`
            New, expanded `Add` or ``self`` if expansion did not change
            the object.
        """
        if not self.contains_perm:
            return self

        changed = False
        terms = []
        for t in self:
            if hasattr(t, 'contains_perm') and t.contains_perm:
                new_term = t.expand_permutations()
                if id(new_term) != id(t):
                    changed = True
                    terms.append(new_term)
                    continue
            terms.append(t)

        if changed:
            return Add(terms)
        else:
            return self

    def apply_permutation(self, i, j):
        """Permute two indices in all terms.

        Parameters
        ----------
        i, j : `Index`
            Indices to permute.

        Returns
        -------
        new_add : `Add`
            New `Add` with indices ``i`` and ``j`` exchanged, or ``self`` if
            the object is independent of both.
        """
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        changed = False
        terms = []
        for t in self:
            if hasattr(t, 'apply_permutation'):
                new_term = t.apply_permutation(i, j)
                if id(new_term) != id(t):
                    changed = True
                    terms.append(new_term)
                    continue
            terms.append(t)

        if changed:
            return Add(terms)
        else:
            return self

    def expand(self, keep_diagonal=True):
        """Expand the terms of the `Add`.

        Expands each term into a sum of products.

        Parameters
        ----------
        keep_diagonal : `bool`
            If set, keeps diagonal subterms, like sums of diagonal tensors,
            unexpanded.

        Returns
        -------
        new_add : `Add`
            New, expanded `Add` or ``self`` if expansion did not change the
            terms.
        """
        changed = False
        terms = []
        for t in self:
            if hasattr(t, 'expand'):
                new_term = t.expand(keep_diagonal)
                if id(new_term) != id(t):
                    changed = True
                    terms.append(new_term)
                    continue
            terms.append(t)

        if changed:
            return Add(terms)
        else:
            return self


class Mul(AST):
    """Multiplication node.

    Represents a multiplication of factors.

    .. note:: `Mul` nodes have type ``mul``.

    Parameters
    ----------
    terms : iterable
        Factors to multiply.

    Notes
    -----
    The constructor cleans up the list of terms, removing factors of one,
    splicing `Mul` factors, and collecting numerical factors. Depending on the
    nature and number of factors, the resulting object may not be a `Mul`.

    Attributes
    ----------
    contains_perm : bool
        Flag to signal that at least one factor contains a permutation operator.
    depends_on : `set` of `Index`
        Set of all indices the factors depend on.
    """

    def __init__(self, terms):
        pass

    def __new__(cls, terms):
        cleaned_terms = []
        depends_on = set()
        for t in terms:
            if hasattr(t, 'depends_on'):
                depends_on |= t.depends_on

            if isinstance(t, Mul):
                cleaned_terms += t[:]
            else:
                cleaned_terms.append(t)

        factored_terms = []
        prefactor = 1
        for t in cleaned_terms:
            if isinstance(t, (int, fractions.Fraction)):
                prefactor *= t
            else:
                factored_terms.append(t)

        if prefactor != 1:
            factored_terms.insert(0, prefactor)

        if len(factored_terms) == 0:
            return 1
        elif len(factored_terms) == 1:
            return factored_terms[0]

        obj = super(Mul, cls).__new__(cls)
        super(Mul, obj).__init__('mul')
        obj[:] = factored_terms
        obj.depends_on = depends_on
        obj.contains_perm = any(hasattr(t, 'contains_perm') and t.contains_perm for t in factored_terms)
        return obj

    def __str__(self):
        factors = []
        for f in self:
            if isinstance(f, (int, fractions.Fraction)):
                if f < 0:
                    factors.append('({})'.format(f))
                else:
                    factors.append(str(f))
            elif isinstance(f, Add):
                factors.append('({})'.format(f))
            else:
                factors.append(str(f))
        return '*'.join(factors)

    def expand_permutations(self):
        """Expand permutation operators in factors.

        Expands permutation operators, turning them into sums of permuted
        expressions.

        Returns
        -------
        new_mul : `Mul`
            New, expanded `Mul` or ``self`` if expansion did not change
            the object.
        """
        if not self.contains_perm:
            return self

        changed = False
        terms = []
        for t in reversed(self):
            if hasattr(t, 'contains_perm') and t.contains_perm:
                # `terms` contains all terms right of `t`. Depending on whether t is a permutation
                # object or not, we apply the permutation directly or distribute all terms right of
                # the operator and repeat the process.
                if isinstance(t, Permute):
                    changed = True
                    terms = [ t.apply_operator(terms) ]
                else:
                    changed = True
                    terms = [ t.distribute(terms).expand_permutations() ]
            else:
                terms.insert(0, t)

        if changed:
            return Mul(terms)
        else:
            return self

    def apply_permutation(self, i, j):
        """Permute two indices in all factors.

        Parameters
        ----------
        i, j : `Index`
            Indices to permute.

        Returns
        -------
        new_mul : `Mul`
            New `Mul` with indices ``i`` and ``j`` exchanged, or ``self`` if
            the object is independent of both.
        """
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        changed = False
        terms = []
        for t in self:
            if hasattr(t, 'apply_permutation'):
                new_term = t.apply_permutation(i, j)
                if id(new_term) != id(t):
                    changed = True
                    terms.append(new_term)
                    continue
            terms.append(t)

        if changed:
            return Mul(terms)
        else:
            return self

    def expand(self, keep_diagonal=True):
        """Expand the factors of the `Mul`.

        Expands all factors, then distributes over each `Add` factor.

        Parameters
        ----------
        keep_diagonal : `bool`
            If set, keeps diagonal subterms, like sums of diagonal tensors,
            unexpanded.

        Returns
        -------
        new_expr
            New, expanded expression. May be ``self`` if the expansion did not
            change anything. In most cases the returned expression is a `Mul`
            without `Add` factors or an `Add` of `Mul` terms.
        """
        has_distributable_terms = False

        expanded_terms = [ t.expand(keep_diagonal) if hasattr(t, 'expand') else t for t in self ]

        terms_right = []
        for t in reversed(expanded_terms):
            if hasattr(t, 'distribute'):
                has_distributable_terms = True

                if not terms_right:
                    terms_right.insert(0, t)
                else:
                    distributed = t.distribute(terms_right, 'right', keep_diagonal)

                    if isinstance(distributed, Mul):
                        terms_right = distributed[:]
                    else:
                        terms_right = [ distributed ]
            else:
                terms_right.insert(0, t)

        if not has_distributable_terms:
            return self

        terms = []
        for t in terms_right:
            if hasattr(t, 'distribute'):
                distributed = t.distribute(terms, 'left', keep_diagonal)

                if isinstance(distributed, Mul):
                    terms = distributed[:]
                else:
                    terms = [ distributed ]
            else:
                terms.append(t)

        return Mul(terms)


class Sum(AST):
    """Summation node.

    Represents a sum over indices.

    .. note:: `Sum` nodes have type ``sum``.

    Parameters
    ----------
    subscripts : iterable of `Index`
        Indices that are summed over.
    expression : `AST`
        Body of the sum.

    Notes
    -----
    The constructor cleans up the expression, factoring out factors that do
    not depend on the summed indices, and coalescing sub-sums. Therefore, the
    returned object might be a `Mul` or an `int`.

    Attributes
    ----------
    contains_perm : bool
        Flag to signal that at least one factor contains a permutation operator.
    depends_on : `set` of `Index`
        Indices the expression depends on but are not summed over.
    subscripts : `set` of `Index`
        Indices that are summed over.
    """

    def __init__(self, subscripts, expression):
        pass

    def __new__(cls, subscripts, expression):
        subscripts = set(subscripts)
        depends_on = set()

        if not subscripts:
            return 0

        if isinstance(expression, Mul):
            dependent_factors = []
            independent_factors = []

            for factor in expression:
                if not hasattr(factor, 'depends_on') or subscripts.isdisjoint(factor.depends_on):
                    independent_factors.append(factor)
                else:
                    dependent_factors.append(factor)
                    depends_on |= factor.depends_on

            if independent_factors:
                terms = independent_factors + [Sum(subscripts, Mul(dependent_factors))]
                return Mul(terms)
            else:
                sumnode = super(Sum, cls).__new__(cls)
                super(Sum, sumnode).__init__('sum')
                sumnode[:] = (Mul(dependent_factors),)
                sumnode.subscripts = subscripts
                sumnode.depends_on = depends_on - subscripts
                sumnode.contains_perm = sumnode[0].contains_perm
                return sumnode

        elif isinstance(expression, Sum):
            expression.subscripts |= subscripts
            return expression
        else:
            if hasattr(expression, 'depends_on'):
                depends_on = expression.depends_on

            sumnode = super(Sum, cls).__new__(cls)
            super(Sum, sumnode).__init__('sum')
            sumnode[:] = (expression,)
            sumnode.subscripts = subscripts
            sumnode.depends_on = depends_on - subscripts
            sumnode.contains_perm = hasattr(sumnode[0], 'contains_perm') and sumnode[0].contains_perm
            return sumnode

    def __str__(self):
        return 'sum_{{{0}}}({1!s})'.format(' '.join(sorted(str(s) for s in self.subscripts)), self[0])

    def distribute(self, terms, side='right', keep_diagonal=False):
        """Distribute the sum over the given terms.

        Pulls the given terms into the sum.

        Parameters
        ----------
        terms : `list` of `AST`
            Factors of the product to distribute.
        side : {'left', 'right'}
            Indicates whether the ``terms`` are on the left or right side of
            this `Sum`.
        keep_diagonal : bool
            If True, keeps diagonal terms undistributed.

        Returns
        -------
        new_sum : `Sum`
            A `Sum` containing a `Mul` of the terms with the original
            body.
        """
        if not terms:
            return self

        if side == 'right':
            return Sum(self.subscripts, Mul([self[0]] + terms))
        else:
            return Sum(self.subscripts, Mul(terms + [self[0]]))

    def expand_permutations(self):
        """Expand permutations in the sum body.

        Returns
        -------
        A new `Sum` with permutations expanded, or ``self`` if there are no
        permutations in the body.
        """
        if not self.contains_perm:
            return self

        return Sum(self.subscripts, self[0].expand_permutations())

    def apply_permutation(self, i, j):
        """Permute two indices in the sum body.

        Parameters
        ----------
        i, j : `Index`
            Indices to permute.

        Returns
        -------
        new_sum : `Sum`
            New `Sum` with indices ``i`` and ``j`` exchanged, or ``self`` if
            the object is independent of both.
        """
        ij = {i, j}

        if not ij.isdisjoint(self.subscripts):
            raise ValueError('permutation cannot act on summation dummy indices')

        if not hasattr(self[0], 'apply_permutation') or ij.isdisjoint(self.depends_on):
            return self

        new_expr = self[0].apply_permutation(i, j)
        if id(new_expr) != id(self[0]):
            return Sum(self.subscripts, new_expr)
        else:
            return self

    def expand(self, keep_diagonal=True):
        """Expand the sum body.

        If the body expands to an `Add`, distribute the sum over each term.

        Parameters
        ----------
        keep_diagonal : `bool`
            If set, keeps diagonal subterms, like sums of diagonal tensors,
            unexpanded.

        Returns
        -------
        new_expr
            New, expanded expression. May be ``self`` if the expansion did not
            change anything.
        """
        if not hasattr(self[0], 'expand'):
            return self

        new_expr = self[0].expand(keep_diagonal)
        if not isinstance(new_expr, Add):
            if id(new_expr) != id(self[0]):
                return Sum(self.subscripts, new_expr)
            else:
                return self
        else:
            terms = [ Sum(self.subscripts, t) for t in new_expr  ]
            return Add(terms)


class Permute(AST):
    r"""Permute node.

    Represents a permutation or transposition operator.

    .. note:: `Permute` nodes have type `permute`.

    The permute operator supports two modes of operation: With a single set,
    it acts as a transposition operator. With multiple sets, it generates all
    distinct permutations between indices of different sets, along with the
    appropriate sign of the permutation, e.g.

    .. math::
        P(a/b) &= 1 - P(ab) \\
        P(ab/c) &= 1 - P(ac) - P(bc).

    Parameters
    ----------
    sets : iterable of iterable of `Index`
        Sets of indices to be permuted.

    Attributes
    ----------
    contains_perm : `bool`
        Always `True`.
    depends_on : `set` of `Index`
        Set of all indices appearing in the permute object.
    """

    def __init__(self, sets):
        super(Permute, self).__init__('permute')

        self.sets = tuple(tuple(s) for s in sets)

        if len(self.sets) == 0:
            raise ValueError('need at least one set')
        elif len(self.sets) == 1 and len(self.sets[0]) != 2:
            raise ValueError('Permutation operators with a single set must only permute two indices')

        if any(not isinstance(i, Index) for s in self.sets for i in s):
            raise ValueError('sets must consist of sets of AST indices.')

        self.depends_on = set()
        for s in sets:
            self.depends_on |= s
        self.contains_perm = True

    def __str__(self):
        return 'P({})'.format('/'.join('{{{}}}'.format(' '.join(str(k) for k in s)) for s in self.sets))

    def apply_operator(self, terms):
        """Apply the Permute operator to the provided factors.

        Parameters
        ----------
        terms : iterable
            Factors the `Permute` acts on. It is assumed that the factors
            belong to a `Mul`.

        Returns
        -------
        mul_or_add
            Depending on operation mode, a `Mul` with indices transposed, or
            an `Add` with all generated terms.
        """
        # Transposition-type operator
        if len(self.sets) == 1:
            factors = []
            i, j = self.sets[0]
            for tt in terms:
                if hasattr(tt, 'apply_permutation'):
                    factors.append(tt.apply_permutation(i, j))
                else:
                    factors.append(tt)
            return Mul(factors)

        add_terms = []
        for cycles in sorted(_util.multiset_permutations_cycles(*self.sets), key=len):
            factors = list(terms)
            prefactor = 1
            for cycle in cycles:
                prefactor *= (-1) ** (len(cycle) - 1)

                for k in range(len(factors)):
                    if hasattr(factors[k], 'apply_permutation'):
                        for i, j in _util.pairwise(reversed(cycle)):
                            factors[k] = factors[k].apply_permutation(i, j)

            add_terms.append(Mul([prefactor] + factors))
        return Add(add_terms)

    def apply_permutation(self, i, j):
        """Permute two indices in the permutation sets.

        Parameters
        ----------
        i, j : `Index`
            Indices to permute.

        Returns
        -------
        new_perm : `Permute`
            New `Permute` with indices ``i`` and ``j`` exchanged, or ``self``
            if the object is independent of both, or the permutation had no
            effect.
        """
        ij = {i, j}

        # This permutation is independent of the given indices.
        if ij.isdisjoint(self.depends_on):
            return self

        # If both indices are in the same set, the permutation does nothing.
        for s in self.sets:
            if ij <= s:
                return self

        new_sets = tuple(s.copy() for s in self.sets)
        for s in new_sets:
            if not ij.disjoint(s):
                # The index to be replaced appears in both ij and s and is therefore removed by the
                # symmetric difference. The case that both i and j are in s is excluded because
                # then ij would be a subset of s.
                s ^= ij

        return Permute(new_sets)
