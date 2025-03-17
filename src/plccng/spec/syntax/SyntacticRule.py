from dataclasses import dataclass

from ..lines import Line
from .LhsNonTerminal import LhsNonTerminal
from .Symbol import Symbol


@dataclass(frozen=True)
class SyntacticRule:
    line: Line
    lhs: LhsNonTerminal
    rhsSymbolList: list[Symbol]
    pass
