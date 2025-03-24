from ...lines import Line
from .Divider import Divider
from .parse_from_lines import parse_from_lines


def test_from_lines():
    assert list(parse_from_lines([Line('%', 1, None)])) == [
        Divider(tool='Java', language='Java', line=Line('%', 1, None))
    ]
