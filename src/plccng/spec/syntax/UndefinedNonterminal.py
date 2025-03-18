from dataclasses import dataclass

from ..ValidationError import ValidationError


@dataclass
class UndefinedNonterminal(ValidationError):
    def __init__(self, rule):
        super().__init__(
        line=rule.line,
        message = f"RHS Non-Terminal found that does not exist anywhere in LHS in rule: '{rule.line.string}' on line: {rule.line.number}"
        )
