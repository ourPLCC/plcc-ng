from dataclasses import dataclass, KW_ONLY

from .Symbol import Symbol


@dataclass(frozen=True)
class Terminal(Symbol):
    _: KW_ONLY
    isTerminal: bool = True
    isCapturing: bool = False
