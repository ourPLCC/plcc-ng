import re
from ...structs import LexicalRule, LexicalSpec
from ...parse_rough import parse_rough


def from_string(string, file=None, startLineNumber=1):
    rough = parse_rough.from_string(string, file=file, startLineNumber=startLineNumber)
    return from_lines(rough)


def from_lines(lines):
    return LexicalParser().parse(lines)


class LexicalParser():
    def __init__(self):
        self.lines = None
        self.pattern = re.compile(r'^\s*(?:(?P<Type>(skip|token))\s+)?(?P<Name>\S+)\s+(?P<Pattern>((\'[^\']*\')|("[^"]*")))\s*(?:#.*)*$')
        self.rules = []

    def parse(self, lines):
        self.lines = lines
        if not self.lines:
            return LexicalSpec(self.rules)
        for line in self.lines:
            if self._isBlankOrComment(line):
                continue
            result = self._parseLine(line)
            self.rules.append(result)
        return LexicalSpec(self.rules)

    def _isBlankOrComment(self, line):
        return not line.string.strip() or line.string.strip().startswith("#")

    def _parseLine(self, line):
        m = self.pattern.match(line.string)
        if m:
            name = m['Name']
            pattern = m['Pattern']
            isSkip = (m['Type'] == 'skip')
            return self._makeRule(line, name, pattern, isSkip)
        return line

    def _makeRule(self, line, name, pattern, isSkip):
        pattern = self._stripQuotes(pattern)
        newSkipRule = LexicalRule(line=line, isSkip=isSkip, name=name, pattern=pattern)
        return newSkipRule

    def _stripQuotes(self, pattern):
        pattern = pattern.strip('\'')
        pattern = pattern.strip('\"')
        return pattern
