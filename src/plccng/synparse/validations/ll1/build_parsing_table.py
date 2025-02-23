from collections import defaultdict
from .Grammar import Grammar

class Table:
    def __init__(self, table):
        self._table = table

    def getCell(self, X: object, a: object) -> list[tuple[object]]:
        return self._table[(X,a)]

    def getKeys(self):
        return self._table.keys()


def build_parsing_table(
        FIRST: dict[object, set[object]],
        FOLLOW: dict[object, set[object]],
        g: Grammar) -> Table:
    b = TableBuilder()
    b.setGrammar(g)
    b.setFIRST(FIRST)
    b.setFOLLOW(FOLLOW)
    table = b.build()
    return table


class TableBuilder:
    def __init__(self):
        self._grammar = None
        self._FIRST = None
        self._FOLLOWS = None
        self._rawTable = None

    def setGrammar(self, grammar: Grammar):
        self._grammar = grammar

    def setFIRST(self, FIRST: dict[object, set[object]]):
        self._FIRST = FIRST

    def setFOLLOW(self, FOLLOW: dict[object, set[object]]):
        self.FOLLOW = FOLLOW

    def build(self) -> Table:
        self._buildEmptyRawTable()
        self._updateCellsForEachRule()
        table = self._buildTable()
        return table

    def _buildEmptyRawTable(self):
        self._rawTable = defaultdict(set)

    def _updateCellsForEachRule(self):
        for nonterm, prod in self._grammar.getRulesIterator():
            self._addProductionForEachTerminalInFirst(nonterm, prod)
            self._addProductionForEachFollowIfEpsilonInFirst(nonterm, prod)

    def _addProductionForEachTerminalInFirst(self, nonterm, prod):
        for t in self._FIRST[prod]:
            self._rawTable[(nonterm, t)].add(prod)

    def _addProductionForEachFollowIfEpsilonInFirst(self, nonterm, prod):
        if self._grammar.getEpsilon() in self._FIRST[prod]:
            for t in self.FOLLOW[nonterm]:
                self._rawTable[(nonterm, t)].add(prod)

    def _buildTable(self):
        return Table(self._rawTable)
