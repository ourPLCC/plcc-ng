# src/plcc/cmd/spec_test.py
import pytest
from plcc.cmd.spec import validate_spec_flag, spec_flag_for_child, SPEC_OPTION
from plcc.build.spec import DEFAULT_SPEC_FILE


def test_spec_option_contains_flag():
    assert '--spec' in SPEC_OPTION


def test_spec_option_contains_default_filename():
    assert DEFAULT_SPEC_FILE in SPEC_OPTION


def test_validate_spec_flag_none_does_nothing():
    validate_spec_flag('plcc-test', {'--spec': None})


def test_validate_spec_flag_existing_file_does_nothing(tmp_path):
    f = tmp_path / 'foo.plcc'
    f.write_text('')
    validate_spec_flag('plcc-test', {'--spec': str(f)})


def test_validate_spec_flag_missing_file_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        validate_spec_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert exc.value.code != 0


def test_validate_spec_flag_missing_file_prints_cmd_name(capsys):
    with pytest.raises(SystemExit):
        validate_spec_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert 'plcc-test' in capsys.readouterr().err


def test_validate_spec_flag_missing_file_prints_path(capsys):
    with pytest.raises(SystemExit):
        validate_spec_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert 'nonexistent.plcc' in capsys.readouterr().err


def test_spec_flag_for_child_none_returns_empty():
    assert spec_flag_for_child({'--spec': None}) == []


def test_spec_flag_for_child_path_returns_flag():
    assert spec_flag_for_child({'--spec': 'foo.plcc'}) == ['--spec=foo.plcc']
