from dataclasses import dataclass
import re

from plccng.ValidationError import ValidationError
from ..LexicalRule import LexicalRule


@dataclass
class InvalidName(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid name format for rule '{rule.name}' (Must be uppercase letters, numbers, and underscores, and cannot start with a number) on line: {rule.line.number}"


class NameValidator():
    pattern = re.compile(r'^[A-Z_][A-Z0-9_]*$')

    def validate(self, rule):
        if isinstance(rule, LexicalRule) and not self.pattern.match(rule.name):
            return InvalidName(rule=rule)
