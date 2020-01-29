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

"""Functions for the AMC reduction of equations."""

import itertools

from . import ast

from . import yutsis


class ReductionError(Exception):
    """Exception signaling that the Yutsis graph could not be completely reduced."""
    pass


def reduce_equation(equation, *, permute=None, collect_ninejs=False,
                    convention='wigner', monitor=lambda t, nt, p, np: None):
    """reduce_equation(equation, *, permute=None, collect_ninejs=False,
                    convention='wigner', monitor=lambda t, nt, p, np: None)

    Reduce the given equation to angular-momentum coupled form.

    Parameters
    ----------
    equation : `ast.Equation`
        Equation to reduce.

    permute : {`False`, `True`, 'smart'}
        .. warning:: Not yet implemented.

        Permute tensor subscripts in order to get a simpler coupled
        expression. If set to 'smart', only try permutations most likely to
        succeed.

    collect_ninejs : `bool`
        Try to construct 9j-symbols from sums over products of 6j-symbols.

    convention : {'wigner', 'sakurai'}
        Use the given convention for Wigner-Eckart reduced matrix elements.

    monitor: callable(term: `int`, nterms: `int`, perm: `int`, nperms: `int`)
        Called once for each permutation processed. `term` and `perm` are
        zero-based.

    Returns
    -------
    amc.ast.Equation
        The angular-momentum reduced equation.

    Raises
    ------
    amc.reduction.ReductionError
        If the Yutsis graph cannot be fully reduced.
    """

    rhs = equation.rhs.expand_permutations().expand()

    if isinstance(rhs, ast.Add):
        terms = rhs
    else:
        terms = [rhs]

    index_number = {'hint': 0, 'int': 0, 'rank': 0}
    zero = ast.Index('0', 'int', 'am')
    aux_ast = generate_auxiliary_ast_indices(equation.lhs, index_number, zero)

    # To arrive at the expression for the symmetry-reduced variable on the
    # left-hand side, we multiply the right-hand side with the coupling
    # Clebsch-Gordan coefficients for the left-hand side and sum over all m
    # quantum numbers. For reduced tensors, the transformation from reduced to
    # unreduced looks identical to its reverse. For unreduced tensors the
    # prefactor is slightly different, which is why we have to pass an
    # additional flag.
    new_lhs = ast.ReducedVariable(equation.lhs.tensor, equation.lhs.subscripts, aux_ast)

    new_terms = []
    nterms = len(terms)
    for t, term in enumerate(terms):
        new_terms.append(
            reduce_term(
                equation.lhs,
                aux_ast,
                term,
                dict(**index_number),
                zero,
                permute=permute,
                collect_ninejs=collect_ninejs,
                convention=convention,
                monitor=lambda p, np: monitor(t, nterms, p, np)))

    new_rhs = ast.Add(new_terms)
    return ast.Equation(new_lhs, new_rhs)


def reduce_term(lhs, aux_lhs_ast, term, index_number, zero_ast, *,
                permute=None, collect_ninejs=False, convention='wigner',
                monitor=lambda p, np: None):
    """reduce_term(lhs, aux_lhs_ast, term, index_number, zero_ast, *,
                   permute=None, collect_ninejs=False, convention='wigner',
                   monitor=lambda p, np: None)

    Reduce a single term into angular-momentum coupled form.

    Parameters
    ----------
    lhs : `ast.Variable`
        Left-hand side of the equation.

    aux_lhs_ast: `list` of `ast.Index`
        Auxiliary indices of the reduced left-hand side tensor.

    term : `ast.Mul` or `ast.Sum`
        Term to reduce. Should be a single sum over a product of tensor
        variables.

    index_number : `dict` {'hint': `int`, 'int': `int`, 'rank': `int`}
        Dictionary holding the counters for automatically generating auxiliary
        indices. Values should be large enough so that new generated names do
        not alias left-hand auxiliary indices.

    zero_ast : `ast.Index`
        Index denoting a zero angular momentum.

    permute : {`False`, `True`, 'smart'}
        .. warning:: Not yet implemented.

        Permute tensor subscripts in order to get a simpler coupled
        expression. If set to 'smart', only try permutations most likely to
        succeed.

    collect_ninejs : `bool`
        Try to construct 9j-symbols from sums over products of 6j-symbols.

    convention : {'wigner', 'sakurai'}
        Use the given convention for Wigner-Eckart reduced matrix elements.

    monitor: callable(perm : `int`, nperms : `int`)
        Called once for each permutation processed. `perm` is zero-based.

    Returns
    -------
    `ast.Sum` or `ast.Mul`
        The angular-momentum reduced term.

    Raises
    ------
    `reduction.ReductionError`
        If the Yutsis graph cannot be fully reduced.
    """

    _check_convention(convention)

    if not isinstance(term, (ast.Sum, ast.Mul)):
        raise ValueError('Term should be (a sum over) a product of factors.')

    # For now, we only consider the original permutation. Call the monitor function once.
    monitor(0, 1)

    internals = set()

    factors = []
    variables = []

    # Traverse the subtree to get all prefactors and variables.
    class ReduceTraverser(ast.ASTTraverser):

        def n_variable(self, n):
            nonlocal variables, factors
            if n.tensor.diagonal:
                factors.append(n)
            else:
                variables.append(n)

        def n_add(self, n):
            nonlocal factors
            if not n.is_diagonal():
                raise ValueError('Term contains a sum of nondiagonal factors.'
                                 ' Expand first.')
            factors.append(n)
            self.prune()

        def n_sum(self, n):
            nonlocal internals
            internals |= n.subscripts

        def n_mul(self, n):
            pass

        def default(self, n):
            nonlocal factors
            factors.append(n)

    ReduceTraverser().start(term)

    external_idx = {i: yutsis.Idx('hint', i.name, is_particle=True, external=True)
                    for i in lhs.depends_on}
    internal_idx = {i: yutsis.Idx('hint', i.name, is_particle=True, external=False)
                    for i in internals}
    aux_idx = []

    zero = yutsis.Idx('int', '0', is_particle=False, zero=True)
    internal_idx[zero_ast] = zero

    idx = dict()
    idx.update(external_idx)
    idx.update(internal_idx)

    clebsches = []
    jvariables = []

    for v in variables:
        cl, aux = variable_to_clebsches(v, idx, convention=convention, lhs=False)
        clebsches += cl
        aux_idx += aux

        jvariables.append((v, aux))

    # save the auxiliary variables created for the RHS for later.
    aux_rhs = aux_idx[:]

    cl_lhs, aux_lhs = variable_to_clebsches(lhs, external_idx, convention=convention,
                                            lhs=True)

    external_idx.update({astidx: idx for astidx, idx in zip(aux_lhs_ast, aux_lhs)})

    clebsches += cl_lhs
    aux_idx = aux_lhs + aux_idx

    # Generate additional tensor-coupling clebsches for nonscalar operators.
    rankindices = [aux[-1] for v, aux in jvariables]
    rankidx_lhs = aux_lhs[-1]

    if len(rankindices) == 1:
        # If there is only one tensor on the right-hand side, its rank has to be identical to the
        # left-hand side rank.

        if not rankindices[0].zero:
            clebsches.append(yutsis.ClebschGordan([rankindices[0], zero, rankidx_lhs], [+1, +1, +1]))

    if len(rankindices) > 1:
        # If there is more than one tensor, we couple them left-to-right to intermediate angular
        # momenta. The final angular momentum is the one on the left-hand side.
        for k, i in enumerate(rankindices):
            if k == 0:
                left_idx = i
                continue

            if not (left_idx.zero and i.zero):
                if k + 1 == len(rankindices):
                    new_idx = rankidx_lhs
                else:
                    new_idx = yutsis.Idx(yutsis.Idx.coupled_type(left_idx, i),
                                        is_particle=False, external=False)
                    aux_idx.append(new_idx)
                clebsches.append(yutsis.ClebschGordan([left_idx, i, new_idx], [+1, +1, +1]))
                left_idx = new_idx
            else:
                left_idx = zero

    Y = yutsis.YutsisReduction(list(idx.values()) + aux_idx, clebsches,
                                    zero)

    if Y.get_number_of_nodes() != 0:
        # Full reduction failed. Until we have permutations, we can only fail here.
        raise ReductionError()

    if collect_ninejs:
        Y.collect_ninejs()

    for sixj in Y.sixjs:
        sixj.canonicalize()
        for i in sixj.indices:
            if i not in internal_idx and i not in external_idx:
                aux_rhs.append(i)
                aux_idx.append(i)

    handle_deltas(Y)

    # Generate a map from Yutsis indices to the AST indices.
    subscript_map = {}
    subscript_map.update({i: astidx for astidx, i in external_idx.items()})
    subscript_map.update({i: astidx for astidx, i in internal_idx.items()})

    # Update constraints on named AST indices.
    for astidx, i in internal_idx.items():
        if i.constrained_to is not None:
            astidx.constrained_to = subscript_map[i.constrained_to]

    # Generate new AST indices for the independent auxiliary indices
    # introduced by the reduction procedure.
    yutsis_auxiliary_indices_to_ast(aux_idx, subscript_map, index_number, zero_ast)

    idx = {astidx: i for i, astidx in subscript_map.items() if i.constrained_to is None or i.external or i.is_particle}

    reduced_variables = tuple(
        ast.ReducedVariable(v.tensor, v.subscripts,
                            tuple(subscript_map[l] for l in aux))
        for v, aux in jvariables)

    deltas = tuple(ast.DeltaJ(astidx, subscript_map[idx.constrained_to]) for astidx, idx in external_idx.items() if idx.constrained_to is not None)
    trideltas = tuple(ast.TriangularDelta(subscript_map[l] for l in t.indices) for t in Y.triangulardeltas)
    sixjs = tuple(ast.SixJ(subscript_map[l] for l in s.indices) for s in Y.sixjs)
    ninejs = tuple(ast.NineJ(subscript_map[l] for l in n.indices) for n in Y.ninejs)
    hatfactors = tuple(
        ast.HatPhaseFactor(i, hatpower=idx[i].jhat, jphase=idx[i].jphase, mphase=idx[i].mphase, sign=idx[i].sign)
        for i in sorted(set(subscript_map.values()), key=lambda astidx: astidx.name))

    new_mul = ast.Mul(itertools.chain(deltas, factors, hatfactors, trideltas, sixjs, ninejs, reduced_variables))
    new_rhs = ast.Sum(tuple(itertools.chain(internals, (subscript_map[l] for l in aux_rhs if subscript_map[l] not in external_idx))), new_mul)

    return new_rhs


def variable_to_clebsches(v, idx, convention='wigner', lhs=False):
    """Generate a Clebsch-Gordan network according to the coupling scheme of
    the given tensor variable.

    Parameters
    ----------
    v : `ast.Variable`
        The tensor variable.

    idx : `dict`(`ast.Index`: `yutsis.Idx`)
        Mapping from AST indices to Yutsis graph indices

    convention : {'wigner', 'sakurai'}
        Use the given convention for Wigner-Eckart reduced matrix elements.

    lhs : `bool`
        Set to True to generate the Clebsch-Gordan network for the variable on
        the left-hand side to reduce the right-hand side of the equation.
        Depending on `convention` and `wet_scalar`, this needs some additional
        hat factors to cancel a free summation over the total projection quantum
        number. This factor is added when `lhs` is True.

    Returns
    -------
    clebsches : `list` of `yutsis.ClebschGordan`
        List of Clebsch-Gordan coefficients needed to (un-)reduce the variable

    aux : `list` of `yutsis.Idx`
        List of additional angular-momentum indices generated in the reduction
        process.
    """

    _check_convention(convention)

    clebsches = []
    aux = []

    def rec(s):
        if isinstance(s[0], tuple):
            s0 = (rec(s[0]), 1)
        else:
            s0 = (idx[v.subscripts[abs(s[0]) - 1]], +1 if s[0] > 0 else -1)
        if isinstance(s[1], tuple):
            s1 = (rec(s[1]), 1)
        else:
            s1 = (idx[v.subscripts[abs(s[1]) - 1]], +1 if s[1] > 0 else -1)

        # Create a new dummy index for the coupled angular momentum and add
        # the coupling CG to the list.
        cpidx = yutsis.Idx(yutsis.Idx.coupled_type(s0[0], s1[0]),
                                is_particle=False, external=lhs)
        cg = yutsis.ClebschGordan([s0[0], s1[0], cpidx],
                                       [s0[1], s1[1], 1])

        # If the time-reversed state is coupled, we have to add a (-1)^(j-m)
        # phase.
        if s0[1] < 0:
            s0[0].jphase += 1
            s0[0].mphase -= 1
        if s1[1] < 0:
            s1[0].jphase += 1
            s1[0].mphase -= 1

        clebsches.append(cg)
        aux.append(cpidx)
        return cpidx

    # Special case for simple numbers: generate a zero rank index for consistency.
    if not v.tensor.scheme:
        return [], [yutsis.Idx('int',
                               is_particle=False,
                               external=lhs,
                               zero=True)]

    if isinstance(v.tensor.scheme[0], tuple):
        s0 = (rec(v.tensor.scheme[0]), 1)
    else:
        s0 = (idx[v.subscripts[abs(v.tensor.scheme[0]) - 1]],
              +1 if v.tensor.scheme[0] > 0 else -1)
    if isinstance(v.tensor.scheme[1], tuple):
        s1 = (rec(v.tensor.scheme[1]), 1)
    else:
        s1 = (idx[v.subscripts[abs(v.tensor.scheme[1]) - 1]],
              +1 if v.tensor.scheme[1] > 0 else -1)

    # The last coupling is different from the previous ones since we have to
    # be compatible with the usual WET conventions.
    rankidx = yutsis.Idx(yutsis.Idx.coupled_type(s0[0], s1[0]),
                         is_particle=False,
                         external=lhs,
                         zero=v.tensor.scalar,
                         rank=True)

    if not v.tensor.scalar or v.tensor.reduce:
        if convention == 'wigner':
            rankidx.jphase += 2
            s0[0].jhat -= 1
        elif convention == 'sakurai':
            s1[0].jhat -= 1

    # If we are preparing the Yutsis graph for the left-hand side an equation,
    # where the LHS tensor is an unreduced scalar, we have to add an
    # additional j1 hat factor to cancel the unrestricted m sum that remains
    # after the reduction.
    if lhs and v.tensor.scalar and not v.tensor.reduce:
        s1[0].jhat -= 2

    # This Clebsch-Gordan is equal to a delta if the operator is scalar.
    cg = yutsis.ClebschGordan([s1[0], rankidx, s0[0]], [s1[1], 1, s0[1]])

    clebsches.append(cg)
    aux.append(rankidx)
    return clebsches, aux


def _check_convention(convention):
    if convention not in ('wigner', 'sakurai'):
        raise ValueError('Unknown WET convention: {}.'
                         ' Must be wigner or sakurai.'.format(convention))


def handle_deltas(Y):
    """Handle delta constraints arising from the reduction of the Yutsis graph.

    Separates all indices mentioned in delta constraints of the Yutsis graph
    `Y` into disjoint sets, where all indices are constrained by deltas to have
    the same value. Selects one index from each of these sets as independent,
    and marks all others as dependent, transferring phases and hat factor powers
    to the independent index.

    Parameters
    ----------
    Y : `yutsis.Graph`
        Yutsis graph to process.

    Returns
    -------
    `dict`(`yutsis.Idx`: `yutsis.Idx`)
        mapping from all encountered indices to their independent index.
    """

    deltas = list(Y.deltas)

    idxmap = {}

    for delta in deltas:

        # If delta already considered then continue
        if delta not in Y.deltas:
            continue

        # Initialize deltaList with delta
        deltaList = [delta]

        # Loop over the deltaList
        for deltap in deltaList:

            # Get indices
            idx1 = deltap.indices[0]
            idx2 = deltap.indices[1]

            # Find other delta that should be in deltaList
            for deltapp in deltas:

                # If already added then continue
                if deltapp in deltaList:
                    continue

                # If deltas share an index then add deltapp
                if idx1 in deltapp.indices or idx2 in deltapp.indices:
                    deltaList.append(deltapp)

        # Sort the list of deltas
        deltaList.sort(key=lambda dlt: ((0 if dlt.indices[0].zero else 1), (0 if dlt.indices[0].external else 1), (0 if dlt.indices[0].is_particle else 1), len(dlt.indices[0].name), dlt.indices[0].name))

        # Get surviving index
        survivingIdx = deltaList[0].indices[0]
        while survivingIdx.constrained_to is not None:
            survivingIdx = survivingIdx.constrained_to

        # Get list of all other indices
        for dlt in deltaList:
            for idx in dlt.indices:
                if idx != survivingIdx and idx not in idxmap:
                    idx.set_constraint(survivingIdx)
                    idxmap[idx] = survivingIdx

        # Remove deltas from Yutsis
        for deltap in deltaList:
            Y.deltas.remove(deltap)

    return idxmap


_TYPE_MAP = {
    'int': 'J{}',
    'hint': 'j{}',
    'rank': 'λ{}',
    }


def generate_auxiliary_ast_indices(v, index_number, zero):
    """Generate auxiliary AST indices arising from the reduction of the given variable.

    Parameters
    ----------
    v : `ast.Variable`
        Tensor variable.

    index_number : `dict` {'hint': `int`, 'int': `int`, 'rank': `int`}
        Dictionary holding the counters for automatically generating auxiliary
        indices. Values should be large enough so that new generated names do
        not alias already existing ones.

    zero : `ast.Index`
        AST index to use for zero indices.

    Returns
    -------
    `list` of `ast.Index`
        List of generated indices.
    """
    aux_ast = []

    def rec(s):
        if isinstance(s[0], tuple):
            s0 = rec(s[0])
        else:
            s0 = v.subscripts[abs(s[0]) - 1]
        if isinstance(s[1], tuple):
            s1 = rec(s[1])
        else:
            s1 = v.subscripts[abs(s[1]) - 1]

        # Create a new dummy index for the coupled angular momentum.
        cptype = ast.Index.coupled_type(s0, s1)
        name = _TYPE_MAP[cptype].format(index_number[cptype])
        index_number[cptype] += 1

        cpidx = ast.Index(name=name, type=cptype, class_='am')
        aux_ast.append(cpidx)
        return cpidx

    if not v.tensor.scheme:
        return [zero]

    if isinstance(v.tensor.scheme[0], tuple):
        s0 = rec(v.tensor.scheme[0])
    else:
        s0 = v.subscripts[abs(v.tensor.scheme[0]) - 1]
    if isinstance(v.tensor.scheme[1], tuple):
        s1 = rec(v.tensor.scheme[1])
    else:
        s1 = v.subscripts[abs(v.tensor.scheme[1]) - 1]

    if v.tensor.scalar:
        aux_ast.append(zero)
    else:
        cptype = ast.Index.coupled_type(s0, s1)
        name = _TYPE_MAP['rank'].format(index_number['rank'])
        index_number['rank'] += 1
        rankidx = ast.Index(name=name, type=cptype, class_='am')
        aux_ast.append(rankidx)

    return aux_ast


def yutsis_auxiliary_indices_to_ast(aux_idx, subscript_map, index_number, zero):
    """Generate AST indices for unconstrained Yutsis indices.

    Generates new AST indices for the given list of Yutsis indices, and adds
    them to ``subscript_map``.

    Parameters
    ----------
    aux_idx : `list` of `yutsis.Idx`
        List of Yutsis indices to process.

    subscript_map : `dict`(`yutsis.Idx`: `amc.ast.Index`)
        Mapping from Yutsis indices to known AST indices, e.g., external indices.
        New indices are added to this mapping.

    index_number : `dict` {'hint': `int`, 'int': `int`, 'rank': `int`}
        Dictionary holding the counters for automatically generating auxiliary
        indices. Values should be large enough so that new generated names do
        not alias already existing ones.

    zero : `ast.Index`
        AST index to use for zero indices.
    """
    for idx in aux_idx:
        if idx not in subscript_map:
            if idx.constrained_to is None:
                if not idx.zero:
                    if idx.rank:
                        name = _TYPE_MAP['rank'].format(index_number['rank'])
                        index_number['rank'] += 1
                    else:
                        name = _TYPE_MAP[idx.type].format(index_number[idx.type])
                        index_number[idx.type] += 1
                    subscript_map[idx] = ast.Index(name, idx.type, 'am')
                else:
                    subscript_map[idx] = zero
            else:
                sidx = idx.constrained_to

                if sidx not in subscript_map:
                    if not idx.zero:
                        if sidx.rank:
                            name = _TYPE_MAP['rank'].format(index_number['rank'])
                            index_number['rank'] += 1
                        else:
                            name = _TYPE_MAP[sidx.type].format(index_number[sidx.type])
                            index_number[sidx.type] += 1
                        subscript_map[sidx] = ast.Index(name, sidx.type, 'am')
                    else:
                        subscript_map[sidx] = zero

                subscript_map[idx] = subscript_map[sidx]
