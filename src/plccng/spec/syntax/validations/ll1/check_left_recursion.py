from .Grammar import Grammar
import copy

def check_left_recursion(grammar: Grammar):
    return LeftRecursionChecker(grammar).findLeftRecursion()

class LeftRecursionChecker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammarCopy = copy.deepcopy(grammar)
        self.substitutions = {}
        self.nonterminalsInOrder = list(self.grammarCopy.getRules().keys())
        self.rulesDict = self.grammarCopy.getRules()
        self.rulesFromOriginal = []
        self.rulesToTraverse = []
        self.visited = set()

    def findLeftRecursion(self):
        leftRecursion = []
        seen = []
        for nt in self.nonterminalsInOrder:
            leftRecursion += self._getLeftRecursion(nt, seen)
            seen.append(nt)
        return leftRecursion

    def _substituteRules(self, nt, seen):
        currNontermRules = self.rulesDict[nt]
        for prevNonterm in seen:
            rulesToRemove = self._getRulesToRemove(currNontermRules, prevNonterm)
            newRules = self._makeReplacementRules(rulesToRemove, prevNonterm)
            self._removeRules(currNontermRules, rulesToRemove)
            self._addRules(newRules, currNontermRules)

    def _getLeftRecursion(self, nt, seen):
        instances = []
        self._substituteRules(nt, seen)
        for rule in self._findDirectLeftRecursionInstances(nt):
            instances.append(self._getRulesFromOriginalAfterTraversal(nt, rule))
        return instances

    def _getRulesToRemove(self, currNontermRules, prevNonterm):
        rulesToRemove = set()
        for r in currNontermRules:
            if r[0] == prevNonterm:
                rulesToRemove.add(r)
        return rulesToRemove

    def _makeReplacementRules(self, rulesToRemove, prevNonterm):
        newRules = []
        for rule in rulesToRemove:
            for prevNontermRule in self.rulesDict[prevNonterm]:
                newRule = prevNontermRule + rule[1:]
                newRules.append(newRule)
                self.substitutions[newRule] = (rule, prevNontermRule, prevNonterm)
        return newRules

    def _removeRules(self, currNontermRules, rulesToRemove):
        for rule in rulesToRemove:
            currNontermRules.remove(rule)

    def _addRules(self, newRules, currNontermRules):
        currNontermRules.extend(newRules)

    def _findDirectLeftRecursionInstances(self, nt):
        return [r for r in self.grammarCopy.getRules()[nt] if r[0] == nt]

    def _getRulesFromOriginalAfterTraversal(self, nt, startRule):
        self.rulesFromOriginal = []
        self.rulesToTraverse = [(nt, startRule)]
        self.visited = set()
        while self.rulesToTraverse:
            self._traverseRule()
        return self.rulesFromOriginal

    def _traverseRule(self):
        lhs, rhs = self.rulesToTraverse.pop(0)
        rule = (lhs, rhs)
        if rule not in self.visited:
            self.visited.add(rule)
            self._checkSubstitutionsForOriginalRules(lhs, rhs)

    def _checkSubstitutionsForOriginalRules(self, lhs, rhs):
        if self._ruleInOriginalGrammar(lhs, rhs):
            self.rulesFromOriginal.append((lhs, rhs))
        if rhs in self.substitutions:
            origRuleR, origRuleS, origNontermForS = self.substitutions[rhs]
            self.rulesToTraverse.extend([(lhs, origRuleR), (origNontermForS, origRuleS)])

    def _ruleInOriginalGrammar(self, lhs, rhs):
        return rhs in self.grammar.getRules().get(lhs, [])
