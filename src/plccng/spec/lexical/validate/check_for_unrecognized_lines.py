from dataclasses import dataclass

from ...lines import Line
from ...ValidationError import ValidationError


def check_for_unrecognized_lines(rulesOrLines):
    errors = []
    for thing in rulesOrLines:
        if isinstance(thing, Line):
            errors.append(UnrecognizedLine(thing))
    return errors


@dataclass
class UnrecognizedLine(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Invalid rule format found on line: {line.number}"
