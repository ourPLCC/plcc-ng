from collections import defaultdict

class Grammar:
    def __init__(self):
        self._rules = defaultdict(list)
        self._startSymbol = None
        self._terminals = set()
        self._eof = object()
        self._epsilon = object()

    def addRule(self, nonterminal: object, form: list[object]):
        f = tuple(form)
        self._updateStartSymbol(nonterminal)
        self._addForm(nonterminal, f)
        self._removeFromTerminals(nonterminal)
        self._addTerminals(f)

    def _updateStartSymbol(self, nonterminal):
        if self._startSymbol is None:
            self._startSymbol = nonterminal

    def _addForm(self, nonterminal, form):
        self._rules[nonterminal].append(form)

    def _removeFromTerminals(self, nonterminal):
        if nonterminal in self._terminals:
            self._terminals.remove(nonterminal)

    def _addTerminals(self, form):
        for symbol in form:
            if symbol not in self._rules:
                self._terminals.add(symbol)

    def getStartSymbol(self) -> object:
        return self._startSymbol

    def isTerminal(self, object: object) -> bool:
        return object in self._terminals

    def isNonterminal(self, object: object) -> bool:
        return object in self._rules

    def getRules(self) -> dict[object, list[tuple[object]]]:
        return self._rules

    def getRulesIterator(self):
        for X, A in self._rules.items():
            for a in A:
                yield (X, a)

    def getTerminals(self) -> set[object]:
        return self._terminals

    def getNonterminals(self) -> set[object]:
        return set(self._rules.keys())

    def getEpsilon(self):
        return self._epsilon

    def getEof(self):
        return self._eof
