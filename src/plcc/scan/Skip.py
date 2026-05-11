from dataclasses import dataclass, field
from ..lines import Line

@dataclass
class Skip:
    lexeme: str
    name: str
    line: Line
    column: int
    pattern: str = field(default="", compare=False)
    attempts: list = field(default_factory=list, compare=False)
