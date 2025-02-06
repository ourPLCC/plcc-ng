from plccng.load_spec.structs import (
    CapturingTerminal,
    Terminal,
    RepeatingSyntacticRule,
    SyntacticSpec,
    LexicalSpec
)
from plccng.load_spec.errors import UndefinedTerminalError

def validate_terminals_defined(syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec):
    return TerminalsDefinedValidator(syntacticSpec, lexicalSpec).validate()

class TerminalsDefinedValidator:
    def __init__(self, syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec):
        self.syntacticSpec = syntacticSpec
        self.lexicalSpec = lexicalSpec
        self.definedTerminals = None
        self.errorList = []

    def validate(self):
        for rule in self.syntacticSpec:
            if isinstance(rule, RepeatingSyntacticRule) and rule.separator:
                self._validateSeparatorIsDefined(rule)
            self._validateTerminalsDefined(rule)
        return self.errorList

    def _validateTerminalsDefined(self, rule):
        for sym in rule.rhsSymbolList:
            if self._isTerminal(sym) and self._isUndefined(sym):
                self.errorList.append(UndefinedTerminalError(rule))

    def _validateSeparatorIsDefined(self, rule):
        if self._isTerminal(rule.separator) and self._isUndefined(rule.separator):
            self.errorList.append(UndefinedTerminalError(rule))

    def _isTerminal(self, sym):
        return isinstance(sym, (Terminal, CapturingTerminal))

    def _isUndefined(self, sym):
        if self.definedTerminals is None:
            self.definedTerminals = self._getDefinedTerminals(self.lexicalSpec)
        return sym.name not in self.definedTerminals

    def _getDefinedTerminals(self, lexicalSpec):
        if not lexicalSpec:
            return set()
        return {rule.name for rule in lexicalSpec.ruleList}
