from dataclasses import dataclass

from ..lines import Line


@dataclass
class LexError:
    line: Line
    column: int

    def __str__(self):
        return f"""{self.line.file}:{self.line.number}:{self.column}:{self.__class__.__name__} '{self.line.string[self.column-1]}'"""
