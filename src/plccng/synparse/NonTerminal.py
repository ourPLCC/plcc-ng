from .Symbol import Symbol


from dataclasses import dataclass


@dataclass(frozen=True)
class NonTerminal(Symbol):
    pass
