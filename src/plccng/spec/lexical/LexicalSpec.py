from dataclasses import dataclass

from ...lines import Line
from .LexicalRule import LexicalRule


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule|Line]

    def __len__(self):
        return len(self.ruleList)
