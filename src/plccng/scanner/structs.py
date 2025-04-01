from dataclasses import dataclass

from ..lines import Line


@dataclass
class Match:
    name: str
    lexeme: str
    line: Line
    column: int

@dataclass
class Token(Match):
    pass

@dataclass
class Skip(Match):
    pass

class LexError(Exception):
    def __init__(self, line, column):
        self.line=line
        self.column=column
        self.message=f"Could not match proceeding characters to any token, starting at column '{column}': '{line.string}'"