from dataclasses import dataclass

from plccng.lineparse import Line


@dataclass
class Divider:
    tool: str
    language: str
    line: Line
