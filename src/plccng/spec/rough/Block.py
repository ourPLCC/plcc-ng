from dataclasses import dataclass

from ..lines import Line


@dataclass
class Block:
    lines: list[Line]
