from collections import defaultdict
from .Grammar import Grammar
from .errors import LeftRecursionException

def build_first_sets(grammar: Grammar):
    return FirstSetBuilder(grammar).build()

class FirstSetBuilder:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = defaultdict(set)
        self.callStack = []

    def build(self):
        for symbol in self.grammar.getNonterminals():
            self.firstSets[symbol.name] = self._computeFirst(symbol)
        for symbol in self.grammar.getTerminals():
            self.firstSets[symbol.name] = self._computeFirst(symbol)
        for nonterminal, productions in self.grammar.getRules().items():
            for production in productions:
                concatenatedProduction = " ".join(sym.name for sym in production)
                self.firstSets[concatenatedProduction] = self._computeFirstForProduction(production)
        return self.firstSets

    def _computeFirst(self, symbol):
        if self.grammar.isTerminal(symbol.specObject):
            return {symbol.name}
        if symbol.name in self.callStack:
            raise LeftRecursionException(symbol.name)
        self.callStack.append(symbol.name)
        first = {self.grammar.getEpsilon().name} if symbol == self.grammar.getEpsilon() else self._computeFirstForNonterminal(symbol)
        self.callStack.pop()
        return first

    def _computeFirstForNonterminal(self, symbol):
        first = set()
        allDeriveEpsilon = True
        if self._hasEpsilonRule(symbol):
            first.add(self.grammar.getEpsilon().name)
        for rules in self.grammar.getRules()[symbol.name]:
            for rule in rules:
                symFirst = self._computeFirst(rule)
                first.update(symFirst - {self.grammar.getEpsilon().name})
                if self.grammar.getEpsilon().name not in symFirst:
                    allDeriveEpsilon = False
                    break
            if allDeriveEpsilon:
                first.add(self.grammar.getEpsilon().name)
        return first

    def _computeFirstForProduction(self, production):
        first = set()
        for symbol in production:
            symFirst = self._computeFirst(symbol)
            first.update(symFirst - {self.grammar.getEpsilon().name})
            if self.grammar.getEpsilon().name not in symFirst:
                break
        else:
            first.add(self.grammar.getEpsilon().name)
        return first

    def _hasEpsilonRule(self, symbol):
        return any(rule[0] == self.grammar.getEpsilon() for rule in self.grammar.getRules()[symbol.name])
