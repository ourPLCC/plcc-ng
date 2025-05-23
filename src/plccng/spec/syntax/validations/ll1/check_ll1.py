from ....ValidationError import ValidationError

from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets
from .build_parsing_table import build_parsing_table
from .check_parsing_table_for_ll1 import check_parsing_table_for_ll1
from .check_left_recursion import check_left_recursion
from .Grammar import Grammar


def check_ll1(grammar: Grammar) -> list[ValidationError]:
    return LL1Checker(grammar).check()


class LL1Checker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar

    def check(self) -> list[ValidationError]:
        errors = check_left_recursion(self.grammar)
        if errors:
            return errors
        errors = self._checkll1()
        return errors

    def _checkll1(self):
        firsts = build_first_sets(self.grammar)
        follows = build_follow_sets(self.grammar, firsts)
        table = build_parsing_table(firsts, follows, self.grammar)
        errors = check_parsing_table_for_ll1(table)
        return errors
