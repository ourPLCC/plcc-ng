from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class InvalidSeparator(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message=f"Invalid RHS separator, must be terminal: '{rule.line.string}'"
        )
