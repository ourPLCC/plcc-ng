from dataclasses import dataclass, KW_ONLY

from .NonTerminal import NonTerminal


@dataclass(frozen=True)
class LhsNonTerminal(NonTerminal):
    altName: str | None = None
    _: KW_ONLY
    isCapturing: bool = False
