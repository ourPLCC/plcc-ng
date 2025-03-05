from dataclasses import dataclass

from .Symbol import Symbol


@dataclass(frozen=True)
class NonTerminal(Symbol):
    pass
