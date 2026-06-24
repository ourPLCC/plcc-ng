import pytest

from .validate import validate_fragments


def _classes():
    return [
        {'name': 'ExprRest', 'abstract': True,  'extends': None},
        {'name': 'AddRest',  'abstract': False, 'extends': 'ExprRest'},
        {'name': 'NilRest',  'abstract': False, 'extends': 'ExprRest'},
        {'name': 'Prog',     'abstract': False, 'extends': None},
    ]


# --- Group 1: valid names pass silently ---

@pytest.mark.parametrize('kind', ['top', 'import', 'body', 'file'])
def test_abstract_rule_name_is_valid(kind):
    validate_fragments([{'class_name': 'ExprRest', 'kind': kind}], _classes())


@pytest.mark.parametrize('kind', ['top', 'import', 'body', 'file'])
def test_lone_concrete_name_is_valid(kind):
    validate_fragments([{'class_name': 'Prog', 'kind': kind}], _classes())


def test_unknown_name_is_valid_for_file_fragments():
    validate_fragments([{'class_name': 'Helpers', 'kind': 'file'}], _classes())


def test_empty_fragment_list_is_valid():
    validate_fragments([], _classes())


# --- Group 2: concrete-with-abstract-parent errors ---

@pytest.mark.parametrize('kind', ['top', 'import', 'body', 'file'])
def test_concrete_alternative_name_raises_for_all_kinds(kind):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'AddRest', 'kind': kind}], _classes())


def test_concrete_error_message_names_the_concrete_class(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'AddRest', 'kind': 'body'}], _classes())
    assert 'AddRest' in capsys.readouterr().err


def test_concrete_error_message_names_the_parent_module(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'AddRest', 'kind': 'body'}], _classes())
    assert 'ExprRest' in capsys.readouterr().err


def test_concrete_error_message_suggests_using_parent(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'NilRest', 'kind': 'top'}], _classes())
    err = capsys.readouterr().err
    assert 'ExprRest' in err


# --- Group 3: unknown name on injected fragment kinds ---

@pytest.mark.parametrize('kind', ['top', 'import', 'body'])
def test_unknown_name_raises_for_injected_kinds(kind):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'Helpers', 'kind': kind}], _classes())


def test_unknown_name_error_message_includes_the_bad_name(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'Helpers', 'kind': 'body'}], _classes())
    assert 'Helpers' in capsys.readouterr().err


def test_unknown_name_error_message_lists_valid_module_names(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'Helpers', 'kind': 'body'}], _classes())
    err = capsys.readouterr().err
    assert 'ExprRest' in err
    assert 'Prog' in err
