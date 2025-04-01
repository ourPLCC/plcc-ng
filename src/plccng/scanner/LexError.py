from dataclasses import dataclass

from ..lines import Line


@dataclass
class LexError:
    line: Line
    column: int
