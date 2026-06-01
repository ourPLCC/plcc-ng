from dataclasses import dataclass

from ...lines import Line


@dataclass
class Divider:
    tool: str
    language: str
    line: Line
