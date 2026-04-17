import pytest

from .scan import main as scan_main
from .rep import main as rep_main


def _exits_nonzero(fn):
    with pytest.raises(SystemExit) as exc:
        fn([])
    assert exc.value.code != 0


def test_rep_exits_nonzero():
    _exits_nonzero(rep_main)


