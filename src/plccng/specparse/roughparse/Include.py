from dataclasses import dataclass

from plccng.lineparse import Line


@dataclass(frozen=True)
class Include:
    file: str
    line: Line
