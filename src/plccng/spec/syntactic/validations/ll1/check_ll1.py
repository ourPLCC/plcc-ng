from .Grammar import Grammar
from .....ValidationError import ValidationError
from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets
from .build_parsing_table import build_parsing_table
from .check_parsing_table_for_ll1 import check_parsing_table_for_ll1


def check_ll1(grammar: Grammar) -> list[ValidationError]:
    return LL1Checker(grammar).check()


class LL1Checker:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar

    def check(self) -> list[ValidationError]:
        # TODO: Check for left recursion (direct or indirect)
        # TODO: Check for non-left-refactored rules
        errors = self._checkll1()
        return errors

    def _checkll1(self):
        firsts = build_first_sets(self.grammar)
        follows = build_follow_sets(self.grammar, firsts)
        table = build_parsing_table(firsts, follows, self.grammar)
        errors = check_parsing_table_for_ll1(table)
        return errors
