from plccng.lineparse import Line


from dataclasses import dataclass


@dataclass
class Divider:
    tool: str
    language: str
    line: Line
