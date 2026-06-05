from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...lines import Line
from ...scan.Skip import Skip

if TYPE_CHECKING:
    from ...scan.BlockOpened import BlockOpened


@dataclass
class SkipRule:
    line: Line | None
    name: str
    pattern: str
    close_pattern: str | None = None
    isSkip: bool = field(init=False, default=True, compare=False, repr=False)

    def make_match(self, match: re.Match[str], line, index) -> Skip | BlockOpened:
        if self.close_pattern is not None:
            from ...scan.BlockOpened import BlockOpened
            return BlockOpened(
                rule=self, lexeme=match.group(), line=line, column=1 + index,
            )
        return Skip(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )

    def make_block_result(self, lexeme: str, line: Line, column: int) -> Skip:
        return Skip(lexeme=lexeme, name=self.name, line=line, column=column, pattern=self.pattern)
