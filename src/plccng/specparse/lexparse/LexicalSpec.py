from dataclasses import dataclass

from ..lineparse import Line
from .LexicalRule import LexicalRule


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule|Line]
