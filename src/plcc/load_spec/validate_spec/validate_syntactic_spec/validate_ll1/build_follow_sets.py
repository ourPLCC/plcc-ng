from collections import defaultdict
from .Grammar import Grammar
from .build_first_sets import build_first_sets

def build_follow_sets(grammar: Grammar):
    return FollowSetBuilder(grammar).build()

class FollowSetBuilder:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = build_first_sets(grammar)
        self.followSets = defaultdict(set)

    def build(self):
        self.followSets[self.grammar.getStartSymbol()].add(self.grammar.getEOF().name)
        updated = True
        while updated:
            updated = False
            for nonterminal in self.grammar.getNonterminals():
                if self._computeFollow(nonterminal):
                    updated = True
        return self.followSets

    def _computeFollow(self, nonterminal):
        updated = False
        for lhs, rules in self.grammar.getRules().items():
            for lists in rules:
                for i, rule in enumerate(lists):
                    if rule == nonterminal:
                        if self._processFollowRule(lhs, lists, i, nonterminal):
                            updated = True
        return updated

    def _processFollowRule(self, lhs, rules, index, nonterminal):
        updated = False
        if index + 1 < len(rules):
            if self._addFirstOfNextSymbol(rules[index + 1], nonterminal):
                updated = True
        if index + 1 == len(rules) or self._canDeriveEmpty(rules[index + 1:]):
            if self._addFollowOfLHS(lhs, nonterminal):
                updated = True
        return updated

    def _addFirstOfNextSymbol(self, nextSymbol, nonterminal):
        nextFirst = self.firstSets[nextSymbol.name] - {self.grammar.getEpsilon().name}
        origLen = len(self.followSets[nonterminal.name])
        self.followSets[nonterminal.name].update(nextFirst)
        return len(self.followSets[nonterminal.name]) > origLen

    def _addFollowOfLHS(self, lhs, nonterminal):
        origLen = len(self.followSets[nonterminal.name])
        self.followSets[nonterminal.name].update(self.followSets[lhs])
        return len(self.followSets[nonterminal.name]) > origLen

    def _canDeriveEmpty(self, symbols):
        return all(self._canDeriveEmptyString(symbol) for symbol in symbols)

    def _canDeriveEmptyString(self, symbol):
        if symbol == self.grammar.getEpsilon():
            return True
        if self.grammar.isNonterminal(symbol.specObject):
            if self._allRulesCanDeriveEmpty(symbol):
                return True
        return False

    def _allRulesCanDeriveEmpty(self, symbol):
        if all(self._canDeriveEmptyString(rule) for rule in self.grammar.getRules()[symbol.name][0]):
            return True

