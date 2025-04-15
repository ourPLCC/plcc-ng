import pytest

from .cli import cli


def test_help(capfd):
    cli('plccng -h'.split()[1:])
    out, err = capfd.readouterr()
    assert "Usage" in out

def test_scan(capfd):
    with pytest.raises(SystemExit):
        cli('plccng scan -h'.split()[1:])
    out, err = capfd.readouterr()
    assert "Usage" in out
