from dataclasses import dataclass

from ..lineparse import Line


@dataclass
class LexicalRule:
    line: Line
    isSkip: bool
    name: str
    pattern: str
