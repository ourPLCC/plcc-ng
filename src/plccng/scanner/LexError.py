from dataclasses import dataclass

from ..spec import Line


@dataclass
class LexError:
    line: Line
    column: int
