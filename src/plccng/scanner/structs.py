from dataclasses import dataclass
from ..spec import LexicalSpecError

@dataclass
class HasLexErrors(Exception):
    lexErrors: list[LexicalSpecError]
