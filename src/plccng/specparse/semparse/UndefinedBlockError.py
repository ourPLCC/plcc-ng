from dataclasses import dataclass

from plccng.specparse.ValidationError import ValidationError


@dataclass
class UndefinedBlockError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Undefined Block for {self.line.string} on line: {self.line.number}"
