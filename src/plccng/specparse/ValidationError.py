from dataclasses import dataclass

from .lineparse import Line


@dataclass
class ValidationError:
    line: Line
    message: str
