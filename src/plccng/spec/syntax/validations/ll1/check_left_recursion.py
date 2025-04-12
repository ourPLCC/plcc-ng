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
        self._substituteForms(nonterm, seen)
        for rule in self._getDirectLeftRecursion(nonterm):
            instances.append(self._getRulesFromOriginal(nonterm, rule))
        return instances

    def _substituteForms(self, nonterm, seen):
        forms = self._getForms(nonterm)
        for nt in seen:
            formsToRemove = self._getFormsThatStartWith(forms, nt)
            formsToAdd = self._makeReplacementForms(formsToRemove, nt)
            self._removeRules(nonterm, formsToRemove)
            self._addRules(nonterm, formsToAdd)

    def _getFormsThatStartWith(self, forms, nonterm):
        return [r for r in forms if r[0] == nonterm]

    def _makeReplacementForms(self, formsToRemove, startingNonterm):
        forms = []
        for formToReplace in formsToRemove:
            for statingNontermForm in self._getForms(startingNonterm):
                newForm = statingNontermForm + formToReplace[1:]
                forms.append(newForm)
                self.substitutions[newForm] = (formToReplace, statingNontermForm, startingNonterm)
        return forms

    def _removeRules(self, nt, forms):
        for f in forms:
            self._removeRule(nt, f)

    def _addRules(self, nt, forms):
        for f in forms:
            self._addRule(nt, f)

    def _getDirectLeftRecursion(self, nt):
        return [r for r in self.grammarCopy.getForms(nt) if r[0] == nt]

    def _getRulesFromOriginal(self, nt, startRule):
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
        return rhs in self.grammar.getForms(lhs)

    def _getForms(self, lhs):
        return self.grammarCopy.getForms(lhs)

    def _getNonterminals(self):
        return self.grammar.getNonterminalList()

    def _removeRule(self, nt, form):
        self.grammarCopy.removeRule(nt, form)

    def _addRule(self, nt, form):
        self.grammarCopy.addRule(nt, form)
