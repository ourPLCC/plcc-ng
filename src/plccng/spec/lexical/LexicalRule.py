from dataclasses import dataclass

from ..lines import Line


@dataclass
class LexicalRule:
    line: Line
    isSkip: bool
    name: str
    pattern: str
