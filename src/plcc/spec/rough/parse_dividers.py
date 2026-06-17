import re

from ...lines import Line
from .Divider import Divider
from .UnexpectedTokensOnDividerError import UnexpectedTokensOnDividerError

_BARE_PERCENT = re.compile(r'^%\s*$')
_PERCENT_PREFIX = re.compile(r'^%(?:\s|$)')
_FIRST_TOKEN = re.compile(r'^%\s*(\S)')


def parse_dividers(lines):
    if not lines:
        return
    for line in lines:
        if isinstance(line, Line) and _PERCENT_PREFIX.match(line.string):
            if _BARE_PERCENT.match(line.string):
                yield Divider(line=line)
            else:
                match = _FIRST_TOKEN.match(line.string)
                col = match.start(1) + 1
                raise UnexpectedTokensOnDividerError(line=line, column=col)
        else:
            yield line
