import re
from re import Match

from plccng.lineparse import Line
from plccng.spec.structs import LexicalRule, LexicalSpec
from plccng.roughparse import fromstring


def from_string(string, file=None, startLineNumber=1):
    rough = fromstring(string, file=file, startLineNumber=startLineNumber)
    return from_lines(rough)


def from_lines(lines):
    return LexicalParser(lines).parseLexicalSpec()


class LexicalParser():
    def __init__(self, lines):
        self.lines = lines
        self.patterns = {
            'skipToken' : re.compile(r'^\s*skip\s+(?P<Name>\S+)\s+(?P<Pattern>((\'\S+\')|(\"\S+\")))\s*(?:#.*)*$'),
            'tokenToken' : re.compile(r'^\s*(?:token\s+)?(?P<Name>\S+)\s+(?P<Pattern>((\'\S+\')|(\"\S+\")))\s*(?:#.*)*$')
        }
        self.spec = LexicalSpec([])

    def parseLexicalSpec(self):
        for part in self.lines:
            if self._isBlankOrComment(part):
                continue
            else:
                self._processLine(part)
        return self.spec

    def _processLine(self, line):
            lineIsSkipToken, lineIsRegularToken = self._matchToken(line.string)
            if lineIsSkipToken or lineIsRegularToken:
                self.spec.ruleList.append(self._generateTokenRule(line, lineIsSkipToken, lineIsRegularToken))
            else:
                self.spec.ruleList.append(line)

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
