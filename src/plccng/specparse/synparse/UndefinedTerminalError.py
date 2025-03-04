from dataclasses import dataclass

from ..ValidationError import ValidationError


@dataclass
class UndefinedTerminalError(ValidationError):
    def __init__(self, rule):
        super().__init__(
            line=rule.line,
            message=f"Undefined terminal for rule: '{rule.line.string}' on line: {rule.line.number}. All terminals must be defined in the lexical section of the grammar file."
        )
