from plccng.lineparse import Line


from dataclasses import dataclass


@dataclass
class LexError:
    line: Line
    column: int
