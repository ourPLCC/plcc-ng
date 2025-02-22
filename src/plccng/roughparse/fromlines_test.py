from plccng.lineparse import Line
from .fromlines import fromlines
from .structs import Divider


def test_from_lines():
    assert list(fromlines([Line('%', 1, None)])) == [
        Divider(tool='Java', language='Java', line=Line('%', 1, None))
    ]
