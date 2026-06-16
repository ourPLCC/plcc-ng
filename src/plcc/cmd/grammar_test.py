import pytest
from plcc.cmd.grammar import validate_grammar_flag, grammar_flag_for_child, GRAMMAR_OPTION
from plcc.build.grammar import DEFAULT_GRAMMAR_FILE


def test_grammar_option_contains_flag():
    assert '--grammar' in GRAMMAR_OPTION


def test_grammar_option_contains_default_filename():
    assert DEFAULT_GRAMMAR_FILE in GRAMMAR_OPTION


def test_validate_grammar_flag_none_does_nothing():
    validate_grammar_flag('plcc-test', {'--grammar': None})


def test_validate_grammar_flag_existing_file_does_nothing(tmp_path):
    f = tmp_path / 'foo.plcc'
    f.write_text('')
    validate_grammar_flag('plcc-test', {'--grammar': str(f)})


def test_validate_grammar_flag_missing_file_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        validate_grammar_flag('plcc-test', {'--grammar': 'nonexistent.plcc'})
    assert exc.value.code != 0


def test_validate_grammar_flag_missing_file_prints_cmd_name(capsys):
    with pytest.raises(SystemExit):
        validate_grammar_flag('plcc-test', {'--grammar': 'nonexistent.plcc'})
    assert 'plcc-test' in capsys.readouterr().err


def test_validate_grammar_flag_missing_file_prints_path(capsys):
    with pytest.raises(SystemExit):
        validate_grammar_flag('plcc-test', {'--grammar': 'nonexistent.plcc'})
    assert 'nonexistent.plcc' in capsys.readouterr().err


def test_grammar_flag_for_child_none_returns_empty():
    assert grammar_flag_for_child({'--grammar': None}) == []


def test_grammar_flag_for_child_path_returns_flag():
    assert grammar_flag_for_child({'--grammar': 'foo.plcc'}) == ['--grammar=foo.plcc']
