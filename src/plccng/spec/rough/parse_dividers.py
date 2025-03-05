import re

from ..lines.Line import Line
from .Divider import Divider


def parse_dividers(lines):
    return DividerParser(lines).parse()


class DividerParser:
    def __init__(self, lines):
        self.lines = lines
        self.defaultToolPath = "Java"
        self.defaultLanguage = "Java"
        self.patterns = self._compilePatternDictionary()

    def parse(self):
        if not self.lines:
            return
        for line in self.lines:
            if self._isLine(line) and self._isDivider(line.string):
                yield self._parseDivider(line)
            else:
                yield line

    def _parseDivider(self,line):
        matchToolLanguage = self._matchToolLanguage(line.string)
        matchToolOnly = self._matchToolOnly(line.string)
        tool = self._getTool(matchToolLanguage, matchToolOnly)
        language = self._getLanguage(matchToolLanguage, matchToolOnly)
        return self._createDivider(tool, language, line)

    def _getTool(self, matchToolLanguage, matchToolOnly):
        if matchToolLanguage:
            return matchToolLanguage['tool']
        elif matchToolOnly:
            return matchToolOnly['tool']
        else:
            return self.defaultToolPath

    def _getLanguage(self, matchToolLanguage, matchToolOnly):
        if matchToolLanguage:
            return matchToolLanguage['language']
        elif matchToolOnly:
            return matchToolOnly['tool']
        else:
            return self.defaultLanguage

    def _isLine(self, line):
        return isinstance(line, Line)

    def _isDivider(self, string):
        return bool(self.patterns['divider'].match(string))

    def _matchToolLanguage(self, string):
        return self.patterns['toolLanguage'].match(string)

    def _matchToolOnly(self, string):
        return self.patterns['toolOnly'].match(string)

    def _createDivider(self, toolName, languageName, line):
        return Divider(tool=toolName, language=languageName, line=line)

    def _compilePatternDictionary(self):
        return {
            'divider': re.compile(r'^%(?:\s.*)?$'),
            'toolLanguage': re.compile(r'^%\s*(?P<tool>\S+)\s(?P<language>\S+).*$'),
            'toolOnly': re.compile(r'^%\s*(?P<tool>\S+)\s*$')
        }
