import pytest
import docopt

from .make import main as run_main, validate_tool_name


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_validate_tool_name_accepts_valid():
    validate_tool_name('diagram')
    validate_tool_name('Java')
    validate_tool_name('my-tool')
    validate_tool_name('tool_123')


def test_validate_tool_name_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_tool_name('../etc')
    with pytest.raises(ValueError):
        validate_tool_name('foo/bar')
    with pytest.raises(ValueError):
        validate_tool_name('/absolute')


def test_validate_tool_name_rejects_empty():
    with pytest.raises(ValueError):
        validate_tool_name('')
