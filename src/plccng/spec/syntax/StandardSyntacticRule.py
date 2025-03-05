from dataclasses import dataclass

from .SyntacticRule import SyntacticRule


@dataclass(frozen=True)
class StandardSyntacticRule(SyntacticRule):
    pass
