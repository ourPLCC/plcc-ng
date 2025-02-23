from plccng.lineparse.Line import Line


from dataclasses import dataclass


@dataclass
class TargetLocator:
    line: Line
    className: str
    modifier: str = None
