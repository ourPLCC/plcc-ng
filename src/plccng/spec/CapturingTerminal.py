from plccng.spec.CapturingSymbol import CapturingSymbol
from plccng.spec.Terminal import Terminal


from dataclasses import dataclass


@dataclass(frozen=True)
class CapturingTerminal(CapturingSymbol, Terminal):
    pass
