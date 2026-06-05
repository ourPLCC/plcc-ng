import re

from .BlockOpened import BlockOpened
from .LexError import LexError
from .UnclosedBlockError import UnclosedBlockError


class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if lines is None:
            return
        it = iter(lines)
        for line in it:
            yield from self._scanLine(line, it)

    def _scanLine(self, line, it, start=0):
        index = start
        while index < len(line.string):
            result = self.matcher.match(line, index)
            if isinstance(result, BlockOpened):
                open_end = index + len(result.lexeme)
                yield from self._scanBlock(result, line, open_end, it)
                return
            elif isinstance(result, LexError):
                yield result
                index += 1
            else:
                index += len(result.lexeme)
                yield result

    def _scanBlock(self, opened, line, start, it):
        close_re = re.compile(opened.rule.close_pattern)
        # Check for close on the opening line (same-line case).
        m = close_re.search(line.string, start)
        if m:
            lexeme = line.string[start:m.start()]
            yield opened.rule.make_block_result(lexeme, opened.line, opened.column)
            yield from self._scanLine(line, it, start=m.end())
            return
        # Close not on opening line — buffer and consume subsequent lines.
        buffer = line.string[start:]
        for next_line in it:
            m = close_re.search(next_line.string)
            if m:
                buffer += next_line.string[:m.start()]
                yield opened.rule.make_block_result(buffer, opened.line, opened.column)
                yield from self._scanLine(next_line, it, start=m.end())
                return
            buffer += next_line.string
        # Iterator exhausted without finding close.
        yield UnclosedBlockError(line=opened.line, column=opened.column, rule=opened.rule)
