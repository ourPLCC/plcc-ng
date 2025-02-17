from dataclasses import dataclass

@dataclass
class Line:
    text: str
    number: int
    file: str = None

@dataclass
class LexError:
    line: Line
    column: int

@dataclass
class Token:
    lexeme: str
    name: str

@dataclass
class Skip:
    lexeme: str
