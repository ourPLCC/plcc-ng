from dataclasses import dataclass

from ...lines import Line


@dataclass(frozen=True)
class Include:
    file: str
    line: Line
