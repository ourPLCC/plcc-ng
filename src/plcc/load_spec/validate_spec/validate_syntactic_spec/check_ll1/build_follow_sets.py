from collections import defaultdict
from .Grammar import Grammar
from .build_first_sets import build_first_sets

def build_follow_sets(grammar: Grammar, firsts):
    return FollowSetBuilder(grammar, firsts).build()

class FollowSetBuilder:
    def __init__(self, grammar: Grammar, firsts):
        self.grammar = grammar
        self.firstSets = firsts
        self.followSets = defaultdict(set)
        self._changed = False

    def build(self):
        self._updateStartSymbol()
        self._updateNonterminalsUntilNoChange()
        return self.followSets

    def _updateStartSymbol(self):
        self.followSets[self.grammar.getStartSymbol()].add(self.grammar.getEof())

    def _updateNonterminalsUntilNoChange(self):
        self._changed = True
        while self._changed:
            self._changed = False
            self._updateNonterminals()

    def _updateNonterminals(self):
        for nonterminal in self.grammar.getNonterminals():
            self._updateNonterminal(nonterminal)

    def _updateNonterminal(self, nonterminal):
        for lhs, rules in self.grammar.getRules().items():
            for production in rules:
                self._updateWithEachOccuranceOfNonterminalInProduction(nonterminal, lhs, production)

    def _updateWithEachOccuranceOfNonterminalInProduction(self, nonterminal, lhs, production):
        for i, symbol in enumerate(production):
            if symbol == nonterminal:
                self._updateWithSingleOccuranceOfNonterminalInProduction(lhs, production, i, nonterminal)

    def _updateWithSingleOccuranceOfNonterminalInProduction(self, lhs, rules, index, nonterminal):
        if self._isLastOccuranceInRule(rules, index):
            self._addFollowOfLHS(lhs, nonterminal)
        else:
            self._addFirstOfNextSymbol(rules[index + 1], nonterminal)
            if self._canDeriveEmpty(rules[index + 1:]):
                self._addFollowOfLHS(lhs, nonterminal)

    def _isLastOccuranceInRule(self, rules, index):
        return index + 1 == len(rules)

    def _addFirstOfNextSymbol(self, nextSymbol, nonterminal):
        nextFirst = self.firstSets[nextSymbol] - {self.grammar.getEpsilon()}
        origLen = len(self.followSets[nonterminal])
        self.followSets[nonterminal].update(nextFirst)
        if len(self.followSets[nonterminal]) > origLen:
            self._changed = True

    def _addFollowOfLHS(self, lhs, nonterminal):
        origLen = len(self.followSets[nonterminal])
        self.followSets[nonterminal].update(self.followSets[lhs])
        if len(self.followSets[nonterminal]) > origLen:
            self._changed = True

    def _canDeriveEmpty(self, symbols):
        return all(self._canDeriveEmptyString(symbol) for symbol in symbols)

    def _canDeriveEmptyString(self, symbol):
        if symbol == self.grammar.getEpsilon():
            return True
        if self.grammar.isNonterminal(symbol):
            if self._allRulesCanDeriveEmpty(symbol):
                return True
        return False

    def _allRulesCanDeriveEmpty(self, symbol):
        if all(self._canDeriveEmptyString(rule) for rule in self.grammar.getRules()[symbol][0]):
            return True

