from dataclasses import dataclass

from ..lines.Line import Line


@dataclass
class TargetLocator:
    line: Line
    className: str
    modifier: str = None
