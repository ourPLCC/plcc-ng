from plccng.lineparse.Line import Line
from plccng.spec.LhsNonTerminal import LhsNonTerminal
from plccng.spec.Symbol import Symbol


from dataclasses import dataclass


@dataclass(frozen=True)
class SyntacticRule:
    line: Line
    lhs: LhsNonTerminal
    rhsSymbolList: list[Symbol]
    pass
