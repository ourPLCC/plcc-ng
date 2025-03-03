from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class InvalidLhsNameError(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message=f"Invalid LHS name format for rule: '{rule.line.string}' (must start with a lower-case letter, and may contain upper or lower case letters, numbers and/or underscore) on line: {rule.line.number}"
        )
