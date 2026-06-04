from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..lines import Line

if TYPE_CHECKING:
    from ..spec.lexical.TokenRule import TokenRule
    from ..spec.lexical.SkipRule import SkipRule


@dataclass
class BlockOpened:
    rule: TokenRule | SkipRule
    lexeme: str
    line: Line
    column: int
    attempts: list = field(default_factory=list, compare=False)

    @property
    def name(self) -> str:
        return self.rule.name

    @property
    def pattern(self) -> str:
        return self.rule.pattern
