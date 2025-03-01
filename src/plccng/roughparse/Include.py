from plccng.lineparse import Line


from dataclasses import dataclass


@dataclass(frozen=True)
class Include:
    file: str
    line: Line
