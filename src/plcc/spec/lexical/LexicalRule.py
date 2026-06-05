from __future__ import annotations
from typing import Protocol

from ...lines import Line
from ...scan.Token import Token
from ...scan.Skip import Skip


class LexicalRule(Protocol):
    line: Line | None
    name: str
    pattern: str
    isSkip: bool

    def make_match(self, match, line: Line, index: int) -> Token | Skip: ...
