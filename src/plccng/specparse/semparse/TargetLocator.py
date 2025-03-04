from dataclasses import dataclass

from ..lineparse.Line import Line


@dataclass
class TargetLocator:
    line: Line
    className: str
    modifier: str = None
