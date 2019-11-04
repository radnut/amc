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
            if diagonal:
                scheme = (scheme,) * 2

            if len(scheme) != 2:
                raise ValueError('scheme must be a 2-tuple')

            scheme = self._check_scheme(scheme, 1, mode[0] + mode[1])

        else:
            scheme = (self._create_scheme(1, mode[0]), self._create_scheme(mode[0] + 1, mode[1]))

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

        if scheme[0] == 0:
            return (0, _rec(scheme[1]))
        elif scheme[1] == 0:
            return (_rec(scheme[0]), 0)
        else:
            return _rec(scheme)

    @staticmethod
    def _create_scheme(start, num):
        if num == 0:
            return 0
        if num == 1:
            return start
        return (TensorDeclaration._create_scheme(start, num-1), start + num-1)

    def get_drudge_desc(self):
        name = self.attrs.get('latex', self.name)

        return [ '{{{}}}'.format(name), self.mode[0], self.mode[1] ]


class Equation(AST):
    def __init__(self, lhs, rhs):
        super(Equation, self).__init__('equation')
        if not isinstance(lhs, Variable):
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

    def expand(self, keep_single=True):
        new_rhs = self.rhs.expand(keep_single)
        if id(new_rhs) == id(self.rhs):
            return self
        return Equation(self.lhs, new_rhs)

    def to_drudge(self):
        subscript_map = {}
        for s in self.lhs.subscripts:
            subscript_map[s] = len(subscript_map) + 1

        rhs = self.rhs.expand_permutations().expand()

        if isinstance(rhs, Add):
            terms = rhs
        else:
            terms = [ rhs ]

        drudge_list = []
        for term in terms:
            term_subscript_map = dict(subscript_map)

            prefactor = fractions.Fraction(1)
            drudge_term = []

            def _handle_term(t):
                nonlocal prefactor
                if isinstance(t, Mul):
                    for tt in t:
                        _handle_term(tt)
                if isinstance(t, (int, fractions.Fraction)):
                    prefactor *= t
                if isinstance(t, Sum):
                    for s in sorted(t.subscripts):
                        term_subscript_map[s] = len(term_subscript_map) + 1

                    if len(t[0]) == 0:
                        sumterms = [ t[0] ]
                    else:
                        assert isinstance(t[0], Mul)
                        sumterms = t[0]

                    for st in sumterms:
                        _handle_term(st)
                elif isinstance(t, Variable):
                    if len(t.subscripts) <= 1:
                        return

                    drudge_term.append(t.to_drudge(term_subscript_map))

            _handle_term(term)
            drudge_list.append([prefactor.numerator, prefactor.denominator, drudge_term])

        return [self.lhs.to_drudge(subscript_map), drudge_list]



class Variable(AST):
    def __init__(self, tensor, subscripts):
        super(Variable, self).__init__('variable')

        if (not tensor.diagonal and len(subscripts) != tensor.totalmode) or (tensor.diagonal and len(subscripts) != tensor.totalmode//2):
            raise ValueError(
                'Expected {totalmode} subscripts on tensor "{name}", got {nsubscripts}'.format(
                    totalmode=(tensor.totalmode if not tensor.diagonal else tensor.totalmode//2), name=tensor.name, nsubscripts=len(subscripts)))

        self.tensor = tensor
        self.subscripts = subscripts
        self.depends_on = set(subscripts)

    def __str__(self):
        return '{0}_{{{1}}}'.format(self.tensor.name, ' '.join(self.subscripts))

    def apply_permutation(self, i, j):
        ij = {i, j}

        if ij.isdisjoint(self.depends_on):
            return self

        subst = {i: j, j: i}

        new_subscripts = tuple(subst.get(s, s) for s in self.subscripts)
        return Variable(self.tensor, new_subscripts)

    def to_drudge(self, subscript_map):
        return self.tensor.get_drudge_desc() + [[ subscript_map[s] for s in self.subscripts ]]


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

    def distribute(self, terms, side='right', keep_single=False):
        if not terms:
            return self

        if keep_single:
            def _rec(t):
                if isinstance(t, Variable):
                    return len(t.subscripts) > 1
                elif not isinstance(t, AST):
                    return False
                for tt in t:
                    if _rec(tt):
                        return True
                return False

            if not _rec(self):
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

    def expand(self, keep_single=True):
        changed = False
        terms = []
        for t in self:
            if hasattr(t, 'expand'):
                new_term = t.expand(keep_single)
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

    def expand(self, keep_single=True):
        # print('Mul: expanding {}...'.format(self))

        has_distributable_terms = False

        expanded_terms = [ t.expand(keep_single) if hasattr(t, 'expand') else t for t in self ]

        terms_right = []
        for t in reversed(expanded_terms):
            if hasattr(t, 'distribute'):
                has_distributable_terms = True

                if not terms_right:
                    terms_right .insert(0, t)
                else:
                    #print('Mul: Distribute right: {} over {}'.format(t, terms_right))
                    distributed = t.distribute(terms_right, 'right', keep_single)

                    if isinstance(distributed, Mul):
                        terms_right = distributed[:]
                    else:
                        terms_right = [ distributed ]
            else:
                terms_right.insert(0, t)

        if not has_distributable_terms:
            #print('Mul: expanded {} unchanged (no distributable terms)'.format(self))
            return self

        # print('Mul: terms right: {}'.format(terms_right))
        terms = []
        for t in terms_right:
            if hasattr(t, 'distribute'):
                #print('Mul: Distribute left: {} revo {}'.format(terms, t))

                distributed = t.distribute(terms, 'left', keep_single)

                if isinstance(distributed, Mul):
                    terms = distributed[:]
                else:
                    terms = [ distributed ]
            else:
                terms.append(t)

        # print('Mul: expanded {} to {}'.format(self, Mul(terms)))

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
        return 'sum_{{{0}}}({1!s})'.format(' '.join(sorted(self.subscripts)), self[0])

    def distribute(self, terms, side='right', keep_single=False):
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

    def expand(self, keep_single=True):
        if not hasattr(self[0], 'expand'):
            return self

        new_expr = self[0].expand(keep_single)
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

        if len(sets) == 0:
            raise ValueError('need at least one set')
        elif len(sets) == 1 and len(sets[0]) != 2:
            raise ValueError('Permutation operators with a single set must only permute two indices')

        self.sets = tuple(sets)
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
                prefactor *= (-1)**(len(cycle)-1)

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
