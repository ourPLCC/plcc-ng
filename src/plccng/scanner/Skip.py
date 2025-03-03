from dataclasses import dataclass


@dataclass
class Skip:
    lexeme: str
    name: str
    column: int
