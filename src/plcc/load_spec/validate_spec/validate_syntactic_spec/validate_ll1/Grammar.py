from .errors import InvalidFormException

def generate_grammar():
    return Grammar()

class Grammar:
    def __init__(self):
        self.rules = {}
        self.startSymbol = None
        self.terminals = set()
        self.nonterminals = set()

    def addRule(self, nonterminal: object, form: list[object]):
        self._checkParametersForErrors(nonterminal, form)
        self._addRuleList(nonterminal, form)
        self._populateTerminals(form)
        self._updateStartSymbol(nonterminal)

    def _checkParametersForErrors(self, nonterminal: object, form: list[object]):
        if not isinstance(form, list):
            raise InvalidFormException(str(form))
        for symbol in form:
            if not self.hasHashMethod(symbol) or not self.hasEqMethod(symbol):
                raise InvalidFormException(str(form))

    def _addRuleList(self, nonterminal: str, form: list[str]):
        self.nonterminals.add(nonterminal)
        if nonterminal in self.terminals:
            self.terminals.remove(nonterminal)
        if nonterminal not in self.rules:
            self.rules[nonterminal] = []
        self.rules[nonterminal].append(form)

    def _populateTerminals(self, form: list[str]):
        for symbol in form:
            if self.isTerminal(symbol):
                self.terminals.add(symbol)

    def _updateStartSymbol(self, nonterminal: str):
        if self.startSymbol is None:
            self.startSymbol = nonterminal

    def hasHashMethod(self, obj):
        return hasattr(obj, '__hash__') and obj.__hash__ is not None

    def hasEqMethod(self, obj):
        return hasattr(obj, '__eq__')

    def getStartSymbol(self) -> str:
        return self.startSymbol

    def isTerminal(self, object: str) -> bool:
        return not self.isNonterminal(object)

    def isNonterminal(self, object: str) -> bool:
        return object in self.nonterminals

    def getRules(self) -> dict[str, list[list[str]]]:
        return self.rules

    def getTerminals(self) -> set[str]:
        return self.terminals

    def getNonterminals(self) -> set[str]:
        return self.nonterminals
