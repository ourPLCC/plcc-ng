from .Grammar import Grammar
import copy

def check_left_recursion(grammar: Grammar):
    return LeftRecursionChecker(grammar).getLeftRecursion()

class LeftRecursionChecker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammarCopy = copy.deepcopy(grammar)
        self.substitutions = {}
        self.rulesFromOriginal = []
        self.rulesToTraverse = []
        self.visited = set()

    def getLeftRecursion(self):
        leftRecursion = []
        seen = []
        for nt in self._getNonterminals():
            leftRecursion += self._getLeftRecursion(nt, seen)
            seen.append(nt)
        return leftRecursion

    def _getLeftRecursion(self, nonterm, seen):
        instances = []
        self._expand(nonterm, seen)
        for rule in self._getDirectLeftRecursion(nonterm):
            offendingRules = self._getOriginalGrammarRules(nonterm, rule)
            instances.append(offendingRules)
        return instances

    def _expand(self, definedNonterm, seen):
        for nt in seen:
            for original in self._getFormsStartingWithNonterm(definedNonterm=definedNonterm, firstNonterm=nt):
                self._removeRule(definedNonterm, original)
                for expandedFirstNonterm in self._getForms(original[0]):
                    new = expandedFirstNonterm + original[1:]
                    self._addRule(definedNonterm, new)
                    self._recordExpansion(new, original, expandedFirstNonterm)

    def _getFormsStartingWithNonterm(self, definedNonterm, firstNonterm):
        return [f for f in self._getForms(definedNonterm) if f[0] == firstNonterm]

    def _recordExpansion(self, new, original, expandedNonterm):
        self.substitutions[new] = (original, expandedNonterm)

    def _getDirectLeftRecursion(self, nt):
        return [r for r in self.grammarCopy.getForms(nt) if r[0] == nt]

    def _getOriginalGrammarRules(self, nt, startRule):
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
            origRuleR, origRuleS = self.substitutions[rhs]
            self.rulesToTraverse.extend([(lhs, origRuleR), (origRuleR[0], origRuleS)])

    def _ruleInOriginalGrammar(self, lhs, rhs):
        return rhs in self.grammar.getForms(lhs)

    def _getForms(self, lhs):
        return self.grammarCopy.getForms(lhs)

    def _getNonterminals(self):
        return self.grammar.getNonterminalList()

    def _removeRule(self, nt, form):
        self.grammarCopy.removeRule(nt, form)

    def _addRule(self, nt, form):
        self.grammarCopy.addRule(nt, form)
