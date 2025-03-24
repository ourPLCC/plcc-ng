import re

from .check_for_duplicate_names import check_for_duplicate_names
from .LexicalRule import LexicalRule
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
        type_ = m[1] if m is not None else 'token'
        index += len(m[0])

        m = re.compile(r'\s*([A-Z_][A-Z0-9_]*)').match(string, index)
        if m is None:
            self.errors.append(NameExpected(line=line, index=index))
            return
        name = m[1]
        index += len(m[0])

        m = re.compile(r'\s*(\S)').match(string, index)
        if not m:
            self.errors.append(PatternExpected(line=line, index=index))
            return
        delimiter = m[1]
        delimiter_escaped = re.escape(delimiter)
        index += len(m[0])

        m = re.compile(f'(?:(?!{delimiter_escaped}).)*').match(string, index)
        regex = m[0]
        index += len(m[0])

        try:
            re.compile(regex)
        except re.PatternError as e:
            self.errors.append(PatternCompilationError(line=line, index=index-len(m[0]), error=e))
            return

        m = re.compile(f'{delimiter_escaped}').match(string, index)
        if not m:
            self.errors.append(PatternDelimiterExpected(line=line, index=index, delimiter=delimiter))
            return
        index += len(m[0])

        m = re.compile(r'\s*(?:#.*)?$').match(string, index)
        if not m:
            self.errors.append(UnexpectedContent(line=line, index=index))

        self.ruleList.append(LexicalRule(line=line, isSkip=(type_=='skip'), name=name, pattern=regex))
