import re
from dataclasses import dataclass

from plccng.specparse.ValidationError import ValidationError

from ..LexicalRule import LexicalRule


def check_format_of_patterns(rulesOrLines):
    errors = []
    for thing in rulesOrLines:
        if isinstance(thing, LexicalRule):
            try:
                re.compile(thing.pattern)
            except re.PatternError as e:
                errors.append(InvalidPattern(rule=thing, error=e))
    return errors


@dataclass
class InvalidPattern(ValidationError):
    def __init__(self, rule, error):
        self.line = rule.line
        self.message = f"Could not compile pattern: {rule.pattern}\nCaused by {error}"
