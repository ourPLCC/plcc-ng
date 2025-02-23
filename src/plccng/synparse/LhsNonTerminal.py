from .NonTerminal import NonTerminal


from dataclasses import dataclass


@dataclass(frozen=True)
class LhsNonTerminal(NonTerminal):
    altName: str | None = None
    pass
