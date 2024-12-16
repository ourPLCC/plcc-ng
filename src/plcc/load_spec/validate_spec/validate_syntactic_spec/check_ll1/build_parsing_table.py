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
    table = defaultdict(set)

    for X in g.getNonterminals():
        for a in g.getRules()[X]:
            for t in FIRST[a]:
                table[(X, t)].add(a)
            if g.getEpsilon() in FIRST[a]:
                for t in FOLLOW[X]:
                    table[(X, t)].add(a)
    return Table(table)
