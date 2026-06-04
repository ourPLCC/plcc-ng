from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...lines import Line
from ...scan.Token import Token

if TYPE_CHECKING:
    from ...scan.BlockOpened import BlockOpened


@dataclass
class TokenRule:
    line: Line
    name: str
    pattern: str
    close_pattern: str | None = None
    isSkip: bool = field(init=False, default=False, compare=False, repr=False)

    def make_match(self, match: re.Match[str], line, index) -> Token | BlockOpened:
        if self.close_pattern is not None:
            from ...scan.BlockOpened import BlockOpened
            return BlockOpened(
                rule=self, lexeme=match.group(), line=line, column=1 + index,
            )
        return Token(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )

    def make_block_result(self, lexeme: str, line: Line, column: int) -> Token:
        return Token(lexeme=lexeme, name=self.name, line=line, column=column, pattern=self.pattern)
