import json
import pytest
from .build_model import build_model


# Shape matches actual plcc-spec output:
# - syntax.rules[].rhsSymbolList (not 'rhs')
# - lhs has name, isTerminal, altName, isCapturing
# - rhsSymbolList symbols have name, isTerminal, isCapturing (and altName for capturing symbols)
_TRIVIAL_SPEC = {
    "lexical": {
        "ruleList": [
            {
                "name": "NUM",
                "pattern": "\\d+",
                "isSkip": False,
                "line": {"string": "token NUM '\\d+'", "number": 1, "file": None}
            }
        ]
    },
    "syntax": {
        "rules": [
            {
                "line": {"string": "<program> ::= NUM", "number": 3, "file": None},
                "lhs": {"name": "program", "isTerminal": False, "altName": None, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True}
                ]
            }
        ]
    },
    "semantics": [
        {"language": "PlantUML", "tool": "diagram", "codeFragmentList": []}
    ]
}


def test_returns_model_with_start():
    model = build_model(_TRIVIAL_SPEC)
    assert model['start'] == 'program'


def test_returns_one_class():
    model = build_model(_TRIVIAL_SPEC)
    assert len(model['classes']) == 1
    assert model['classes'][0]['name'] == 'Program'


def test_class_has_num_field():
    model = build_model(_TRIVIAL_SPEC)
    fields = model['classes'][0]['fields']
    assert any(f['name'] == 'num' and f['type'] == 'Token' for f in fields)


def test_semantic_sections_present():
    model = build_model(_TRIVIAL_SPEC)
    sections = model['semantic_sections']
    assert any(s['tool'] == 'diagram' and s['language'] == 'PlantUML' for s in sections)


_ARITH_SPEC = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "Expr", "isTerminal": False, "isCapturing": True, "altName": "expr"}
                ]
            },
            {
                "lhs": {"name": "Expr", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "Term", "isTerminal": False, "isCapturing": True, "altName": "term"},
                    {"name": "ExprRest", "isTerminal": False, "isCapturing": True, "altName": "rest"}
                ]
            },
            {
                "lhs": {"name": "ExprRest", "altName": "AddRest", "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "PLUS", "isTerminal": True, "isCapturing": False},
                    {"name": "Term", "isTerminal": False, "isCapturing": True, "altName": "term"},
                    {"name": "ExprRest", "isTerminal": False, "isCapturing": True, "altName": "rest"}
                ]
            },
            {
                "lhs": {"name": "ExprRest", "altName": "NilRest", "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": []
            },
            {
                "lhs": {"name": "Term", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                ]
            }
        ]
    },
    "semantics": [
        {"language": "Python", "tool": "calculate", "codeFragmentList": []}
    ]
}


def test_trivial_class_has_abstract_false():
    model = build_model(_TRIVIAL_SPEC)
    assert model['classes'][0]['abstract'] == False


def test_trivial_class_has_no_methods_key():
    model = build_model(_TRIVIAL_SPEC)
    assert 'methods' not in model['classes'][0]


def test_arith_start_is_program():
    model = build_model(_ARITH_SPEC)
    assert model['start'] == 'program'


def test_arith_exprrest_is_abstract():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['abstract'] == True


def test_arith_exprrest_has_no_fields():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['fields'] == []


def test_arith_exprrest_extends_none():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['extends'] is None


def test_arith_addrest_is_concrete():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    assert addrest['abstract'] == False


def test_arith_addrest_extends_exprrest():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    assert addrest['extends'] == 'ExprRest'


def test_arith_addrest_has_term_and_rest_fields():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    field_names = [f['name'] for f in addrest['fields']]
    assert 'term' in field_names
    assert 'rest' in field_names


def test_arith_nilrest_extends_exprrest():
    model = build_model(_ARITH_SPEC)
    nilrest = next(c for c in model['classes'] if c['name'] == 'NilRest')
    assert nilrest['extends'] == 'ExprRest'


def test_arith_nilrest_has_no_fields():
    model = build_model(_ARITH_SPEC)
    nilrest = next(c for c in model['classes'] if c['name'] == 'NilRest')
    assert nilrest['fields'] == []


def test_arith_term_has_token_field():
    model = build_model(_ARITH_SPEC)
    term = next(c for c in model['classes'] if c['name'] == 'Term')
    fields = {f['name']: f['type'] for f in term['fields']}
    assert fields.get('num') == 'Token'


def test_arith_abstract_before_concrete():
    model = build_model(_ARITH_SPEC)
    names = [c['name'] for c in model['classes']]
    assert names.index('ExprRest') < names.index('AddRest')
    assert names.index('ExprRest') < names.index('NilRest')


def test_arith_expr_extends_none():
    model = build_model(_ARITH_SPEC)
    expr = next(c for c in model['classes'] if c['name'] == 'Expr')
    assert expr['extends'] is None
    assert expr['abstract'] == False
