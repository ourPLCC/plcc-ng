from collections import defaultdict

class Table:
    def __init__(self):
        self._table = defaultdict(list)

    def getCell(self, X: str, a: str) -> list[set[str]]:
        return self._table[(X,a)]

    def addCell(self, X: str, a: str, rhs:str):
        self._table[(X, a)].append(rhs)

    def getFilledCellLocations(self) -> list[tuple[str, str]]:
        return list(self._table.keys())

def build_parsing_table(first: dict[str, set[str]], follow: dict[str, set[str]], rules: dict[str, list[str]]) -> Table:
    return ParsingTableBuilder(first, follow, rules).build()

class ParsingTableBuilder:
    def __init__(self, first, follow, rules):
        self.first = first
        self.follow = follow
        self.rules = rules
        self.table = Table()

    def build(self):
        self._addRulesToCorrectCells()
        return self.table

    def _addRulesToCorrectCells(self):
        for nonterminal in self.rules.keys():
            for production in self.rules[nonterminal]:
                self._addFirstSetRulesIfValid(nonterminal, production)

                if self._isEpsilonInSet(self.first[production]):
                    self._addFollowSetRules(nonterminal, production)

    def _addFirstSetRulesIfValid(self, nonterminal: str, production: str):
        for t in self.first[production]:
            if self._isTerminalEpisilon(t):
                continue
            self.table.addCell(nonterminal, t, production)

    def _addFollowSetRules(self, nonterminal: str, production: str):
        for t in self.follow[nonterminal]:
            self.table.addCell(nonterminal, t, production)

    def _isTerminalEpisilon(self, t: str):
        return True if t == '' else False

    def _isEpsilonInSet(self, s: set):
        return True if '' in s else False
