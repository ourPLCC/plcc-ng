from dataclasses import dataclass

from ..specparse import Line


@dataclass
class LexError:
    line: Line
    column: int
