from .SyntacticRule import SyntacticRule
from .Terminal import Terminal


from dataclasses import dataclass


@dataclass(frozen=True)
class RepeatingSyntacticRule(SyntacticRule):
    separator: Terminal | None = None
    pass
