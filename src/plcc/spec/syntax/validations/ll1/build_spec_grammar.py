from ...CapturingTerminal import CapturingTerminal
from ...InvalidSymbolException import InvalidSymbolException
from ...InvalidSyntacticSpecException import InvalidSyntacticSpecException
from ...NonTerminal import NonTerminal
from ...Symbol import Symbol
from ...SyntacticRule import SyntacticRule
from ...SyntacticSpec import SyntacticSpec
from ...Terminal import Terminal
from .Grammar import Grammar
from .LL1Wrapper import LL1Wrapper, wrap_ll1


def build_spec_grammar(syntactic_spec: SyntacticSpec):
    return SpecGrammar(syntactic_spec)

class SpecGrammar(Grammar):
    def __init__(self, syntacticSpec: SyntacticSpec):
        super().__init__()
        self.epsilon = wrap_ll1("", None)
        self.eof = wrap_ll1(chr(26), None)
        self.rules = {}
        self.nonterminals = set()
        self.terminals = set()
        self.startSymbol = None
        self._processSyntacticSpec(syntacticSpec)

    def _processSyntacticSpec(self, syntacticSpec: SyntacticSpec) -> None:
        self._validateSyntacticSpec(syntacticSpec)
        for rule in syntacticSpec:
            self._processRule(rule)

    def _validateSyntacticSpec(self, syntacticSpec: SyntacticSpec) -> None:
        if not isinstance(syntacticSpec, SyntacticSpec):
            raise InvalidSyntacticSpecException(str(syntacticSpec))

    def _processRule(self, rule: SyntacticRule) -> None:
        nonterminal = wrap_ll1(rule.lhs.name, rule.lhs)
        if len(rule.rhsSymbolList) == 0:
            rhsWrappers = [self.getEpsilon()]
        else:
            rhsWrappers = [self._wrapSymbol(sym) for sym in rule.rhsSymbolList]
        self.addRule(nonterminal, rhsWrappers)
        self._updateStartSymbol(nonterminal)

    def _wrapSymbol(self, sym: Terminal | NonTerminal) -> LL1Wrapper:
        return wrap_ll1(sym.name, sym)

    def addRule(self, nonterminal: LL1Wrapper, form: list[LL1Wrapper]) -> None:
        nonterminal = self._checkWrapped(nonterminal)
        wrappedForm = [self._checkWrapped(sym) for sym in form]
        self._addRuleList(nonterminal, wrappedForm)
        self._updateNonterminalsAndTerminals(nonterminal, wrappedForm)

    def _addRuleList(self, nonterminal: LL1Wrapper, wrappedForm: list[LL1Wrapper]) -> None:
        if nonterminal.name not in self.rules:
            self.rules[nonterminal.name] = []
        self.rules[nonterminal.name].append(wrappedForm)

    def _checkWrapped(self, sym: object) -> LL1Wrapper:
        if isinstance(sym, LL1Wrapper):
            return sym
        elif isinstance(sym, Symbol):
            return self._wrapSymbol(sym)
        else:
            raise InvalidSymbolException(str(sym))

    def _updateNonterminalsAndTerminals(self, nonterminal: LL1Wrapper, form: list[LL1Wrapper]) -> None:
        self.nonterminals.add(nonterminal)
        for sym in form:
            if self.isTerminal(sym.specObject) or self.isCapturingTerminal(sym.specObject):
                self.terminals.add(sym)
            elif self.isNonterminal(sym.specObject):
                self.nonterminals.add(sym)

    def _updateStartSymbol(self, nonterminal: LL1Wrapper) -> None:
        if self.startSymbol is None:
            self.startSymbol = nonterminal.name

    def isTerminal(self, object: object) -> bool:
        return isinstance(object, Terminal)

    def isCapturingTerminal(self, object: object) -> bool:
        return isinstance(object, CapturingTerminal)

    def isNonterminal(self, object: object) -> bool:
        return isinstance(object, NonTerminal)

    def getRules(self) -> dict[LL1Wrapper, list[list[LL1Wrapper]]]:
        return self.rules

    def getStartSymbol(self) -> LL1Wrapper:
        return self.startSymbol

    def getNonterminalSet(self) -> set[LL1Wrapper]:
        return self.nonterminals

    def getTerminals(self) -> set[LL1Wrapper]:
        return self.terminals

    def getEpsilon(self) -> LL1Wrapper:
        return self.epsilon

    def getEOF(self) -> LL1Wrapper:
        return self.eof
