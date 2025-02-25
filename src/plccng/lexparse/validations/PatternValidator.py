from ..LexicalRule import LexicalRule
from .InvalidRulePattern import InvalidRulePattern


class PatternValidator():
    def check(self, rule):
        if isinstance(rule, LexicalRule):
            if "\'" in rule.pattern or "\"" in rule.pattern or rule.pattern == '':
                return InvalidRulePattern(rule=rule)
