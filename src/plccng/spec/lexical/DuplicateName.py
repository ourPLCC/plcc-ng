from .LexicalSpecError import LexicalSpecError


class DuplicateName(LexicalSpecError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Duplicate rule name found '{rule.name}' on line: {rule.line.number}"
