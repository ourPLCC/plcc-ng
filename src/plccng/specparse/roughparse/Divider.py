from dataclasses import dataclass

from ..lineparse import Line


@dataclass
class Divider:
    tool: str
    language: str
    line: Line
