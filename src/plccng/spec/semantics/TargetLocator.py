from dataclasses import dataclass

from ...lines import Line


@dataclass
class TargetLocator:
    line: Line
    className: str
    modifier: str = None
