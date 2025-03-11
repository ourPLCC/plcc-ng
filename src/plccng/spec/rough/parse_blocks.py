import re

from .. import lines
from .Block import Block
from .raise_handler import raise_handler
from .UnclosedBlockError import UnclosedBlockError


def parse_blocks(lines, handler=raise_handler):
    if lines is None:
        return []
    PPP = re.compile(r'^%%%(?:\s*#.*)?$')
    PPLC = re.compile(r'^%%{(?:\s*#.*)?$')
    PPRC = re.compile(r'^%%}(?:\s*#.*)?$')
    brackets = {
        PPP: PPP,
        PPLC: PPRC
    }
    return BlockParser(brackets, handler).parse(lines)


class BlockParser():
    def __init__(self, brackets, handler):
        self.brackets = brackets
        self.handler = handler
        self.closing = None

    def parse(self, lines):
        self.lines = iter(lines)
        for line in self.lines:
            if not self.isBlockStart(line):
                yield line
            else:
                yield from self.parseBlock(line)

    def isBlockStart(self, line):
        for b in self.brackets:
            if b.match(line.string):
                return True
        return False

    def parseBlock(self, line):
        blockLines = [line]
        self.setClosingFor(line)
        for line in self.lines:
            blockLines.append(line)
            if self.isClosing(line):
                yield Block(blockLines)
                return
        # No closing found.
        self.handler(UnclosedBlockError(line=line, column=len(blockLines[-1].string)+1, message='Start of block: {blockLines[0].file}:{blockLines[0].number}'))
        # Add a closing line to be consistent (since blocks contain their closing)
        closing = lines.Line(string='%%%', number=blockLines[-1].number+1, file=blockLines[-1].file)
        blockLines.append(closing)
        yield Block(blockLines)

    def setClosingFor(self, line):
        for b in self.brackets:
            if b.match(line.string):
                self.closing = self.brackets[b]
                return
        else:       # pragma: no cover
            pass    # self.brackets is never empty

    def isClosing(self, line):
        return self.closing.match(line.string) is not None
