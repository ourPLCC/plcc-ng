import pytest

from plcc.lang.reserved_words import check_reserved_field_names, reject_reserved_field_names


def _class(name, fields, abstract=False, extends=None):
    return {
        'name': name,
        'abstract': abstract,
        'extends': extends,
        'fields': fields,
        'rule_name': name,
    }


def test_check_reserved_field_names_reports_a_collision():
    classes = [_class('VarExp', [{'name': 'var', 'type': 'Token', 'is_list': False}])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var'}))
    assert len(errors) == 1
    assert "class 'VarExp'" in errors[0]
    assert "field 'var'" in errors[0]
    assert "javascript reserved word 'var'" in errors[0]


def test_check_reserved_field_names_ignores_non_colliding_fields():
    classes = [_class('VarExp', [{'name': 'name', 'type': 'Token', 'is_list': False}])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var'}))
    assert errors == []


def test_check_reserved_field_names_ignores_list_suffixed_fields():
    classes = [_class('Words', [{'name': 'varList', 'type': 'Token', 'is_list': True}])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var'}))
    assert errors == []


def test_check_reserved_field_names_reports_one_message_per_collision():
    classes = [_class('Pair', [
        {'name': 'var', 'type': 'Token', 'is_list': False},
        {'name': 'class', 'type': 'Token', 'is_list': False},
    ])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var', 'class'}))
    assert len(errors) == 2


def test_reject_reserved_field_names_exits_1_and_prints_stage_prefixed_error(capsys):
    classes = [_class('VarExp', [{'name': 'var', 'type': 'Token', 'is_list': False}])]
    with pytest.raises(SystemExit) as exc_info:
        reject_reserved_field_names(
            classes, 'javascript', frozenset({'var'}), stage='plcc-javascript-emit'
        )
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.startswith('plcc-javascript-emit: error:')
    assert "field 'var'" in captured.err


def test_reject_reserved_field_names_is_a_noop_when_clean(capsys):
    classes = [_class('VarExp', [{'name': 'name', 'type': 'Token', 'is_list': False}])]
    reject_reserved_field_names(
        classes, 'javascript', frozenset({'var'}), stage='plcc-javascript-emit'
    )
    captured = capsys.readouterr()
    assert captured.err == ''
