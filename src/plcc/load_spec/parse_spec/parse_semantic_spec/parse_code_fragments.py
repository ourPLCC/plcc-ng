
from plcc.load_spec.structs import CodeFragment
from .parse_target_locator import parse_target_locator
from plcc.load_spec.structs import Line
from plcc.load_spec.structs import Block
from plcc.load_spec.structs import Divider
import re

def parse_code_fragments(lines_and_blocks: list[Line | Block]):
    parser = CodeFragmentParser(lines_and_blocks)
    return parser.parse()

class CodeFragmentParser:
    def __init__(self, lines_and_blocks: list[Line | Block]):
        self.lines_and_blocks = lines_and_blocks
        self.codeFragmentList = []
        self.targetLocator = None

    def parse(self):
        for obj in self.lines_and_blocks:
            self._parse_line_or_block(obj)

        if self.targetLocator != None:
            raise CodeFragmentMissingBlockError(self.targetLocator.line)

        return self.codeFragmentList

    def _parse_line_or_block(self, obj):
        handler = {
                Line: self._parse_line,
                Block: self._parse_block
            }.get(type(obj))

        handler(obj)


    def _parse_block(self, block):
        if self.targetLocator == None:
            raise UndefinedTargetLocatorError(block.lines[0])

        self.codeFragmentList.append(CodeFragment(targetLocator=self.targetLocator, block=block))
        self.targetLocator = None

    def _parse_line(self, line):
        if self._isCommentOrBlank(line.string):
                return

        if self.targetLocator != None:
            raise DuplicateTargetLocatorError(line.string)
        else:
            self.targetLocator = parse_target_locator(line)


    def _isCommentOrBlank(self, obj_str):
        return True if re.match(r'\s*#', obj_str) or re.match(r'\s*$', obj_str) else False


class CodeFragmentMissingBlockError(Exception):
    def __init__(self, line):
        self.line = line

class UndefinedTargetLocatorError(Exception):
    def __init__(self, line):
        self.line = line

class DuplicateTargetLocatorError(Exception):
    def __init__(self, line):
        self.line = line
