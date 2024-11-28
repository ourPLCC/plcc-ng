from ....parse_spec.parse_syntactic_spec.structs import SyntacticSpec
from .Grammar import Grammar
from ..errors import ValidationError
from .create_spec_grammar import create_spec_grammar
from .generate_first_sets import generate_first_sets
from .generate_follow_sets import generate_follow_sets

def check_ll1(syntactic_spec: SyntacticSpec):
    grammar = create_spec_grammar(syntactic_spec)
    return LL1Checker(grammar).check()

class LL1Checker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = generate_first_sets(self.grammar)
        self.followSets = generate_follow_sets(self.grammar)
        self.errorList = []

    def check(self) -> list[ValidationError]:
        return self.errorList



