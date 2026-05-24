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
    assert any(s['tool'] == 'diagram' and s['language'] == 'plantuml' for s in sections)


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


_ARITH_SPEC_WITH_FRAGMENTS = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": []
            },
            {
                "lhs": {"name": "ExprRest", "altName": "AddRest", "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": []
            }
        ]
    },
    "semantics": [
        {
            "language": "Python",
            "tool": "calculate",
            "codeFragmentList": [
                {
                    "targetLocator": {"className": "AddRest", "modifier": None},
                    "block": {"lines": [
                        {"string": "%%%"},
                        {"string": "def eval(self, acc):"},
                        {"string": "    return acc"},
                        {"string": "%%%"}
                    ]}
                },
                {
                    "targetLocator": {"className": "Helper", "modifier": None},
                    "block": {"lines": [
                        {"string": "%%%"},
                        {"string": "class Helper: pass"},
                        {"string": "%%%"}
                    ]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "import"},
                    "block": {"lines": [
                        {"string": "%%%"},
                        {"string": "import os"},
                        {"string": "%%%"}
                    ]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "top"},
                    "block": {"lines": [{"string": "%%%"}, {"string": "# top"}, {"string": "%%%"}]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "class"},
                    "block": {"lines": [{"string": "%%%"}, {"string": "(Mixin)"}, {"string": "%%%"}]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "init"},
                    "block": {"lines": [{"string": "%%%"}, {"string": "self.x = 1"}, {"string": "%%%"}]}
                }
            ]
        }
    ]
}


def _get_fragments(spec=_ARITH_SPEC_WITH_FRAGMENTS, section_index=0):
    model = build_model(spec)
    return model['semantic_sections'][section_index]['fragments']


def test_fragment_kind_body_for_known_class():
    frags = _get_fragments()
    addrest_body = next(f for f in frags if f['class_name'] == 'AddRest' and f['kind'] == 'body')
    assert addrest_body['kind'] == 'body'


def test_fragment_kind_file_for_unknown_class():
    frags = _get_fragments()
    helper = next(f for f in frags if f['class_name'] == 'Helper')
    assert helper['kind'] == 'file'


def test_fragment_kind_import_from_modifier():
    frags = _get_fragments()
    import_frag = next(f for f in frags if f['kind'] == 'import')
    assert import_frag['class_name'] == 'AddRest'


def test_fragment_kind_top_from_modifier():
    frags = _get_fragments()
    top_frag = next(f for f in frags if f['kind'] == 'top')
    assert top_frag['class_name'] == 'AddRest'


def test_fragment_kind_class_from_modifier():
    frags = _get_fragments()
    class_frag = next(f for f in frags if f['kind'] == 'class')
    assert class_frag['class_name'] == 'AddRest'


def test_fragment_kind_init_from_modifier():
    frags = _get_fragments()
    init_frag = next(f for f in frags if f['kind'] == 'init')
    assert init_frag['class_name'] == 'AddRest'


def test_fragment_body_strips_percent_markers():
    frags = _get_fragments()
    addrest_body = next(f for f in frags if f['class_name'] == 'AddRest' and f['kind'] == 'body')
    assert addrest_body['body'] == 'def eval(self, acc):\n    return acc'


def test_fragment_body_preserves_indentation():
    frags = _get_fragments()
    addrest_body = next(f for f in frags if f['class_name'] == 'AddRest' and f['kind'] == 'body')
    assert '    return acc' in addrest_body['body']


def test_fragment_class_name_passed_verbatim():
    frags = _get_fragments()
    helper = next(f for f in frags if f['class_name'] == 'Helper')
    assert helper['class_name'] == 'Helper'


def test_semantic_section_has_fragments_key():
    model = build_model(_ARITH_SPEC_WITH_FRAGMENTS)
    assert 'fragments' in model['semantic_sections'][0]


def test_empty_codeFragmentList_gives_empty_fragments():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {"rules": []},
        "semantics": [{"language": "Java", "tool": "Java", "codeFragmentList": []}]
    }
    model = build_model(spec)
    assert model['semantic_sections'][0]['fragments'] == []


# ---- entry_point pass-through ----

def test_semantic_section_entry_point_null_when_absent():
    model = build_model(_TRIVIAL_SPEC)
    assert model['semantic_sections'][0].get('entry_point') is None


def test_semantic_section_entry_point_when_present():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {"rules": []},
        "semantics": [{"language": "Python", "tool": "calc", "entry_point": "_run", "codeFragmentList": []}]
    }
    model = build_model(spec)
    assert model['semantic_sections'][0]['entry_point'] == '_run'


# ---- rule_name on classes ----

def test_trivial_class_has_rule_name():
    model = build_model(_TRIVIAL_SPEC)
    assert model['classes'][0]['rule_name'] == 'program'


def test_arith_abstract_class_has_rule_name():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['rule_name'] == 'ExprRest'


def test_arith_concrete_subclass_has_parent_rule_name():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    assert addrest['rule_name'] == 'ExprRest'


def test_arith_nilrest_has_parent_rule_name():
    model = build_model(_ARITH_SPEC)
    nilrest = next(c for c in model['classes'] if c['name'] == 'NilRest')
    assert nilrest['rule_name'] == 'ExprRest'


def test_arith_expr_has_rule_name():
    model = build_model(_ARITH_SPEC)
    expr = next(c for c in model['classes'] if c['name'] == 'Expr')
    assert expr['rule_name'] == 'Expr'


_ARBNO_SPEC = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "rands", "isTerminal": False, "isCapturing": True, "altName": "rands"}
                ]
            },
            {
                "lhs": {"name": "rands", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "expr", "isTerminal": False, "isCapturing": True, "altName": "expr"}
                ],
                "separator": {"name": "COMMA", "isTerminal": True, "isCapturing": False}
            },
            {
                "lhs": {"name": "expr", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                ]
            }
        ]
    },
    "semantics": []
}


def test_arbno_class_field_has_is_list_true():
    model = build_model(_ARBNO_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['is_list'] is True


def test_arbno_field_name_has_list_suffix():
    model = build_model(_ARBNO_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['name'] == 'exprList'


def test_arbno_field_type_is_base_element_type():
    model = build_model(_ARBNO_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['type'] == 'Expr'


def test_non_arbno_field_has_is_list_false():
    model = build_model(_TRIVIAL_SPEC)
    field = model['classes'][0]['fields'][0]
    assert field['is_list'] is False


def test_arbno_token_field_has_correct_type():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {
            "rules": [
                {
                    "lhs": {"name": "items", "altName": None, "isTerminal": False, "isCapturing": False},
                    "rhsSymbolList": [
                        {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                    ],
                    "separator": None
                }
            ]
        },
        "semantics": []
    }
    model = build_model(spec)
    items = next(c for c in model['classes'] if c['name'] == 'Items')
    assert items['fields'][0]['name'] == 'numList'
    assert items['fields'][0]['type'] == 'Token'
    assert items['fields'][0]['is_list'] is True


def test_extract_body_strips_percent_markers_with_trailing_newlines():
    from .build_model import _extract_body
    lines = [
        {'string': '%%%\n'},
        {'string': '    public void $run() {\n'},
        {'string': '    }\n'},
        {'string': '%%%\n'},
    ]
    result = _extract_body(lines)
    assert '%%%' not in result
    assert result == '    public void $run() {\n    }'


def test_extract_body_strips_percent_markers_with_trailing_spaces():
    from .build_model import _extract_body
    lines = [{'string': '%%% \n'}, {'string': '    body line\n'}, {'string': '%%% \n'}]
    result = _extract_body(lines)
    assert '%%%' not in result
    assert result == '    body line'


def test_semantic_section_language_normalized_to_lowercase():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {"rules": []},
        "semantics": [{"language": "PYTHON", "tool": "calc", "codeFragmentList": []}]
    }
    model = build_model(spec)
    assert model['semantic_sections'][0]['language'] == 'python'
