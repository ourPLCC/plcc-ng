import io
import json
import pytest

from .emit import build_ebnf


_RULE = lambda name, alt, rhs: {
    'line': {'string': '', 'number': 1, 'file': ''},
    'lhs': {'name': name, 'isTerminal': False, 'altName': alt, 'isCapturing': False},
    'rhsSymbolList': rhs,
}
_NT = lambda name: {'name': name, 'isTerminal': False, 'altName': None, 'isCapturing': False}
_T  = lambda name: {'name': name, 'isTerminal': True, 'isCapturing': False}
_REPEAT = lambda name, rhs, sep=None: {
    **_RULE(name, None, rhs),
    'separator': {'name': sep, 'isTerminal': True, 'isCapturing': False} if sep else None,
}


def _spec(rules):
    return {'syntax': {'rules': rules}}


def test_startebnf_and_endebnf():
    result = build_ebnf(_spec([_RULE('A', None, [_NT('B')])]))
    assert result.startswith('@startebnf\n')
    assert result.rstrip().endswith('@endebnf')


def test_standard_rule_single_nonterminal():
    result = build_ebnf(_spec([_RULE('Program', None, [_NT('Stmt')])]))
    assert 'Program ::= Stmt ;' in result


def test_nonterminal_rendered_unquoted():
    result = build_ebnf(_spec([_RULE('A', None, [_NT('B')])]))
    assert 'B' in result
    assert "'B'" not in result


def test_terminal_rendered_quoted():
    result = build_ebnf(_spec([_RULE('A', None, [_T('PLUS')])]))
    assert "'PLUS'" in result


def test_standard_rule_multiple_symbols():
    result = build_ebnf(_spec([_RULE('Expr', None, [_NT('Term'), _T('PLUS'), _NT('Expr')])]))
    assert "Expr ::= Term 'PLUS' Expr ;" in result


def test_multiple_alternatives_same_lhs():
    rules = [
        _RULE('Expr', None, [_NT('Term')]),
        _RULE('Expr', 'Add', [_NT('Expr'), _T('PLUS'), _NT('Term')]),
    ]
    result = build_ebnf(_spec(rules))
    assert "Expr ::= Term | Expr 'PLUS' Term ;" in result


def test_alternatives_appear_once_not_twice():
    rules = [
        _RULE('Expr', None, [_NT('Term')]),
        _RULE('Expr', 'Add', [_NT('Expr'), _T('PLUS'), _NT('Term')]),
    ]
    result = build_ebnf(_spec(rules))
    assert result.count('Expr ::=') == 1


def test_repeating_rule_no_separator():
    result = build_ebnf(_spec([_REPEAT('Items', [_NT('Item')])]))
    assert 'Items ::= { Item } ;' in result


def test_repeating_rule_with_separator():
    result = build_ebnf(_spec([_REPEAT('Args', [_NT('Arg')], sep='COMMA')]))
    assert "Args ::= { Arg 'COMMA' } ;" in result


def test_empty_production():
    result = build_ebnf(_spec([_RULE('Opt', None, [])]))
    assert 'Opt ::=  ;' in result


def test_lhs_order_preserved():
    rules = [
        _RULE('B', None, [_NT('C')]),
        _RULE('A', None, [_NT('B')]),
    ]
    result = build_ebnf(_spec(rules))
    assert result.index('B ::=') < result.index('A ::=')


def test_arith_grammar_smoke():
    rules = [
        _RULE('Program', None, [_NT('Expr')]),
        _RULE('Expr', None, [_NT('Term'), _NT('ExprRest')]),
        _RULE('ExprRest', 'AddRest', [_T('PLUS'), _NT('Term'), _NT('ExprRest')]),
        _RULE('ExprRest', 'NilRest', []),
        _RULE('Term', None, [_T('NUM')]),
    ]
    result = build_ebnf(_spec(rules))
    assert '@startebnf' in result
    assert 'Program ::= Expr ;' in result
    assert "ExprRest ::= 'PLUS' Term ExprRest |  ;" in result
    assert "Term ::= 'NUM' ;" in result
