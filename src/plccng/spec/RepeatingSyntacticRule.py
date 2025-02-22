from plccng.spec.SyntacticRule import SyntacticRule
from plccng.spec.Terminal import Terminal


from dataclasses import dataclass


@dataclass(frozen=True)
class RepeatingSyntacticRule(SyntacticRule):
    separator: Terminal | None = None
    pass
