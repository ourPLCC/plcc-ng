from .CapturingSymbol import CapturingSymbol
from .Terminal import Terminal


from dataclasses import dataclass


@dataclass(frozen=True)
class CapturingTerminal(CapturingSymbol, Terminal):
    pass
