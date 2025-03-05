from dataclasses import dataclass

from .SyntacticRule import SyntacticRule
from .Terminal import Terminal


@dataclass(frozen=True)
class RepeatingSyntacticRule(SyntacticRule):
    separator: Terminal | None = None
    pass
