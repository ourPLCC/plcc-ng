from .SyntacticRule import SyntacticRule


from dataclasses import dataclass


@dataclass(frozen=True)
class StandardSyntacticRule(SyntacticRule):
    pass
