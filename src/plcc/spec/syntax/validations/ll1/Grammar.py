from collections import defaultdict


class Grammar:
    def __init__(self):
        self._forms = defaultdict(list)
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

    def removeRule(self, nonterminal, form):
        self._forms[nonterminal].remove(form)

    def _updateStartSymbol(self, nonterminal):
        if self._startSymbol is None:
            self._startSymbol = nonterminal

    def _addForm(self, nonterminal, form):
        self._forms[nonterminal].append(form)

    def _removeFromTerminals(self, nonterminal):
        if nonterminal in self._terminals:
            self._terminals.remove(nonterminal)

    def _addTerminals(self, form):
        for symbol in form:
            if symbol not in self._forms:
                self._terminals.add(symbol)

    def getStartSymbol(self) -> object:
        return self._startSymbol

    def isTerminal(self, object: object) -> bool:
        return object in self._terminals

    def isNonterminal(self, object: object) -> bool:
        return object in self._forms

    def getForms(self, symbol):
        return self._forms[symbol]

    def getRulesIterator(self):
        for X, A in self._forms.items():
            for a in A:
                yield (X, a)

    def getTerminals(self) -> set[object]:
        return self._terminals

    def getNonterminalSet(self) -> set[object]:
        return set(self._forms.keys())

    def getNonterminalList(self):
        return list(sorted(self.getNonterminalSet()))

    def getEpsilon(self):
        return self._epsilon

    def getEof(self):
        return self._eof
