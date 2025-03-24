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
        for n in self.nonterminalsInOrder:
            self._handleLeftRecursionSubstitutions(n)
            directLeftRecursiveRules = self._findDirectLeftRecursion(n)
            if directLeftRecursiveRules:
                return self._traverseSubstitutionsForOriginal(directLeftRecursiveRules[0])
        return None

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
                        self.substitutions[newRule] = r
            for r in rulesToRemove:
                rulesDict[n].remove(r)
            rulesDict[n].extend(newRules)

    def _findDirectLeftRecursion(self, n):
        return [r for r in self.grammarCopy.getRules()[n] if r[0] == n]

    def _traverseSubstitutionsForOriginal(self, startRule):
        rulesFromOriginal = []
        visited = set()
        rulesToTraverse = [startRule]
        while rulesToTraverse:
            rule = rulesToTraverse.pop(0)
            if rule in visited:
                continue
            visited.add(rule)
            if self._ruleInOriginalGrammar(rule):
                rulesFromOriginal.append(rule)
            if rule in self.substitutions:
                origRule = self.substitutions[rule]
                rulesToTraverse.append(origRule)
        return rulesFromOriginal if rulesFromOriginal else None

    def _ruleInOriginalGrammar(self, rule):
        return any(rule in rules for rules in self.grammar.getRules().values())
