from plccng.lineparse import Line
from .InvalidRule import InvalidRule


class UnrecognizedLineValidator():
    def check(self, line):
        if isinstance(line, Line):
            return InvalidRule(line)
