from plccng.ValidationError import ValidationError


from dataclasses import dataclass


@dataclass
class UndefinedBlockError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Undefined Block for {self.line.string} on line: {self.line.number}"
