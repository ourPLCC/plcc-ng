from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class InvalidRuleError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Invalid rule format found on line: {line.number}"
