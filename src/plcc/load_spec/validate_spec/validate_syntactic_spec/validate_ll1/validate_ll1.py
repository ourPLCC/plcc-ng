from .check_ll1 import check_ll1
from ..replace_repeating_with_standard_rules import replace_repeating_with_standard_rules

def validate_ll1(syntactic_spec):
    return LL1Validator(syntactic_spec).validate()

class LL1Validator:
    def __init__(self, syntactic_spec):
        self.syntacticSpec = replace_repeating_with_standard_rules(syntactic_spec)

    def validate(self):
        return check_ll1(self.syntacticSpec)
