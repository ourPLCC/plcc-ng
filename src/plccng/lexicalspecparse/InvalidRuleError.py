from dataclasses import dataclass
from plccng.ValidationError import ValidationError


@dataclass
class InvalidRuleError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Invalid rule format found on line: {line.number}"
