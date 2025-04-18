from dataclasses import dataclass
from ..lines import Line

@dataclass
class Token:
    lexeme: str
    name: str
    line: Line
    column: int
    file: str = ""
