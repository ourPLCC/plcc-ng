import re
from ..LexicalRule import LexicalRule
from .InvalidRuleName import InvalidRuleName


class RuleNameValidator():
    pattern = re.compile(r'^[A-Z_][A-Z0-9_]*$')

    def check(self, rule):
        if isinstance(rule, LexicalRule) and not self.pattern.match(rule.name):
            return InvalidRuleName(rule=rule)
