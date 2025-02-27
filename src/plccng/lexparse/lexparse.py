import re

from plccng.lineparse import Line
import plccng.roughparse as roughparse

from .LexicalSpec import LexicalSpec
from .LexicalRule import LexicalRule


def fromstring(string, file=None, startLineNumber=1):
    rough = roughparse.fromstring(string, file=file, startLineNumber=startLineNumber)
    return fromlines(rough)


def fromlines(lines):
    return LexicalParser(lines).parseLexicalSpec()


class LexicalParser():
    def __init__(self, lines):
        self.lines = lines
        self.patterns = {
            'skipToken' : re.compile(r'''^\s*skip\s+(?P<Name>\S+)\s+(?P<Pattern>((?:'(?:\\.|[^'\\])*')|(?:"(?:\\.|[^"\\])*")))\s*(?:#.*)*$'''),
            'tokenToken' : re.compile(r'''^\s*(?:token\s+)?(?P<Name>\S+)\s+(?P<Pattern>((?:'(?:\\.|[^'\\])*')|(?:"(?:\\.|[^"\\])*")))\s*(?:#.*)*$''')
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

    def _generateTokenRule(self, line: Line, lineIsSkipToken: re.Match[str], lineIsRegularToken: re.Match[str]) -> LexicalRule:
        if lineIsSkipToken:
            return self._generateSkipToken(line, lineIsSkipToken['Name'], lineIsSkipToken['Pattern'])
        else: # must be a lineIsRegularToken
            return self._generateRegularToken(line, lineIsRegularToken['Name'], lineIsRegularToken['Pattern'])

    def _isBlankOrComment(self, line: Line) -> bool:
        return not line.string.strip() or line.string.strip().startswith("#")

    def _matchToken(self, lineStr: str) -> tuple[re.Match[str] | None, re.Match[str] | None]:
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
        return pattern[1:-1]
