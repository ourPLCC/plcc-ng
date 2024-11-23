from .Grammar import Grammar
from ..errors import ValidationError
from .FirstSets import generate_first_sets
from .FollowSets import generate_follow_sets

def check(grammar: Grammar):
    return LL1Checker(grammar).check()

class LL1Checker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.firstSets = generate_first_sets(grammar)
        self.followSets = generate_follow_sets(grammar, self.firstSets)
        self.errorList = []

    def check(self) -> list[ValidationError]:
        return self.errorList



