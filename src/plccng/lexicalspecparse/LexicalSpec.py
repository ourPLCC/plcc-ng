from dataclasses import dataclass
from plccng.lineparse.Line import Line
from .LexicalRule import LexicalRule


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule|Line]
