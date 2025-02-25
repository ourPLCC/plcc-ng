from ..LexicalRule import LexicalRule
from .DuplicateRuleName import DuplicateRuleName


class UniqueRuleNameValidator:
    def __init__(self):
        self.seen = set()

    def check(self, rule):
        if isinstance(rule, LexicalRule):
            if rule.name in self.seen:
                return DuplicateRuleName(rule)
            else:
                self.seen.add(rule.name)
