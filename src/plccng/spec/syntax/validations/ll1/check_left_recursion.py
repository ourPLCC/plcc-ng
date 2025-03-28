from .Grammar import Grammar
import copy

def check_left_recursion(grammar):
    return LeftRecursionChecker(grammar).check()

class LeftRecursionChecker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammarCopy = copy.deepcopy(grammar)
        self.substitutions = {}
        self.nonterminalsInOrder = list(self.grammarCopy.getRules().keys())

    def check(self):
        allLeftRecursionInstances = []
        for n in self.nonterminalsInOrder:
            self._handleLeftRecursionSubstitutions(n)
            directLeftRecursiveRules = self._findDirectLeftRecursion(n)
            if directLeftRecursiveRules:
                origCompleteRules = self._traverseSubstitutionsForOriginal(n, directLeftRecursiveRules)
                allLeftRecursionInstances.append(origCompleteRules)
        return allLeftRecursionInstances if allLeftRecursionInstances else None

    def _handleLeftRecursionSubstitutions(self, n):
        rulesDict = self.grammarCopy.getRules()
        currNontermRules = rulesDict[n]
        for prevNonterm in self.nonterminalsInOrder[:self.nonterminalsInOrder.index(n)]:
            rulesToRemove = set()
            newRules = []
            for r in currNontermRules:
                if r[0] == prevNonterm:
                    rulesToRemove.add(r)
                    for prevNontermRule in rulesDict[prevNonterm]:
                        newRule = prevNontermRule + r[1:]
                        newRules.append(newRule)
                        self.substitutions[newRule] = (r, prevNontermRule, prevNonterm)
            for r in rulesToRemove:
                rulesDict[n].remove(r)
            rulesDict[n].extend(newRules)

    def _findDirectLeftRecursion(self, n):
        return [r for r in self.grammarCopy.getRules()[n] if r[0] == n]

    def _traverseSubstitutionsForOriginal(self, n, startRules):
        rulesFromOriginal = []
        rulesToTraverse = [(n, rule) for rule in startRules]
        visited = set()
        while rulesToTraverse:
            lhs, rhs = rulesToTraverse.pop(0)
            rule = (lhs, rhs)
            if rule in visited:
                continue
            visited.add(rule)
            if self._ruleInOriginalGrammar(lhs, rhs):
                rulesFromOriginal.append(rule)

            if rhs in self.substitutions:
                origRuleR, origRuleS, origNontermForS = self.substitutions[rhs]
                rulesToTraverse.append((n, origRuleR))
                rulesToTraverse.append((origNontermForS, origRuleS))

        return rulesFromOriginal

    def _ruleInOriginalGrammar(self, lhs, rhs):
        return rhs in self.grammar.getRules().get(lhs, [])
