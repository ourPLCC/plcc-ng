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
