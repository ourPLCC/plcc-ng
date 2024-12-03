from collections import defaultdict
from .Grammar import Grammar

def build_first_sets(grammar: Grammar):
    return FirstSetBuilder(grammar).build()

class FirstSetBuilder:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = defaultdict(set)

    def build(self):
        self._addEpsilon()
        self._addTerminals()
        self._addNonterminals()
        self._addProductions()
        return self.firstSets

    def _addEpsilon(self):
        self.firstSets[self.grammar.getEpsilon()] = {self.grammar.getEpsilon()}

    def _addTerminals(self):
        for symbol in self.grammar.getTerminals():
            self.firstSets[symbol] = {symbol}

    def _addNonterminals(self):
        change = True
        while change:
            change = False
            for symbol in self.grammar.getNonterminals():
                N = len(self.firstSets[symbol])
                self._updateNonterminal(symbol)
                if N != len(self.firstSets[symbol]):
                    change = True

    def _updateNonterminal(self, symbol):
        productions = self.grammar.getRules()[symbol]
        self._update(productions, symbol)

    def _addProductions(self):
        for nonterminal, productions in self.grammar.getRules().items():
            self._update(productions)
        return self.firstSets

    def _update(self, withProductions, key=None):
        for production in withProductions:
            k = production if key is None else key
            allDeriveEpsilon = True
            for s in production:
                symFirst = self.firstSets[s]
                self.firstSets[k].update(symFirst - {self.grammar.getEpsilon()})
                if self.grammar.getEpsilon() not in symFirst:
                    allDeriveEpsilon = False
                    break
            if allDeriveEpsilon:
                self.firstSets[k].add(self.grammar.getEpsilon())
