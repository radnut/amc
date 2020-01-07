from __future__ import (absolute_import, print_function, division)

import fractions

from . import _util


class AST(object):
    __slots__ = ('type', '_kids', 'attr')

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

    class _PruneError(Exception):

        def __init__(self, params=None):
            self.params = params

    @staticmethod
    def traverse(root, preaction=(lambda n, **k: None), postaction=(lambda n, r, **k: None)):
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
        default_pre = getattr(self, 'default', lambda n, **k: None)
        default_post = getattr(self, 'default_exit', lambda n, r, **k: None)

        def _pre(n):
            if hasattr(n, 'type'):
                method = getattr(self, 'n_' + n.type, default_pre)
            else:
                method = default_pre
            method(n)

        def _post(n, r):
            if hasattr(n, 'type'):
                method = getattr(self, 'n_' + n.type + '_exit', default_post)
            else:
                method = default_post
            return method(n, r)

        return self.traverse(root, preaction=_pre, postaction=_post)

    def prune(self, params=None):
        raise ASTTraverser._PruneError(params)


class TensorDeclaration(AST):

    def __init__(self, name, mode, rank=0, diagonal=False, scheme=None, **kwargs):
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
                raise ValueError('mode must be a nonnegative integer or a 2-tuple')

        rank = fractions.Fraction(rank)
        if rank < 0 or rank.denominator not in (1, 2):
            raise ValueError('rank must be a nonnegative (half-)integer')

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
        self.rank = rank
        self.diagonal = diagonal
        self.scheme = scheme
        self.attrs = kwargs

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Tensor {0.name} {{mode={0.mode}, rank={0.rank}, diagonal={0.diagonal}, scheme={0.scheme} }}'.format(self)

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
        if not self.rhs.contains_perm:
            return self

        new_rhs = self.rhs.expand_permutations()
        if id(new_rhs) == id(self.rhs):
            return self
        return Equation(self.lhs, new_rhs)

    def expand(self, keep_diagonal=True):
        new_rhs = self.rhs.expand(keep_diagonal)
        if id(new_rhs) == id(self.rhs):
            return self
        return Equation(self.lhs, new_rhs)


class Index(object):

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
        if (i1.type == 'hint' and i2.type == 'hint') or (i1.type == 'int' and i2.type == 'int'):
            return 'int'
        return 'hint'


class Variable(AST):

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
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        subst = {i: j, j: i}

        new_subscripts = tuple(subst.get(s, s) for s in self.subscripts)
        return Variable(self.tensor, new_subscripts)


class ReducedVariable(AST):

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
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        subst = {i: j, j: i}

        new_subscripts = tuple(subst.get(s, s) for s in self.subscripts)
        return Variable(self.tensor, new_subscripts)


class ThreeJ(AST):

    def __init__(self, indices):
        super(ThreeJ, self).__init__('threej')

        self.indices = tuple(indices)

        if len(self.indices) != 3:
            raise ValueError('indices list must have three elements.')

        if any(not isinstance(i, Index) for i in self.indices):
            raise ValueError('elements of the indices list must be AST indices.')

        if sum(1 if i.type == 'int' else 0 for i in self.indices) not in (1, 3):
            raise ValueError('incompatible indices (must be of hhi or iii type).')

        self.depends_on = set(self.indices)

    def __str__(self):
        return 'ThreeJ({})'.format(' '.join(map(str, self.indices)))


class SixJ(AST):

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

    def __init__(self, a, b):
        super(DeltaJ, self).__init__('deltaj')
        self.a = a
        self.b = b
        self.depends_on = {a, b}

    def __str__(self):
        return 'DeltaJ({0!s},{1!s})'.format(self.a, self.b)


class HatPhaseFactor(AST):

    def __init__(self, *args, **kwargs):
        pass

    def __new__(cls, index, hatpower=0, jphase=0, mphase=0, sign=1):
        if index.type == 'hint':
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

        def _rec(t):
            if isinstance(t, Variable):
                return t.tensor.diagonal
            elif not isinstance(t, AST):
                return True
            else:
                return all(_rec(tt) for tt in t)

        return _rec(self)

    def distribute(self, terms, side='right', keep_diagonal=True):
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
        if not terms:
            return self

        if side == 'right':
            return Sum(self.subscripts, Mul([self[0]] + terms))
        else:
            return Sum(self.subscripts, Mul(terms + [self[0]]))

    def expand_permutations(self):
        if not self.contains_perm:
            return self

        return Sum(self.subscripts, self[0].expand_permutations())

    def apply_permutation(self, i, j):
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
                # symmetric difference. THe case that both i and j are in s is excluded because
                # then ij would be a subset of s.
                s ^= ij

        return Permute(new_sets)
