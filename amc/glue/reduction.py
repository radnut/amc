'''
Created on 12.12.2019

@author: wirth
'''

import itertools

from ..frontend import _ast as ast

from .. import YutsisGraph


class ReductionError(Exception):
    pass


def reduce_equation(equation, *, permute=None, collect_ninejs=False,
                    convention='edmonds', wet_scalar=False,
                    monitor=lambda _: None):
    rhs = equation.rhs.expand_permutations().expand()

    if isinstance(rhs, ast.Add):
        terms = rhs
    else:
        terms = [rhs]

    index_number = {'hint': 0, 'int': 0}
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
    for term in terms:
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
                wet_scalar=wet_scalar,
                monitor=monitor))

    new_rhs = ast.Add(new_terms)
    return ast.Equation(new_lhs, new_rhs)


def reduce_term(lhs, aux_lhs_ast, term, index_number, zero_ast, *, permute=None, collect_ninejs=False,
                convention='edmonds', wet_scalar=False,
                monitor=lambda _: None):

    _check_convention(convention)

    if not isinstance(term, (ast.Sum, ast.Mul)):
        raise ValueError('Term should be (a sum over) a product of factors.')

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

    external_idx = {i: YutsisGraph.Idx('hint', i.name, is_particle=True, external=True)
                    for i in lhs.depends_on}
    internal_idx = {i: YutsisGraph.Idx('hint', i.name, is_particle=True, external=False)
                    for i in internals}
    aux_idx = []

    zero = YutsisGraph.Idx('int', '0', is_particle=False, zero=True)
    internal_idx[zero_ast] = zero

    idx = dict()
    idx.update(external_idx)
    idx.update(internal_idx)

    clebsches = []
    jvariables = []

    for v in variables:
        cl, aux = variable_to_clebsches(v, idx, convention=convention,
                                        wet_scalar=wet_scalar, lhs=False)
        clebsches += cl
        aux_idx += aux

        jvariables.append((v, aux))

    # save the auxiliary variables created for the RHS for later.
    aux_rhs = aux_idx[:]

    cl_lhs, aux_lhs = variable_to_clebsches(lhs, external_idx, convention=convention,
                                            wet_scalar=wet_scalar, lhs=True)

    external_idx.update({astidx: idx for astidx, idx in zip(aux_lhs_ast, aux_lhs)})

    clebsches += cl_lhs
    aux_idx = aux_lhs + aux_idx

    Y = YutsisGraph.YutsisReduction(list(idx.values()) + aux_idx, clebsches,
                                    zero)

    # Until we have permutations, we can only fail
    if Y.get_number_of_nodes() != 0:
        raise ReductionError()

    for sixj in Y.sixjs:
        sixj.canonicalize()
        for i in sixj.indices:
            if i not in internal_idx and i not in external_idx:
                aux_rhs.append(i)
                aux_idx.append(i)

    if collect_ninejs:
        Y.collect_ninejs()

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

    idx = {astidx: i for i, astidx in subscript_map.items()}

    reduced_variables = tuple(
        ast.ReducedVariable(v.tensor, v.subscripts,
                            tuple(subscript_map[l] for l in aux))
        for v, aux in jvariables)

    deltas = tuple(ast.DeltaJ(astidx, subscript_map[idx.constrained_to]) for astidx, idx in external_idx.items() if idx.constrained_to is not None)
    threejs = tuple(ast.ThreeJ(subscript_map[l] for l in t.indices) for t in Y.threejs)
    sixjs = tuple(ast.SixJ(subscript_map[l] for l in s.indices) for s in Y.sixjs)
    ninejs = tuple(ast.NineJ(subscript_map[l] for l in n.indices) for n in Y.ninejs)
    hatfactors = tuple(ast.HatPhaseFactor(i, hatpower=idx[i].jhat, jphase=idx[i].jphase, mphase=idx[i].mphase, sign=idx[i].sign) for i in set(subscript_map.values()))

    new_mul = ast.Mul(itertools.chain(deltas, factors, hatfactors, threejs, sixjs, ninejs, reduced_variables))
    new_rhs = ast.Sum(tuple(itertools.chain(internals, (subscript_map[l] for l in aux_rhs if subscript_map[l] not in external_idx))), new_mul)

    return new_rhs


def variable_to_clebsches(v, idx, convention='edmonds', wet_scalar=False,
                          lhs=False):

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
        cpidx = YutsisGraph.Idx(YutsisGraph.Idx.coupled_type(s0[0], s1[0]),
                                is_particle=False, external=lhs)
        cg = YutsisGraph.ClebschGordan([s0[0], s1[0], cpidx],
                                       [s0[1], s1[1], 1])

        clebsches.append(cg)
        aux.append(cpidx)
        return cpidx

    # Special case for simple numbers: generate a zero rank index for consistency.
    if not v.tensor.scheme:
        return [], [YutsisGraph.Idx('int',
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
    rankidx = YutsisGraph.Idx(YutsisGraph.Idx.coupled_type(s0[0], s1[0]),
                              is_particle=False,
                              external=lhs,
                              zero=(v.tensor.rank == 0))

    if v.tensor.rank > 0 or wet_scalar:
        if convention == 'edmonds':
            rankidx.jphase += 2
            s0[0].jhat -= 1
        elif convention == 'sakurai':
            s1[0].jhat -= 1

    # If we are preparing the Yutsis graph for the left-hand side an equation,
    # where the LHS tensor is an unreduced scalar, we have to add an
    # additional j1 hat factor to cancel the unrestricted m sum that remains
    # after the reduction.
    if lhs and not wet_scalar:
        s1[0].jhat -= 2

    # This Clebsch-Gordan is equal to a delta if the operator is scalar.
    cg = YutsisGraph.ClebschGordan([s1[0], rankidx, s0[0]], [s1[1], 1, s0[1]])

    if v.tensor.rank == 0:
        s1[0].constrained_to = s0[0]

    clebsches.append(cg)
    aux.append(rankidx)
    return clebsches, aux


def _check_convention(convention):
    if convention not in ('edmonds', 'sakurai'):
        raise ValueError('Unknown WET convention: {}.'
                         ' Must be edmonds or sakurai.'.format(convention))


def handle_deltas(Y):
    """"""

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

        # Apply delta to indices
        # 1) The ones not containing survivingIdx
        # 2) The ones containing survivingIdx
        for dlt in [delta for delta in deltaList if survivingIdx not in delta.indices]:
            dlt.apply()
        for dlt in [delta for delta in deltaList if survivingIdx in delta.indices]:
            dlt.apply()

        # Get list of all other indices
        for dlt in deltaList:
            for idx in dlt.indices:
                if idx != survivingIdx and idx not in idxmap:
                    idx.constrained_to = survivingIdx
                    idxmap[idx] = survivingIdx

        # Remove deltas from Yutsis
        for deltap in deltaList:
            Y.deltas.remove(deltap)

    return idxmap


def generate_auxiliary_ast_indices(v, index_number, zero):
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
        name = ('J{}' if cptype == 'int' else 'j{}').format(index_number[cptype])
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

    if v.tensor.rank == 0:
        aux_ast.append(zero)
    else:
        cptype = ast.Index.coupled_type(s0, s1)
        name = ('J{}' if cptype == 'int' else 'j{}').format(index_number[cptype])
        index_number[cptype] += 1
        rankidx = ast.Index(name=name, type=cptype, class_='am')
        aux_ast.append(rankidx)

    return aux_ast


def yutsis_auxiliary_indices_to_ast(aux_idx, subscript_map, index_number, zero):
    for idx in aux_idx:
        if idx not in subscript_map:
            if idx.constrained_to is None:
                if not idx.zero:
                    name = ('J{}' if idx.type == 'int' else 'j{}').format(index_number[idx.type])
                    index_number[idx.type] += 1
                    subscript_map[idx] = ast.Index(name, idx.type, 'am')
                else:
                    subscript_map[idx] = zero
            else:
                sidx = idx.constrained_to

                if sidx not in subscript_map:
                    if not idx.zero:
                        name = ('J{}' if sidx.type == 'int' else 'j{}').format(index_number[sidx.type])
                        index_number[sidx.type] += 1
                        subscript_map[sidx] = ast.Index(name, sidx.type, 'am')
                    else:
                        subscript_map[sidx] = zero

                subscript_map[idx] = subscript_map[sidx]
