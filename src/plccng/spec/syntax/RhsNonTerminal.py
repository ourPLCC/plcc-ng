from dataclasses import dataclass

from .CapturingSymbol import CapturingSymbol
from .NonTerminal import NonTerminal


@dataclass(frozen=True)
class RhsNonTerminal(CapturingSymbol, NonTerminal):
    pass
