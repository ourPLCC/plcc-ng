from ....parse_spec.parse_syntactic_spec.structs import SyntacticSpec
from .Grammar import Grammar
from ..errors import ValidationError
from .build_spec_grammar import build_spec_grammar
from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets

def check_ll1(syntactic_spec: SyntacticSpec):
    grammar = build_spec_grammar(syntactic_spec)
    return LL1Checker(grammar).check()

class LL1Checker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = build_first_sets(self.grammar)
        self.followSets = build_follow_sets(self.grammar)
        self.errorList = []

    def check(self) -> list[ValidationError]:
        return self.errorList



