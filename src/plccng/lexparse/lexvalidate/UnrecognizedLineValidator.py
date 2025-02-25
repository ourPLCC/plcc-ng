from plccng.ValidationError import ValidationError
from dataclasses import dataclass
from plccng.lineparse import Line


@dataclass
class UnrecognizedLine(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Invalid rule format found on line: {line.number}"


class UnrecognizedLineValidator():
    def check(self, line):
        if isinstance(line, Line):
            return UnrecognizedLine(line)
