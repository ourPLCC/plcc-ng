from dataclasses import dataclass

from .lines import Line


@dataclass
class ValidationError:
    line: Line
    message: str
