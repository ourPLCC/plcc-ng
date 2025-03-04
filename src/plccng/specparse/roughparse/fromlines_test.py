from plccng.lineparse.Line import Line

from .Divider import Divider
from .fromlines import fromlines


def test_from_lines():
    assert list(fromlines([Line('%', 1, None)])) == [
        Divider(tool='Java', language='Java', line=Line('%', 1, None))
    ]
