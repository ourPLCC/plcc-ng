from collections import defaultdict
from .Grammar import Grammar
from .errors import LeftRecursionException

def generate_first_sets(grammar: Grammar):
    return FirstSetGenerator(grammar).generate()

class FirstSetGenerator:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = defaultdict(set)
        self.memoFirst = {}
        self.callStack = []

    def generate(self):
        for symbol in self.grammar.getNonterminals():
            self.firstSets[symbol.name] = self._computeFirst(symbol)
        return self.firstSets

    def _computeFirst(self, symbol):
        if symbol.name in self.memoFirst:
            return self.memoFirst[symbol.name]
        if self.grammar.isTerminal(symbol.specObject):
            return {symbol.name}
        if symbol.name in self.callStack:
            raise LeftRecursionException(symbol.name)
        self.callStack.append(symbol.name)
        first = {self.grammar.getEpsilon().name} if symbol == self.grammar.getEpsilon() else self._computeFirstForNonterminal(symbol)
        self.callStack.pop()
        self.memoFirst[symbol.name] = first
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

    def _hasEpsilonRule(self, symbol):
        return any(rule[0] == self.grammar.getEpsilon() for rule in self.grammar.getRules()[symbol.name])
