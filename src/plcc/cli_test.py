import pytest

from plcc.cli import parse_args

_DOC = """Usage: test [-t]
Options:
  -t --trace  Trace.
"""

_DOC_POSITIONAL = """Usage: test FILE
"""


def test_valid_args_returns_dict():
    args = parse_args(_DOC, ['-t'])
    assert args['--trace'] is True


def test_unrecognized_short_option_exits_1(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC, ['-x'])
    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "error: unrecognized option '-x'" in err
    assert "Usage:" in err


def test_unrecognized_long_option_exits_1(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC, ['--unknown'])
    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "error: unrecognized option '--unknown'" in err
    assert "Usage:" in err


def test_duplicate_option_exits_1(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC, ['-t', '-t'])
    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "error: duplicate option '--trace'" in err
    assert "Usage:" in err


def test_missing_positional_passes_through_unchanged(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC_POSITIONAL, [])
    _, err = capsys.readouterr()
    # Our rewriter did NOT touch this — no "error: unrecognized/duplicate" prefix
    assert "error: unrecognized" not in err
    assert "error: duplicate" not in err
    # docopt's original message is carried in the exception code
    assert "Usage:" in str(exc.value.code)
