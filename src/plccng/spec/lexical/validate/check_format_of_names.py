import re
from dataclasses import dataclass

from ...ValidationError import ValidationError
from ..LexicalRule import LexicalRule


def check_format_of_names(rulesOrLines):
    pattern = re.compile(r'^[A-Z_][A-Z0-9_]*$')
    errors = []
    for thing in rulesOrLines:
        if isinstance(thing, LexicalRule) and not pattern.match(thing.name):
            errors.append(InvalidName(rule=thing))
    return errors


@dataclass
class InvalidName(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid name format for rule '{rule.name}' (Must be uppercase letters, numbers, and underscores, and cannot start with a number) on line: {rule.line.number}"
