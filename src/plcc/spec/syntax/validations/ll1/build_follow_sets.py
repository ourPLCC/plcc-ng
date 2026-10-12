from collections import defaultdict

from .Grammar import Grammar


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
        for nonterminal in self.grammar.getNonterminalSet():
            self._updateNonterminal(nonterminal)

    def _updateNonterminal(self, nonterminal):
        for lhs in self.grammar.getNonterminalSet():
            for production in self.grammar.getForms(lhs):
                self._updateWithEachOccuranceOfNonterminalInProduction(nonterminal, lhs, production)

    def _updateWithEachOccuranceOfNonterminalInProduction(self, nonterminal, lhs, production):
        for i, symbol in enumerate(production):
            if symbol == nonterminal:
                self._updateWithSingleOccuranceOfNonterminalInProduction(lhs, production, i, nonterminal)

    def _updateWithSingleOccuranceOfNonterminalInProduction(self, lhs, production, index, nonterminal):
        for symbol in production[index + 1:]:
            self._addFirstOfSymbol(symbol, nonterminal)
            if not self._isNullable(symbol):
                break
        else:
            self._addFollowOfLHS(lhs, nonterminal)

    def _addFirstOfSymbol(self, symbol, nonterminal):
        first = self.firstSets[symbol] - {self.grammar.getEpsilon()}
        origLen = len(self.followSets[nonterminal])
        self.followSets[nonterminal].update(first)
        if len(self.followSets[nonterminal]) > origLen:
            self._changed = True

    def _addFollowOfLHS(self, lhs, nonterminal):
        origLen = len(self.followSets[nonterminal])
        self.followSets[nonterminal].update(self.followSets[lhs])
        if len(self.followSets[nonterminal]) > origLen:
            self._changed = True

    def _isNullable(self, symbol):
        # A symbol is nullable iff epsilon is in its FIRST set - already
        # computed correctly (existential over all productions) by
        # build_first_sets, so reuse it rather than re-deriving here.
        return self.grammar.getEpsilon() in self.firstSets[symbol]
