from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class InvalidTerminal(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message=f"Invalid RHS alternate name format for rule: '{rule.line.string}' (upper-case letters, numbers, and underscore and cannot start with a number. on line: {rule.line.number}"
        )
