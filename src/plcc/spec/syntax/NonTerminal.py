from dataclasses import dataclass, KW_ONLY

from .Symbol import Symbol


@dataclass(frozen=True)
class NonTerminal(Symbol):
    _: KW_ONLY
    isTerminal: bool = False
