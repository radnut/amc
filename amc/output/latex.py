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

"""LaTeX output for reduced and unreduced equations."""

from __future__ import (absolute_import, print_function, division)

import fractions
import re

from ..ast import ASTTraverser, Add, HatPhaseFactor

_TRANSLATION_TABLE = str.maketrans({
    'α': r'{\alpha}',
    '\u0391': r'A',
    'β': r'{\beta}',
    '\u0392': r'B',
    'γ': r'{\gamma}',
    'Γ': r'{\Gamma}',
    'δ': r'{\delta}',
    'Δ': r'{\Delta}',
    'ε': r'{\epsilon}',
    '\u0395': r'E',
    'ζ': r'{\zeta}',
    '\u0396': r'Z',
    'η': r'{\eta}',
    '\u0397': r'H',
    'ϑ': r'{\vartheta}',
    'θ': r'{\theta}',
    'Θ': r'{\Theta}',
    'ι': r'{\iota}',
    '\u0399': r'I',
    'κ': r'{\kappa}',
    '\u039A': r'K',
    'λ': r'{\lambda}',
    'Λ': r'{\Lambda}',
    'μ': r'{\mu}',
    '\u039C': r'M',
    'ν': r'{\nu}',
    '\u039D': r'N',
    'ξ': r'{\xi}',
    'Ξ': r'{\Xi}',
    '\u03BF': r'o',
    '\u039F': r'O',
    'ϖ': r'{\varpi}',
    'π': r'{\pi}',
    'Π': r'{\Pi}',
    'ρ': r'{\rho}',
    '\u03A1': r'P',
    '\u03C2': r'{\varsigma}',
    'σ': r'{\sigma}',
    'Σ': r'{\Sigma}',
    'τ': r'{\tau}',
    '\u03A4': r'T',
    'υ': r'{\upsilon}',
    'Υ': r'{\Upsilon}',
    'φ': r'{\varphi}',
    'ϕ': r'{\phi}',
    'Φ': r'{\Phi}',
    'χ': r'{\chi}',
    '\u03A7': r'X',
    'ψ': r'{\psi}',
    'Ψ': r'{\Psi}',
    'ω': r'{\omega}',
    'Ω': r'{\Omega}',
    })


class _LatexPrinter(ASTTraverser):

    def __init__(self, *, print_triangulardeltas=False):
        ASTTraverser.__init__(self)

        self.print_triangulardeltas = print_triangulardeltas

    def n_equation_exit(self, eqn, results):
        lhs, rhs = results
        return '{} = {}'.format(lhs, rhs)

    def n_variable_exit(self, v, _):
        return '{}_{{{}}}'.format(v.tensor.attrs.get('latex', v.tensor.name), ' '.join(map(self._latexify_index, v.subscripts)))

    def n_reducedvariable_exit(self, v, _):
        if v.subscripts:
            return '{}_{{{}}}^{{{}}}'.format(v.tensor.attrs.get('latex', v.tensor.name), ' '.join(map(self._latexify_index, v.subscripts)), ' '.join(map(self._latexify_index, v.labels)))
        else:
            # Special case for mode-0 tensors.
            return '{}'.format(v.tensor.attrs.get('latex', v.tensor.name))

    def n_sum_exit(self, s, result):
        if isinstance(s[0], Add):
            fmt = r'\sum_{{{}}} \* \left({}\right)'
        else:
            fmt = r'\sum_{{{}}} \* {}'
        return fmt.format(' '.join(sorted(map(self._latexify_index, s.subscripts))), result[0])

    def n_mul(self, m, **params):
        return dict(in_mul=True)

    def n_mul_exit(self, m, results, in_mul):
        strings = []
        pre = ''

        hatphases = []
        hatphase_begin = None

        for i, r in enumerate(results):
            if m[i] == -1:
                pre = '-'
                continue
            if isinstance(m[i], Add):
                strings.append('({})'.format(r))
            elif isinstance(m[i], HatPhaseFactor):
                if hatphase_begin is None:
                    hatphase_begin = len(strings)
                hatphases.append(m[i])
            elif r is not None and r != '':
                strings.append(r)

        # "Transpose" the hat-phase factors to get a bunch of hat factors and
        # a phase factor for all indices, instead of one-by-one.
        if hatphases:
            phase_exponents = []
            hatpowers = []

            for hp in hatphases:
                phase_exponent, hatpower = self._prepare_hatphase(hp, first=(not phase_exponents))
                if phase_exponent:
                    phase_exponents.append(phase_exponent)
                if hatpower:
                    hatpowers.append(hatpower)

            # Insert hatpowers first, then phases in the same positions to
            # order the phase factor before the hats.
            if hatpowers:
                strings[hatphase_begin:hatphase_begin] = hatpowers
            if phase_exponents:
                strings[hatphase_begin:hatphase_begin] = (r'(-1)^{{{}}}'.format(''.join(phase_exponents)),)

        return pre + r' \* '.join(strings)

    def n_add_exit(self, a, results):
        strings = []
        for i, r in enumerate(results):
            if i != 0 and not r.startswith('-'):
                strings.append('+ ' + r)
            else:
                strings.append(r)
        return ' '.join(strings)

    def n_permute_exit(self, p, results):
        return str(p)

    def n_triangulardelta_exit(self, td, _):
        if self.print_triangulardeltas:
            return r'\triangulardelta{{{}}}{{{}}}{{{}}}'.format(*map(self._latexify_index_j, td.indices))
        else:
            return ''

    def n_sixj_exit(self, sj, _):
        return r'\sixj{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}'.format(*map(self._latexify_index_j, sj.indices))

    def n_ninej_exit(self, nj, _):
        return r'\ninej{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}'.format(*map(self._latexify_index_j, nj.indices))

    def n_deltaj_exit(self, dj, _):
        a = self._latexify_index_j(dj.a)
        b = self._latexify_index_j(dj.b)

        return r'\delta_{{{},{}}}'.format(a, b)

    def n_hatphasefactor(self, hp, **params):
        return dict(in_mul=params.pop('in_mul', False))

    def n_hatphasefactor_exit(self, hp, _, in_mul):
        if in_mul:
            return None

        ret = []
        phase_exponent, hatpower = self._prepare_hatphase(hp)

        if phase_exponent:
            ret.append(r'(-1)^{{{}}}'.format(phase_exponent))

        if hatpower:
            ret.append(hatpower)

        return ' \* '.join(ret)

    def _prepare_hatphase(self, hp, first=True):
        phase_exponent = None
        hatpower = None

        if hp.jphase:
            jphase = '{}{}'.format(abs(hp.jphase) if abs(hp.jphase) != 1 else '', self._latexify_index_j(hp.index))

            if not first:
                sign = '+' if hp.jphase > 0 else '-'
            else:
                sign = '' if hp.jphase > 0 else '-'

            phase_exponent = sign + jphase

        if hp.mphase:
            mphase = '{}m_{{{}}}'.format(abs(hp.mphase) if abs(hp.mphase) != 1 else '', self._latexify_index_j(hp.index))

            if phase_exponent is not None or not first:
                sign = '+' if hp.mphase > 0 else '-'
            else:
                sign = '' if hp.mphase > 0 else '-'

            phase_exponent += sign + mphase

        if hp.hatpower:
            if hp.hatpower != 1:
                hatpower = r'\hatfact{{{}^{{{}}}}}'.format(self._latexify_index_j(hp.index), hp.hatpower)
            else:
                hatpower = r'\hatfact{{{}}}'.format(self._latexify_index_j(hp.index))

        return phase_exponent, hatpower

    def default_exit(self, n, _):
        if isinstance(n, fractions.Fraction):
            if n < 0:
                return r'-\frac{{{0.numerator}}}{{{0.denominator}}}'.format(-n)
            else:
                return r'\frac{{{0.numerator}}}{{{0.denominator}}}'.format(n)
        return str(n)

    def _latexify_index_j(self, i):
        if i.class_ == 'am':
            return self._latexify_index(i)
        else:
            return r'{{j}}_{{{}}}'.format(self._latexify_index(i))

    def _latexify_index(self, s):
        ltx = re.sub(r'^(\w)(\d+)$', r'{\1}_{\2}', str(s))
        return ltx.translate(_TRANSLATION_TABLE)


def convert_expression(expr, print_triangulardeltas=False):
    """Convert an expression to a LaTeX string.

    The output is meant to be used in a ``dmath`` environment defined by the
    ``breqn`` LaTeX package.

    Parameters
    ----------
    expr : `ast.AST`
        An expression represented by an abstract syntax tree.
    print_triangulardeltas : `bool`
        Output 3j triangular constraints. In general, these are unnecessary
        because the constraints are implicitly contained in the tensor
        variables.

    Returns
    -------
    latex : `str`
        A LaTeX representation of the expression.
    """
    lp = _LatexPrinter(print_triangulardeltas=print_triangulardeltas)
    return lp.start(expr)


def equations_to_document(equations, print_triangulardeltas=False):
    """Convert a list of equations to a complete LaTeX document.

    Generates a section for each equation in the list, and subsections for
    each term if the root of the right-hand side expression is an `ast.Add`
    operation. Automatic line breaking of the generated equations is provided
    by the ``breqn`` LaTeX package.

    Parameters
    ----------
    equations : iterable of `ast.Equation`
        Equations to process.
    print_triangulardeltas : `bool`
        Output 3j triangular constraints. In general, these are unnecessary
        because the constraints are implicitly contained in the tensor
        variables.

    Returns
    -------
    latex : `str`
        A LaTeX document as a string.
    """
    output = [r'''
\documentclass{scrartcl}

\usepackage{expl3}
\usepackage{xparse}
\usepackage{amsmath}
\usepackage{breqn}

\newcommand{\triangulardelta}[3]{\Delta(#1 #2 #3)}
\newcommand{\sixj}[6]{\begingroup\setlength{\arraycolsep}{0.2em}\begin{Bmatrix} #1 & #2 & #3 \\ #4 & #5 & #6 \end{Bmatrix}\endgroup}
\newcommand{\ninej}[9]{\begingroup\setlength{\arraycolsep}{0.2em}\begin{Bmatrix} #1 & #2 & #3 \\ #4 & #5 & #6 \\ #7 & #8 & #9 \end{Bmatrix}\endgroup}

\ExplSyntaxOn
\tl_new:N \l__hatfact_tl

\NewDocumentCommand{\hatfact} {m} { \__hatfact_parse:n #1 }

\cs_new:Nn \__hatfact_parse:n { \tl_set:Nn \l__hatfact_main_tl {#1} \__hatfact_hat: }

\cs_generate_variant:Nn \str_set:Nn {Nx}
\cs_new:Nn \__hatfact_hat:
  {
    \str_set:Nx \l_tmpa_str {\l__hatfact_main_tl}
    \str_set:Nn \l_tmpb_str {j}
    \str_if_eq:NNTF \l_tmpa_str \l_tmpb_str {
      \hat{\jmath}
    } {
      \hat \l__hatfact_main_tl
    }
  }
\ExplSyntaxOff

\begin{document}
''']

    for i, eqn in enumerate(equations):
        output.append(r'\section{{Equation {}}}'.format(i + 1))
        if isinstance(eqn.rhs, Add):
            output.append(r'\begin{dmath*}')
            output.append(convert_expression(eqn.lhs) + ' = ')
            output.append(r'\end{dmath*}')

            for j, term in enumerate(eqn.rhs):
                output.append(r'\subsection{{Term {}}}'.format(j + 1))
                output.append(r'\begin{dmath*}')
                output.append(convert_expression(term, print_triangulardeltas=print_triangulardeltas))
                output.append(r'\end{dmath*}')
        else:
            output.append(r'\begin{dmath*}')
            output.append(convert_expression(eqn, print_triangulardeltas=print_triangulardeltas))
            output.append(r'\end{dmath*}')
        output.append(r'')

    output.append(r'\end{document}')
    output.append(r'')

    return '\n'.join(output)
