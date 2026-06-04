from dataclasses import dataclass

from .LexicalRule import LexicalRule


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule]

    def __len__(self):
        return len(self.ruleList)
