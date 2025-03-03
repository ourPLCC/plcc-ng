from dataclasses import dataclass


@dataclass
class Token:
    lexeme: str
    name: str
    column: int
