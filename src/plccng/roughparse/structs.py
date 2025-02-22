from plccng import lineparse
from dataclasses import dataclass


@dataclass
class Block:
    lines: list[lineparse.Line]


@dataclass
class Divider:
    tool: str
    language: str
    line: lineparse.Line


@dataclass(frozen=True)
class Include:
    file: str
    line: lineparse.Line


class CircularIncludeError(Exception):
    def __init__(self, line):
        self.line = line


class UnclosedBlockError(Exception):
    def __init__(self, line):
        self.line = line
