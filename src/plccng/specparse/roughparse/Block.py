from dataclasses import dataclass

from ..lineparse import Line


@dataclass
class Block:
    lines: list[Line]
