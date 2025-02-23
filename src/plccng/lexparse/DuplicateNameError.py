from dataclasses import dataclass
from plccng.ValidationError import ValidationError


@dataclass
class DuplicateNameError(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Duplicate rule name found '{rule.name}' on line: {rule.line.number}"
