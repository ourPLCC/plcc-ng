from dataclasses import dataclass, field

from .SyntacticRule import SyntacticRule


@dataclass
class SyntacticSpec:
    rules: list[SyntacticRule] = field(default_factory=list)

    def __iter__(self):
        return iter(self.rules) if self.rules is not None else iter([])

    def copy(self):
        return SyntacticSpec(self.rules.copy())

    def __len__(self):
        return len(self.rules) if self.rules is not None else 0

    def pop(self, i=-1):
        return self.rules.pop(i)

    def append(self, rule):
        self.rules.append(rule)

    def __getitem__(self, i):
        return self.rules[i]
