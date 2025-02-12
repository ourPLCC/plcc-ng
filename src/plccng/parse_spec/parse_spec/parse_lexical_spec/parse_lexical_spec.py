import re
from re import Match

from plccng.parse_spec.structs import LexicalRule, LexicalSpec, Line
from ...parse_rough import parse_rough


def from_string(string, file=None, startLineNumber=1):
    rough = parse_rough.from_string(string, file=file, startLineNumber=startLineNumber)
    return from_lines(rough)


def from_lines(lines):
    return LexicalParser().parse(lines)


class LexicalParser():
    def __init__(self):
        self.lines = None
        self.patterns = {
            'skipToken' : re.compile(r'^\s*skip\s+(?P<Name>\S+)\s+(?P<Pattern>((\'\S+\')|(\"\S+\")))\s*(?:#.*)*$'),
            'tokenToken' : re.compile(r'^\s*(?:token\s+)?(?P<Name>\S+)\s+(?P<Pattern>((\'\S+\')|(\"\S+\")))\s*(?:#.*)*$')
        }
        self.rules = []

    def parse(self, lines):
        self.lines = lines
        if not self.lines:
            return LexicalSpec(self.rules)
        for line in self.lines:
            if self._isBlankOrComment(line):
                continue
            else:
                self._processLine(line)
        return LexicalSpec(self.rules)

    def _processLine(self, line):
            lineIsSkipToken, lineIsRegularToken = self._matchToken(line.string)
            if lineIsSkipToken or lineIsRegularToken:
                self.rules.append(self._generateTokenRule(line, lineIsSkipToken, lineIsRegularToken))
            else:
                self.rules.append(line)

    def _generateTokenRule(self, line: Line, lineIsSkipToken: Match[str], lineIsRegularToken: Match[str]) -> LexicalRule:
        if lineIsSkipToken:
            return self._generateSkipToken(line, lineIsSkipToken['Name'], lineIsSkipToken['Pattern'])
        else: # must be a lineIsRegularToken
            return self._generateRegularToken(line, lineIsRegularToken['Name'], lineIsRegularToken['Pattern'])

    def _isBlankOrComment(self, line: Line) -> bool:
        return not line.string.strip() or line.string.strip().startswith("#")

    def _matchToken(self, lineStr: str) -> tuple[Match[str] | None, Match[str] | None]:
        isSkipToken = re.match(self.patterns['skipToken'], lineStr)
        isRegularToken = re.match(self.patterns['tokenToken'], lineStr)
        return isSkipToken, isRegularToken

    def _generateSkipToken(self, line: Line, name: str, pattern: str) -> LexicalRule:
        pattern = self._stripQuotes(pattern)
        newSkipRule = LexicalRule(line=line, isSkip=True, name=name, pattern=pattern)
        return newSkipRule

    def _generateRegularToken(self, line: Line, name: str, pattern: str) -> LexicalRule:
        pattern = self._stripQuotes(pattern)
        newTokenRule = LexicalRule(line=line, isSkip=False, name=name, pattern=pattern)
        return newTokenRule

    def _stripQuotes(self, pattern: str) -> str:
        pattern = pattern.strip('\'')
        pattern = pattern.strip('\"')
        return pattern
