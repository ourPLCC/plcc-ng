from .check_ll1 import check_ll1
from .create_spec_grammar import create_spec_grammar

def validate_ll1(syntactic_spec):
    return LL1Validator(syntactic_spec).validate()

class LL1Validator:
    def __init__(self, syntactic_spec):
        self.syntacticSpec = syntactic_spec

    def validate(self):
        grammar = create_spec_grammar(self.syntacticSpec)
        return check_ll1(grammar)
