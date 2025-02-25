from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class UndefinedTargetLocatorError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Undefined class name on line: {self.line.number}"
