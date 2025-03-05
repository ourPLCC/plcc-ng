from dataclasses import dataclass

from .NonTerminal import NonTerminal


@dataclass(frozen=True)
class LhsNonTerminal(NonTerminal):
    altName: str | None = None
    pass
