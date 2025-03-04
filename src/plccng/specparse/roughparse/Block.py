from dataclasses import dataclass

from plccng.lineparse import Line


@dataclass
class Block:
    lines: list[Line]
