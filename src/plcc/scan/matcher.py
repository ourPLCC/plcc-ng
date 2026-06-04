from .Token import Token
from .LexError import LexError
from .Skip import Skip
import re


class Matcher:
    def __init__(self, rules, record_attempts=False):
        self._rules = rules
        self._patterns = None
        self._record_attempts = record_attempts

    def match(self, line, index):
        matches = self._getMatches(line, index)
        if not matches:
            return LexError(line=line, column=index+1)

        result = self._getLongestMatch(matches)

        if self._record_attempts:
            result.attempts = [
                {
                    'name': m.name,
                    'regex': m.pattern,
                    'lexeme': m.lexeme,
                    'char_count': len(m.lexeme),
                    'is_skip': isinstance(m, Skip),
                    'winner': m is result,
                }
                for m in matches
            ]

        return result

    def _getMatches(self, line, index):
        patterns = self._getPatterns()
        matches = []
        for rule, pattern in zip(self._rules, patterns):
            m = pattern.match(line.string, index)
            if not m:
                continue
            if m.end() == index:
                continue
            sot = self._makeSkipOrToken(m, rule, line, index)
            matches.append(sot)
        return matches

    def _getPatterns(self):
        if not self._patterns:
            self._compilePatterns()
        return self._patterns

    def _compilePatterns(self):
        self._patterns = [re.compile(rule.pattern) for rule in self._rules]

    def _makeSkipOrToken(self, match, rule, line, index):
        if rule.isSkip:
            return self._makeSkip(match, rule, line, index)
        return self._makeToken(match, rule, line, index)

    def _makeSkip(self, match, rule, line, index):
        return Skip(
            lexeme=match.group(), name=rule.name,
            line=line, column=1+index, pattern=rule.pattern,
        )

    def _makeToken(self, match, rule, line, index):
        return Token(
            lexeme=match.group(), name=rule.name,
            line=line, column=1+index, pattern=rule.pattern,
        )

    def _getLongestMatch(self, matches):
        # max() returns the first maximum on ties, so declaration order breaks ties.
        return max(matches, key=lambda m: len(m.lexeme))
