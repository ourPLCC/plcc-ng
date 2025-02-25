from plccng.ValidationError import ValidationError
from dataclasses import dataclass
from ..LexicalRule import LexicalRule


@dataclass
class DuplicateName(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Duplicate rule name found '{rule.name}' on line: {rule.line.number}"


class UniqueNameValidator:
    def __init__(self):
        self.seen = set()

    def validate(self, rule):
        if isinstance(rule, LexicalRule):
            if rule.name in self.seen:
                return DuplicateName(rule)
            else:
                self.seen.add(rule.name)
