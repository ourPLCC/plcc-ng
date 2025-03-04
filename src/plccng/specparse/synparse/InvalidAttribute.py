from dataclasses import dataclass

from ..ValidationError import ValidationError


@dataclass
class InvalidAttribute(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message = f"Invalid RHS alternate name format for rule: '{rule.line.string}' (must start with a lower case letter, and may contain upper or lower case letters, numbers, and underscore. on line: {rule.line.number}"
        )
