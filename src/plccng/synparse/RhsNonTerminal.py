from .CapturingSymbol import CapturingSymbol
from .NonTerminal import NonTerminal


from dataclasses import dataclass


@dataclass(frozen=True)
class RhsNonTerminal(CapturingSymbol, NonTerminal):
    pass
