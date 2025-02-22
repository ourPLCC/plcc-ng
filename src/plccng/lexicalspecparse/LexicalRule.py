from dataclasses import dataclass
from plccng.lineparse.Line import Line


@dataclass
class LexicalRule:
    line: Line
    isSkip: bool
    name: str
    pattern: str
