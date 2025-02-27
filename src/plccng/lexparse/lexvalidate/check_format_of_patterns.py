from plccng.ValidationError import ValidationError
from dataclasses import dataclass
from ..LexicalRule import LexicalRule


def check_format_of_patterns(rulesOrLines):
    errors = []
    for thing in rulesOrLines:
        if isinstance(thing, LexicalRule):
            if "\'" in thing.pattern or "\"" in thing.pattern or thing.pattern == '':
                errors.append(InvalidPattern(rule=thing))
    return errors


@dataclass
class InvalidPattern(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid pattern format found '{rule.pattern}' on line: {rule.line.number} (Patterns can not contain closing closing quotes)"
