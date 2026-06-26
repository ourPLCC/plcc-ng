import pytest
from .deserialize import deserialize_syntactic_spec
from .StandardSyntacticRule import StandardSyntacticRule
from .RepeatingSyntacticRule import RepeatingSyntacticRule
from .Terminal import Terminal
from .CapturingTerminal import CapturingTerminal
from .RhsNonTerminal import RhsNonTerminal


def _line(s='<A> ::= B\n', n=1, f='g.plcc'):
    return {'string': s, 'number': n, 'file': f}

def _lhs(name, alt=None):
    return {'name': name, 'altName': alt, 'isTerminal': False, 'isCapturing': False}

def _terminal(name, capturing=False, alt=None):
    d = {'name': name, 'isTerminal': True, 'isCapturing': capturing}
    if alt:
        d['altName'] = alt
    return d

def _nonterminal(name, alt=None):
    return {'name': name, 'isTerminal': False, 'isCapturing': True, 'altName': alt}

def _rule(lhs_name, rhs=None, separator=None):
    r = {'line': _line(), 'lhs': _lhs(lhs_name), 'rhsSymbolList': rhs or []}
    if separator is not None:
        r['separator'] = separator
    return r

def _lex_rule(name, pattern='x', skip=False):
    return {'line': _line(), 'name': name, 'pattern': pattern, 'isSkip': skip}


def test_empty_syntax_gives_empty_spec():
    syn, lex = deserialize_syntactic_spec({'syntax': {'rules': []}, 'lexical': {'ruleList': []}})
    assert len(syn) == 0

def test_standard_rule_is_standard_syntactic_rule():
    spec = {'syntax': {'rules': [_rule('Program')]}, 'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert isinstance(syn[0], StandardSyntacticRule)

def test_rule_with_separator_is_repeating_syntactic_rule():
    spec = {'syntax': {'rules': [_rule('Items', separator=_terminal('COMMA'))]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert isinstance(syn[0], RepeatingSyntacticRule)

def test_separator_is_terminal_instance():
    spec = {'syntax': {'rules': [_rule('Items', separator=_terminal('COMMA'))]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert isinstance(syn[0].separator, Terminal)
    assert syn[0].separator.name == 'COMMA'

def test_lhs_name_preserved():
    spec = {'syntax': {'rules': [_rule('Program')]}, 'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert syn[0].lhs.name == 'Program'

def test_lhs_alt_name_preserved():
    r = _rule('Expr')
    r['lhs']['altName'] = 'AddExpr'
    spec = {'syntax': {'rules': [r]}, 'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert syn[0].lhs.altName == 'AddExpr'

def test_terminal_rhs_symbol():
    spec = {'syntax': {'rules': [_rule('A', rhs=[_terminal('NUM')])]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    sym = syn[0].rhsSymbolList[0]
    assert isinstance(sym, Terminal)
    assert sym.name == 'NUM'

def test_capturing_terminal_rhs_symbol():
    spec = {'syntax': {'rules': [_rule('A', rhs=[_terminal('NUM', capturing=True, alt='n')])]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    sym = syn[0].rhsSymbolList[0]
    assert isinstance(sym, CapturingTerminal)
    assert sym.altName == 'n'

def test_nonterminal_rhs_symbol():
    spec = {'syntax': {'rules': [_rule('A', rhs=[_nonterminal('B', alt='b')])]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    sym = syn[0].rhsSymbolList[0]
    assert isinstance(sym, RhsNonTerminal)
    assert sym.name == 'B'
    assert sym.altName == 'b'

def test_lexical_rule_name_preserved():
    spec = {'syntax': {'rules': []}, 'lexical': {'ruleList': [_lex_rule('NUM')]}}
    _, lex = deserialize_syntactic_spec(spec)
    assert lex.ruleList[0].name == 'NUM'

def test_lexical_skip_rule():
    from ..lexical.TokenRule import TokenRule
    from ..lexical.SkipRule import SkipRule
    spec = {'syntax': {'rules': []}, 'lexical': {'ruleList': [_lex_rule('WS', skip=True)]}}
    _, lex = deserialize_syntactic_spec(spec)
    assert isinstance(lex.ruleList[0], SkipRule)

def test_lexical_token_rule():
    from ..lexical.TokenRule import TokenRule
    spec = {'syntax': {'rules': []}, 'lexical': {'ruleList': [_lex_rule('NUM', skip=False)]}}
    _, lex = deserialize_syntactic_spec(spec)
    assert isinstance(lex.ruleList[0], TokenRule)
