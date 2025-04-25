from .Token import Token
from .LexError import LexError
from .Skip import Skip
import re

class Matcher:
    def __init__(self, rules):
        self._rules = rules
        self._patterns = None

    def match(self, line, index):
        matches = self._getMatches(line, index)
        if not matches:
            return LexError(line=line, column=index+1)
        if isinstance(matches[0], Skip):
            return matches[0]
        return self._getLongestMatch(matches)

    def _getMatches(self, line, index):
        patterns = self._getPatterns()
        matches = []
        for rule, pattern in zip(self._rules, patterns):
            m = pattern.match(line.string, index)
            if not m:
                continue
            sot = self._makeSkipOrToken(m, rule, line, index)
            matches.append(sot)
        return matches

    def _getPatterns(self):
        if not self._patterns:
            self._compilePatterns()
        return self._patterns

    def _compilePatterns(self):
        compiled_patterns = []
        for rule in self._rules:
            pattern = re.compile(rule.pattern)
            compiled_patterns.append(pattern)
        self._patterns = compiled_patterns

    def _makeSkipOrToken(self, match, rule, line, index):
        if(rule.isSkip):
            return self._makeSkip(match, rule, line, index)
        else:
            return self._makeToken(match, rule, line, index)

    def _makeSkip(self, match, rule, line, index):
        return Skip(lexeme=match.group(), name=rule.name, line=line, column=1+index)

    def _makeToken(self, match, rule, line, index):
        return Token(lexeme=match.group(), name=rule.name, line=line, column=1+index)

    def _getLongestMatch(self, matches):
            return max(matches, key=lambda m: len(m.lexeme))
