from .Grammar import Grammar
import copy

def check_left_recursion(grammar: Grammar):
    return LeftRecursionChecker(grammar).check()

class LeftRecursionChecker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammarCopy = copy.deepcopy(grammar)
        self.substitutions = {}
        self.nonterminalsInOrder = list(self.grammarCopy.getRules().keys())
        self.rulesDict = self.grammarCopy.getRules()

    def check(self):
        allLeftRecursionInstances = []
        for n in self.nonterminalsInOrder:
            self._handleLeftRecursionSubstitutions(n)
            directLeftRecursiveRules = self._findDirectLeftRecursion(n)
            if directLeftRecursiveRules:
                for rule in self._findDirectLeftRecursion(n):
                    allLeftRecursionInstances.append(self._traverseSubstitutionsForOriginal(n, rule))
        return allLeftRecursionInstances if allLeftRecursionInstances else None

    def _handleLeftRecursionSubstitutions(self, n):
        currNontermRules = self.rulesDict[n]
        for prevNonterm in self.nonterminalsInOrder[:self.nonterminalsInOrder.index(n)]:
            self._substitute(currNontermRules, prevNonterm)

    def _substitute(self, currNontermRules, prevNonterm):
        rulesToRemove = set()
        newRules = []
        for r in currNontermRules:
            if r[0] == prevNonterm:
                rulesToRemove.add(r)
                for prevNontermRule in self.rulesDict[prevNonterm]:
                    newRule = prevNontermRule + r[1:]
                    newRules.append(newRule)
                    self.substitutions[newRule] = (r, prevNontermRule, prevNonterm)
        for r in rulesToRemove:
            currNontermRules.remove(r)
        currNontermRules.extend(newRules)

    def _findDirectLeftRecursion(self, n):
        return [r for r in self.grammarCopy.getRules()[n] if r[0] == n]

    def _traverseSubstitutionsForOriginal(self, n, startRule):
        rulesFromOriginal = []
        rulesToTraverse = [(n, startRule)]
        visited = set()
        while rulesToTraverse:
            rulesFromOriginal, rulesToTraverse, visited = self._traverse(rulesFromOriginal, rulesToTraverse, visited)
        return rulesFromOriginal

    def _traverse(self, rulesFromOriginal, rulesToTraverse, visited):
        lhs, rhs = rulesToTraverse.pop(0)
        rule = (lhs, rhs)
        if rule not in visited:
            visited.add(rule)
            if self._ruleInOriginalGrammar(lhs, rhs):
                rulesFromOriginal.append(rule)
            if rhs in self.substitutions:
                origRuleR, origRuleS, origNontermForS = self.substitutions[rhs]
                rulesToTraverse.append((lhs, origRuleR))
                rulesToTraverse.append((origNontermForS, origRuleS))
        return rulesFromOriginal, rulesToTraverse, visited

    def _ruleInOriginalGrammar(self, lhs, rhs):
        return rhs in self.grammar.getRules().get(lhs, [])
