from __future__ import annotations
from typing import Protocol, TYPE_CHECKING

from ...lines import Line
from ...scan.Token import Token
from ...scan.Skip import Skip

if TYPE_CHECKING:
    from ...scan.BlockOpened import BlockOpened


class LexicalRule(Protocol):
    line: Line
    name: str
    pattern: str
    close_pattern: str | None
    isSkip: bool

    def make_match(self, match, line: Line, index: int) -> Token | Skip | BlockOpened: ...
    def make_block_result(self, lexeme: str, line: Line, column: int) -> Token | Skip: ...
