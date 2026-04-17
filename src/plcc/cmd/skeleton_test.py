import pytest

from .scan import main as scan_main
from .parse import main as parse_main
from .rep import main as rep_main


def _exits_nonzero(fn):
    with pytest.raises(SystemExit) as exc:
        fn([])
    assert exc.value.code != 0


def test_scan_exits_nonzero():
    _exits_nonzero(scan_main)


def test_parse_exits_nonzero():
    _exits_nonzero(parse_main)


def test_rep_exits_nonzero():
    _exits_nonzero(rep_main)


