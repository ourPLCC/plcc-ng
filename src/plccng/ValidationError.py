from plccng.lineparse.Line import Line


from dataclasses import dataclass


@dataclass
class ValidationError:
    line: Line
    message: str
