import re

from ...lines import Line
from .Divider import Divider
from .TooManyDividerTokensError import TooManyDividerTokensError


def parse_dividers(lines):
    return DividerParser().parse(lines)


class DividerParser:
    def __init__(self):
        self.lines = None
        self.defaultToolPath = "Java"
        self.defaultLanguage = "Java"
        self.patterns = self._compilePatternDictionary()

    def parse(self, lines):
        self.lines = lines
        if not self.lines:
            return
        for line in self.lines:
            if self._isLine(line) and self._isDivider(line.string):
                yield self._parseDivider(line)
            else:
                yield line

    def _parseDivider(self, line):
        matchToolLanguage = self._matchToolLanguage(line.string)
        matchToolOnly = self._matchToolOnly(line.string)
        tool = self._getTool(matchToolLanguage, matchToolOnly)
        language = self._getLanguage(matchToolLanguage, matchToolOnly)
        if matchToolLanguage and matchToolLanguage['extra']:
            col = matchToolLanguage.start('extra') + 1
            raise TooManyDividerTokensError(
                line=line,
                column=col,
                message=f"unexpected token '{matchToolLanguage['extra']}' on divider line",
            )
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
            'toolLanguage': re.compile(r'^%\s*(?P<tool>\S+)\s+(?P<language>\S+)(?:\s+(?P<extra>\S+))?.*$'),
            'toolOnly': re.compile(r'^%\s*(?P<tool>\S+)\s*$')
        }
