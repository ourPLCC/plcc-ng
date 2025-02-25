from dataclasses import dataclass
from plccng.ValidationError import ValidationError


@dataclass
class InvalidRuleName(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid name format for rule '{rule.name}' (Must be uppercase letters, numbers, and underscores, and cannot start with a number) on line: {rule.line.number}"
