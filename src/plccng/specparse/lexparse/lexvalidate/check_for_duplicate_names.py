from dataclasses import dataclass

from plccng.specparse.ValidationError import ValidationError

from ..LexicalRule import LexicalRule


def check_for_duplicate_names(rulesOrLines):
    errors = []
    seen = set()
    for thing in rulesOrLines:
        if isinstance(thing, LexicalRule):
            if thing.name in seen:
                errors.append(DuplicateName(thing))
            else:
                seen.add(thing.name)
    return errors


@dataclass
class DuplicateName(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Duplicate rule name found '{rule.name}' on line: {rule.line.number}"
