from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class DuplicateLhsError(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message=f"Duplicate lhs name: '{rule.line.string}' on line: {rule.line.number}"
        )
