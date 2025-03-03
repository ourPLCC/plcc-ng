from plccng.ValidationError import ValidationError
from dataclasses import dataclass
from ..LexicalRule import LexicalRule
import re


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
