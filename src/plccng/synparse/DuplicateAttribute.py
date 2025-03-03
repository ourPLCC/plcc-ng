from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class DuplicateAttribute(ValidationError):
    def __init__(self, rule, symbolName):
        super().__init__(
            line=rule.line,
            message=f"Duplicate RHS symbol name: '{symbolName}', for rule: '{rule.line.string}', on line: {rule.line.number}. All RHS symbols must have unique names."
        )
