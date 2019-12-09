from __future__ import (absolute_import, print_function, division)

import fractions

from ._ast import ASTTraverser, Add

class _LatexPrinter(ASTTraverser):
    def n_equation_exit(self, eqn, results):
        lhs, rhs = results
        return '{} = {}'.format(lhs, rhs)

    def n_variable_exit(self, v, _):
        return '{}_{{{}}}'.format(v.tensor.attrs.get('latex', v.tensor.name), ' '.join(v.subscripts))

    def n_sum_exit(self, s, result):
        if isinstance(s[0], Add):
            fmt = r'\sum_{{{}}}\left({}\right)'
        else:
            fmt = r'\sum_{{{}}} {}'
        return fmt.format(' '.join(sorted(s.subscripts)), result[0])

    def n_mul_exit(self, m, results):
        strings = []
        pre = ''
        for i, r in enumerate(results):
            if m[i] == -1:
                pre = '-'
                continue
            if isinstance(m[i], Add):
                strings.append('({})'.format(r))
            else:
                strings.append(r)
        return pre + ' '.join(strings)

    def n_add_exit(self, a, results):
        strings = []
        for i, r in enumerate(results):
            if i !=0 and not r.startswith('-'):
                strings.append('+ ' + r)
            else:
                strings.append(r)
        return ' '.join(strings)

    def n_permute_exit(self, p, results):
        return str(p)

    def default_exit(self, n, results):
        if isinstance(n, fractions.Fraction):
            if n < 0:
                return r'-\frac{{{0.numerator}}}{{{0.denominator}}}'.format(-n)
            else:
                return r'\frac{{{0.numerator}}}{{{0.denominator}}}'.format(n)
        return str(n)

def to_latex(equation):
    lp = _LatexPrinter()
    return lp.start(equation)
