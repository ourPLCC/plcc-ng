from dataclasses import dataclass

from ..ValidationError import ValidationError


@dataclass
class DuplicateAttribute(ValidationError):
    def __init__(self, rule, symbolName):
        super().__init__(
            line=rule.line,
            message=f"Duplicate RHS symbol name: '{symbolName}', for rule: '{rule.line.string}', on line: {rule.line.number}. All RHS symbols must have unique names."
        )
