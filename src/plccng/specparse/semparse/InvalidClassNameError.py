from dataclasses import dataclass

from plccng.specparse.ValidationError import ValidationError


@dataclass
class InvalidClassNameError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Invalid name format for ClassName {self.line.string} on line: {self.line.number} (Must start with an upper case letter, and may contain upper or lower case letters, numbers, and underscores)."
