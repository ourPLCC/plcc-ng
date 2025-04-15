import pytest

from .plccng import plccng


def test_help(capfd):
    with pytest.raises(SystemExit):
        plccng('plccng -h'.split())
    out, err = capfd.readouterr()
    assert "Usage" in out
