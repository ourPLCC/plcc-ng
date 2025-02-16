from ..structs import LexError, Skip, Token
import re

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(self, line, index):
        patterns = self.compile_regex()
        for pattern in patterns:
            test_match = re.search(pattern, line.text)
            if(test_match):
                return Token(lexeme = test_match.group())
        return LexError(line=line, column=1)

    def compile_regex(self):
        patterns = []
        for object in self.spec:
            pattern = re.compile(object["regex"])
            patterns.append(pattern)
        return patterns

