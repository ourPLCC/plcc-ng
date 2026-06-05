from __future__ import annotations
import re
from dataclasses import dataclass, field

from ...lines import Line
from ...scan.Skip import Skip


@dataclass
class SkipRule:
    line: Line | None
    name: str
    pattern: str
    isSkip: bool = field(init=False, default=True, compare=False, repr=False)

    def make_match(self, match: re.Match[str], line, index) -> Skip:
        return Skip(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )
