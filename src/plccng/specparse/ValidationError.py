from dataclasses import dataclass

from plccng.lineparse import Line


@dataclass
class ValidationError:
    line: Line
    message: str
