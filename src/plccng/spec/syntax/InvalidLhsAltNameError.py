from dataclasses import dataclass

from ..ValidationError import ValidationError


@dataclass
class InvalidLhsAltNameError(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message=f"Invalid LHS alternate name format for rule: '{rule.line.string}' (must start with a upper-case letter, and may contain upper or lower case letters, numbers and/or underscore) on line: {rule.line.number}"
        )
