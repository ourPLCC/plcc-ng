from __future__ import annotations
import re
from dataclasses import dataclass, field

from ...lines import Line
from ...scan.Token import Token


@dataclass
class TokenRule:
    line: Line | None
    name: str
    pattern: str
    isSkip: bool = field(init=False, default=False, compare=False, repr=False)

    def make_match(self, match: re.Match[str], line, index) -> Token:
        return Token(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )
