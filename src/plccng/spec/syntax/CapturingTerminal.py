from dataclasses import dataclass

from .CapturingSymbol import CapturingSymbol
from .Terminal import Terminal


@dataclass(frozen=True)
class CapturingTerminal(CapturingSymbol, Terminal):
    pass
