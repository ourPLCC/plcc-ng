from dataclasses import dataclass

from ..lines import Line


@dataclass
class Match:
    name: str
    lexeme: str
    line: Line
    column: int

@dataclass
class LexError:
    line: Line
    column: int

@dataclass
class Token(Match):
    pass

@dataclass
class Skip(Match):
    pass
