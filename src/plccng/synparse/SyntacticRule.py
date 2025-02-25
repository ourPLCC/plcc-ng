from plccng.lineparse import Line

from .LhsNonTerminal import LhsNonTerminal
from .Symbol import Symbol


from dataclasses import dataclass


@dataclass(frozen=True)
class SyntacticRule:
    line: Line
    lhs: LhsNonTerminal
    rhsSymbolList: list[Symbol]
    pass
