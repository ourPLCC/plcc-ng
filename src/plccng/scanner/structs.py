from dataclasses import dataclass

@dataclass
class Line:
    text: str
    number: int
    file: str = None

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