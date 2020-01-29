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

from __future__ import (absolute_import, print_function, division)

import re
import fractions

from ._ply import (lex, yacc)
from ..ast import (TensorDeclaration, Index, Equation, Variable, Add, Mul, Sum, Permute)


class LexerError(Exception):
    """A lexer error.

    Parameters
    ----------
    token : LexToken
        The offending token.
    line : `int`
        Line number.
    col : `int`
        Column number.

    Attributes
    ----------
    token : LexToken
        The offending token.
    line : `int`
        Line number.
    col : `int`
        Column number.
    """

    def __init__(self, token, line, col):
        self.token = token
        self.line = line
        self.col = col

    def __str__(self):
        val = self.token.value.splitlines()[0]
        return "Lexical error at or near `%s' (line %d:%d)" % (val, self.line, self.col)


class ParserError(Exception):
    """A parser error.

    Parameters
    ----------
    msg : `str`
        Error message.
    line : `int`
        Line number.
    col : `int`
        Column number.

    Attributes
    ----------
    msg : `str`
        Error message.
    line : `int`
        Line number.
    col : `int`
        Column number.
    """

    def __init__(self, msg, line, col):
        self.msg = msg.format(line=line, col=col)
        self.line = line
        self.col = col

    def __str__(self):
        return self.msg


class ParserSyntaxError(ParserError):
    """A syntax error.

    Parameters
    ----------
    token : LexToken
        Offending token.
    line : `int`
        Line number.
    col : `int`
        Column number.

    Attributes
    ----------
    token : LexToken
        Offending token.
    """

    def __init__(self, token, line, col):
        if token is not None:
            msg = "Syntax error at or near `%s' token (line {line}:{col})" % (token.type,)
        elif line is not None:
            msg = "Syntax error at or near line {line}"
        else:
            msg = "Syntax error at end of file"

        super(ParserSyntaxError, self).__init__(msg, line, col)
        self.token = token


class UnknownTensorError(ParserError):
    """An unknown tensor has been encountered.

    Parameters
    ----------
    name : `str`
        Name of the tensor.
    line : `int`
        Line number.
    col : `int`
        Column number.


    Attributes
    ----------
    name : `str`
        Name of the tensor.
    """

    def __init__(self, name, line, col):
        msg = "Unknown tensor `%s' (line {line}:{col})" % (name,)
        super(UnknownTensorError, self).__init__(msg, line, col)
        self.name = name


class SubscriptError(ParserError):
    """Illegal use of subscripts on a tensor.

    Parameters
    ----------
    tensor : `ast.TensorDeclaration`
        The tensor.
    msg : `str`
        Error message.
    line : `int`
        Line number.
    col : `int`
        Column number.

    Attributes
    ----------
    tensor : `ast.TensorDeclaration`
        The tensor.
    """

    def __init__(self, tensor, msg, line, col):
        msg = "%s (line {line}:{col})" % (msg,)
        super(SubscriptError, self).__init__(msg, line, col)
        self.tensor = tensor


class Lexer:
    tokens = (
        'IDENTIFIER',
        'SUBSCRIPT',
        'NUMBER',
        'STRING',
        'DECLARE',
        'SUM',
        'PERM',
        'BOOL',
    )

    reserved = {'declare': 'DECLARE', 'sum': 'SUM', }

    literals = ('+', '-', '*', '/', ';', '(', ')', '{', '}', '=', ',', '^',)

    t_ignore_COMMENT = r'\#.*'
    t_ignore = ' \t'

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_PERM(self, t):
        r'P\((?:[\w]+|\{[\w ]+\})(?:/(?:[\w]+|\{[\w ]+\}))*\)'

        sets = []
        val = t.value[2:-1]

        while val:
            match = re.match(r'([\w]+|\{[\w ]+\})', val)
            if match.group(1).startswith('{'):
                sets.append(set(match.group(1).split()))
            else:
                sets.append(set(match.group(1)))
            val = val[match.end() + 1:]

        t.value = tuple(sets)
        return t

    def t_BOOL(self, t):
        r'[Tt]rue|[Ff]alse'
        t.value = (t.value.lower() == 'true')
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z][a-zA-Z0-9]*'
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t

    def t_SUBSCRIPT(self, t):
        r'_[\w]+|_\{[\w ]*\}'
        if re.match(r'_[\w]+', t.value):
            t.value = tuple(iter(t.value[1:]))
        else:
            t.value = t.value[2:-1].split()
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'" ([^"\\\n]|\\.)* "'
        t.value = re.sub(r'\\(["\n\\])', r'\1', t.value[1:-1])
        return t

    def t_error(self, t):
        raise LexerError(t, t.lineno, self.find_token_column(t))

    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_token_column(self, token):
        return self.find_column(token.lexpos)

    def find_column(self, lexpos):
        last_cr = self.lexer.lexdata.rfind('\n', 0, lexpos)
        return lexpos - last_cr


class Parser:
    """Parser for AMC files.

    Parameters
    ----------
    optimize : `bool`
        If True, tries to import pregenerated parser and lexer tables to
        improve startup time. If tables do not exist, they are written to the
        package directory, if possible.
    **kwargs
        Additional keword arguments passed to the lexer constructor and the
        main parser invocation `yacc.yacc`. See the `PLY documentation
        <https://www.dabeaz.com/ply/>`_ for details.

    Attributes
    ----------
    lexer : `Lexer`
        The AMC lexer.
    tokens : `tuple`
        List of all tokens generated by the lexer.
    parser : LRParser
        PLY parser object used for parsing.
    """

    def __init__(self, optimize=True, **kwargs):
        self.tensors = {}
        self.equations = []

        lexdebug = kwargs.pop('lexdebug', False)
        parsedebug = kwargs.pop('parsedebug', False)

        if optimize:
            try:
                from . import _lextab
            except ImportError:
                _lextab = '_lextab'

            try:
                from . import _parsetab
            except ImportError:
                _parsetab = '_parsetab'
        else:
            _lextab = '_lextab'
            _parsetab = '_parsetab'

        self.lexer = Lexer(optimize=optimize, debug=lexdebug, lextab=_lextab, **kwargs)

        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self, optimize=optimize, debug=parsedebug, tabmodule=_parsetab, **kwargs)

        self._subscripts = {}

    def parse(self, text, debug=0):
        """Parse the given text as an AMC file.

        Parameters
        ----------
        text : `str`
            Text to parse.
        debug : `int`
            Debug level, increase for more output from the PLY parser.
        """
        self.parser.parse(
            input=text,
            lexer=self.lexer,
            debug=debug)
        return self

    def p_root(self, p):
        '''
        root : statements
            | empty
        '''
        pass

    def p_empty(self, p):
        'empty :'
        pass

    def p_statements(self, p):
        '''
        statements : statements declaration
            | statements equation
            | declaration
            | equation
        '''
        pass

    def p_declaration(self, p):
        "declaration : DECLARE IDENTIFIER kvlist"
        node = TensorDeclaration(p[2], **p[3])
        self.tensors[p[2]] = node
        p[0] = node

    def p_equation(self, p):
        '''
        equation : variable '=' expression ';'
        '''
        var = p[1]
        rhs = p[3]

        self.equations.append(Equation(var, rhs))
        self._subscripts = {}

    def p_kvlist(self, p):
        '''
        kvlist : '{' kvlist_content '}'
            | '{' '}'
        '''
        if len(p) == 3:
            p[0] = {}
        else:
            p[0] = p[2]

    def p_kvlist_content(self, p):
        '''
        kvlist_content : kvlist_content ','  kvpair
            | kvlist_content ','
            | kvpair
        '''
        if len(p) == 2:
            node = {}
            node.update(p[1])
        elif len(p) == 3:
            node = p[1]
        else:
            node = p[1]
            node.update(p[3])

        p[0] = node

    def p_list(self, p):
        '''
        list : '(' list_content ')'
            | '(' ')'
        '''
        if len(p) == 3:
            p[0] = []
        else:
            p[0] = p[2]

    def p_list_content(self, p):
        '''
        list_content : list_content ','  list_item
            | list_content ','
            | list_item
        '''
        if len(p) == 2:
            node = []
            node.append(p[1])
        elif len(p) == 3:
            node = p[1]
        else:
            node = p[1]
            node.append(p[3])

        p[0] = node

    def p_kvpair(self, p):
        '''
        kvpair : IDENTIFIER '=' wholenumber
            | IDENTIFIER '=' fraction
            | IDENTIFIER '=' STRING
            | IDENTIFIER '=' BOOL
            | IDENTIFIER '=' list
        '''
        p[0] = {p[1]: p[3]}

    def p_list_item(self, p):
        '''
        list_item : wholenumber
            | list
        '''
        p[0] = p[1]

    def p_expression(self, p):
        '''
        expression : expression '+' term
            | expression '-' term
            | '-' term
            | term
        '''
        if len(p) == 2:
            node = p[1]
        elif len(p) == 3:
            node = Mul([-1, p[2]])
        else:
            if p[2] == '-':
                term = Mul([-1, p[3]])
            else:
                term = p[3]
            node = Add([p[1], term])
        p[0] = node

    def p_term(self, p):
        '''
        term : term '*' factor
            | factor
        '''
        if len(p) == 2:
            node = p[1]
        else:
            node = Mul([p[1], p[3]])
        p[0] = node

    def p_factor_paren(self, p):
        '''
        factor : '(' expression ')'
        '''
        p[0] = p[2]

    def p_factor_fraction(self, p):
        '''
        factor : fraction
            | NUMBER
        '''
        p[0] = p[1]

    def p_factor_sum(self, p):
        '''
        factor : SUM SUBSCRIPT '(' expression ')'
        '''
        p[0] = Sum(self._to_indices(p[2]), p[4])
        self._remove_indices(p[2])

    def p_factor_variable(self, p):
        '''
        factor : variable
        factor : permute
        '''
        p[0] = p[1]

    def p_variable(self, p):
        '''
        variable : IDENTIFIER SUBSCRIPT
            | IDENTIFIER
        '''
        if len(p) == 2:
            subscripts = ()
        else:
            subscripts = self._to_indices(p[2])

        if p[1] not in self.tensors:
            raise UnknownTensorError(p[1], p.lineno(1), self.lexer.find_column(p.lexpos(1)))

        tensor = self.tensors[p[1]]

        try:
            p[0] = Variable(tensor, subscripts)
        except ValueError as e:
            raise SubscriptError(tensor, str(e), p.lineno(1), self.lexer.find_column(p.lexpos(1)))

    def p_permute(self, p):
        '''
        permute : PERM
        '''
        p[0] = Permute(self._to_indices(s) for s in p[1])

    def p_wholenumber(self, p):
        '''
        wholenumber : NUMBER
            | '-' NUMBER
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = -p[2]

    def p_fraction(self, p):
        '''
        fraction : NUMBER '/' NUMBER
        '''
        p[0] = fractions.Fraction(p[1], p[3])

    def p_error(self, p):
        if p:
            raise ParserSyntaxError(p, p.lineno, self.lexer.find_token_column(p))
        else:
            raise ParserSyntaxError(None, self.lexer.last_token.lineno if self.lexer.last_token is not None else None, 0)

    def _to_indices(self, subscripts):
        ret = []
        for subscript in subscripts:
            if subscript not in self._subscripts:
                self._subscripts[subscript] = Index(subscript, 'hint', 'part')
            ret.append(self._subscripts[subscript])
        return tuple(ret)

    def _remove_indices(self, subscripts):
        for subscript in subscripts:
            self._subscripts.pop(subscript, None)
