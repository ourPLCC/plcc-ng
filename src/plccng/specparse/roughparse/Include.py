from dataclasses import dataclass

from ..lineparse import Line


@dataclass(frozen=True)
class Include:
    file: str
    line: Line
