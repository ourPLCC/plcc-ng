from dataclasses import dataclass
from plccng.lineparse import Line
from .LexicalRule import LexicalRule


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule|Line]
