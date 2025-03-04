from dataclasses import dataclass

from plccng.specparse.ValidationError import ValidationError


@dataclass
class UndefinedTargetLocatorError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Undefined class name on line: {self.line.number}"
