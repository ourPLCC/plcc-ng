from plccng.ValidationError import ValidationError
from dataclasses import dataclass
from ..LexicalRule import LexicalRule


@dataclass
class InvalidPattern(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid pattern format found '{rule.pattern}' on line: {rule.line.number} (Patterns can not contain closing closing quotes)"


class PatternValidator():
    def validate(self, rule):
        if isinstance(rule, LexicalRule):
            if "\'" in rule.pattern or "\"" in rule.pattern or rule.pattern == '':
                return InvalidPattern(rule=rule)
