from plccng.lineparse import Line


from dataclasses import dataclass


@dataclass
class Block:
    lines: list[Line]
