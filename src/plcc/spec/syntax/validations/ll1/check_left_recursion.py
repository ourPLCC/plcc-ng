from .Grammar import Grammar
import copy


def check_left_recursion(grammar: Grammar):
    return LeftRecursionChecker(grammar).getLeftRecursion()


class LeftRecursionChecker:
    def __init__(self, grammar: Grammar):
        self.grammar = copy.deepcopy(grammar)
        self.nonterminals = grammar.getNonterminalList()
        self.tracker = Tracker(grammar)

    def getLeftRecursion(self):
        leftRecursion = []
        seen = []
        for nt in self.nonterminals:
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
        return [form for form in self._getForms(definedNonterm) if form[0] == firstNonterm]

    def _recordExpansion(self, new, original, expandedNonterm):
        self.tracker.record(original, new, expandedNonterm)

    def _getOriginalGrammarRules(self, nt, startRule):
        return self.tracker.getOriginalGrammarRules(nt, startRule)

    def _getDirectLeftRecursion(self, nt):
        return [form for form in self.grammar.getForms(nt) if form[0] == nt]

    def _getForms(self, lhs):
        return self.grammar.getForms(lhs)

    def _removeRule(self, nt, form):
        self.grammar.removeRule(nt, form)

    def _addRule(self, nt, form):
        self.grammar.addRule(nt, form)


class Tracker:
    def __init__(self, originalGrammar):
        self._substitutions = {}
        self._rulesFromOriginal = []
        self._visited = set()
        self._rulesToTraverse = []
        self._originalGrammar = originalGrammar

    def record(self, originalForm, newForm, expandedNonterminal):
        self._substitutions[newForm] = (originalForm, expandedNonterminal)

    def getOriginalGrammarRules(self, nt, startRule):
        self._rulesFromOriginal = []
        self._rulesToTraverse = [(nt, startRule)]
        self._visited = set()
        while self._rulesToTraverse:
            self._traverseRule()
        return self._rulesFromOriginal

    def _traverseRule(self):
        lhs, rhs = self._rulesToTraverse.pop(0)
        rule = (lhs, rhs)
        if rule not in self._visited:
            self._visited.add(rule)
            self._checkSubstitutionsForOriginalRules(lhs, rhs)

    def _checkSubstitutionsForOriginalRules(self, lhs, rhs):
        if self._isRuleInOriginalGrammar(lhs, rhs):
            self._rulesFromOriginal.append((lhs, rhs))
        if rhs in self._substitutions:
            origRuleR, origRuleS = self._substitutions[rhs]
            self._rulesToTraverse.extend([(lhs, origRuleR), (origRuleR[0], origRuleS)])

    def _isRuleInOriginalGrammar(self, lhs, rhs):
        return rhs in self._originalGrammar.getForms(lhs)
