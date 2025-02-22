from dataclasses import dataclass
from plccng.ValidationError import ValidationError


@dataclass
class InvalidPatternError(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid pattern format found '{rule.pattern}' on line: {rule.line.number} (Patterns can not contain closing closing quotes)"
