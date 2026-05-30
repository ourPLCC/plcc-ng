from collections import defaultdict

from .Grammar import Grammar


class Table:
    def __init__(self, table):
        self._table = table

    def getCell(self, X: object, a: object) -> list[tuple[object]]:
        return self._table[(X, a)]

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
    return b.build()


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
        self._rawTable = defaultdict(list)
        for nonterm, prod in self._grammar.getRulesIterator():
            for t in self._predictSet(nonterm, prod):
                self._rawTable[(nonterm, t)].append(prod)
        return Table(self._rawTable)

    def _predictSet(self, nonterm, prod) -> set:
        terminals = set(self._FIRST[prod]) - {self._grammar.getEpsilon()}
        if self._grammar.getEpsilon() in self._FIRST[prod]:
            terminals |= self.FOLLOW[nonterm]
        return terminals
