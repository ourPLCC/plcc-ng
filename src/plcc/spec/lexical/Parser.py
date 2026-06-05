import re

from .check_for_duplicate_names import check_for_duplicate_names
from .TokenRule import TokenRule
from .SkipRule import SkipRule
from .LexicalSpec import LexicalSpec
from .NameExpected import NameExpected
from .PatternCompilationError import PatternCompilationError
from .PatternDelimiterExpected import PatternDelimiterExpected
from .PatternExpected import PatternExpected
from .UnexpectedContent import UnexpectedContent


class Parser():
    def __init__(self):
        self.lines = None
        self.errors = []
        self.ruleList = []

    def parseLexicalSpec(self, lines):
        self.lines = lines
        for part in self.lines:
            if self._isBlankOrComment(part):
                continue
            else:
                self._processLine(part)
        duplications = check_for_duplicate_names(self.ruleList)
        self.errors.extend(duplications)
        return LexicalSpec(self.ruleList), self.errors

    def _isBlankOrComment(self, line):
        return not line.string.strip() or line.string.strip().startswith("#")

    def _processLine(self, line):
        string = line.string
        index = 0

        m = re.compile(r'^\s*(token|skip)?').match(string, index)
        type_ = m[1] if m[1] is not None else 'token'
        index += len(m[0])

        m = re.compile(r'\s*([A-Z_][A-Z0-9_]*)').match(string, index)
        if m is None:
            wsl = self._getLengthOfLeadingWhitespace(string, index)
            self.errors.append(NameExpected(line=line, index=index+wsl))
            return
        name = m[1]
        index += len(m[0])

        regex, index = self._parsePattern(line, string, index)
        if regex is None:
            return

        close_pattern, index = self._parseOptionalPattern(line, string, index)
        if close_pattern is None and index is None:
            return  # error already recorded

        m = re.compile(r'\s*(?:#.*)?$').match(string, index)
        if not m:
            wsl = self._getLengthOfLeadingWhitespace(string, index)
            self.errors.append(UnexpectedContent(line=line, index=index+wsl))
            return

        RuleClass = SkipRule if type_ == 'skip' else TokenRule
        self.ruleList.append(RuleClass(line=line, name=name, pattern=regex, close_pattern=close_pattern))

    def _parsePattern(self, line, string, index):
        """Parse a delimited pattern. Returns (regex, new_index) or (None, None) on error."""
        m = re.compile(r'\s*(\S)').match(string, index)
        if not m:
            wsl = self._getLengthOfLeadingWhitespace(string, index)
            self.errors.append(PatternExpected(line=line, index=index+wsl))
            return None, None
        delimiter = m[1]
        delimiter_escaped = re.escape(delimiter)
        index += len(m[0])

        m = re.compile(f'(?:(?!{delimiter_escaped}).)*').match(string, index)
        regex = m[0]
        index += len(m[0])

        try:
            re.compile(regex)
        except re.error as e:
            self.errors.append(PatternCompilationError(line=line, index=index-len(m[0])+e.pos, error=e))
            return None, None

        m = re.compile(f'{delimiter_escaped}').match(string, index)
        if not m:
            self.errors.append(PatternDelimiterExpected(line=line, index=index, delimiter=delimiter))
            return None, None
        index += len(m[0])
        return regex, index

    def _parseOptionalPattern(self, line, string, index):
        """Parse a second delimited pattern if present. Returns (regex, new_index) or (None, index) if absent, or (None, None) on error."""
        m = re.compile(r'\s*(?:#.*)?$').match(string, index)
        if m:
            return None, index  # no second pattern — that's fine
        return self._parsePattern(line, string, index)

    def _getLengthOfLeadingWhitespace(self, string, index):
        ws = re.compile(r'\s*').match(string, index)
        return len(ws[0])
