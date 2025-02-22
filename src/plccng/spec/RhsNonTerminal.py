from plccng.spec.CapturingSymbol import CapturingSymbol
from plccng.spec.NonTerminal import NonTerminal


from dataclasses import dataclass


@dataclass(frozen=True)
class RhsNonTerminal(CapturingSymbol, NonTerminal):
    pass
